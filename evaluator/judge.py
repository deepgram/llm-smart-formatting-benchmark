"""LLM-judge passes against the Anthropic API.

Two independent calls per row:

- ``judge_accuracy`` — sees reference + actual + optional formatting prompt.
- ``judge_hallucination`` — sees only input + actual (no reference).

Both calls force structured output via Tool Use (a synthetic
``submit_judgment`` / ``submit_hallucination_check`` tool) so the response
is parsed deterministically into Pydantic models. Malformed responses fail
loudly.

The system prompts are wrapped with ``cache_control: ephemeral`` so
identical headers across thousands of calls hit Anthropic's prompt cache
and we pay the cache-read rate after the first call.
"""

from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass, field
from typing import Any, Literal

import anthropic
from anthropic import APIStatusError, RateLimitError
from pydantic import BaseModel, ValidationError

from evaluator.prompts import JUDGE_ACCURACY_SYSTEM, JUDGE_HALLUCINATION_SYSTEM


JUDGE_MODEL_DEFAULT = "claude-opus-4-7"
JUDGE_MAX_TOKENS = 512
JUDGE_TEMPERATURE = 0.0


# ----------------- Pydantic models for the tool-use payloads -----------------


class AccuracyJudgment(BaseModel):
    accuracy: Literal["pass", "style_violation", "numeric_drift", "wrong_value", "other"]
    accuracy_reason: str
    promptability: Literal["followed", "partial", "ignored", "n_a"]
    promptability_reason: str
    catastrophic: bool


class HallucinationJudgment(BaseModel):
    hallucination: Literal["none", "minor_addition", "dropped_content", "fabricated"]
    hallucination_reason: str


# ----------------- Tool schemas -----------------


_ACCURACY_TOOL = {
    "name": "submit_judgment",
    "description": (
        "Submit the structured accuracy + promptability + catastrophic "
        "judgment for one candidate output."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "accuracy": {
                "type": "string",
                "enum": [
                    "pass",
                    "style_violation",
                    "numeric_drift",
                    "wrong_value",
                    "other",
                ],
            },
            "accuracy_reason": {"type": "string"},
            "promptability": {
                "type": "string",
                "enum": ["followed", "partial", "ignored", "n_a"],
            },
            "promptability_reason": {"type": "string"},
            "catastrophic": {"type": "boolean"},
        },
        "required": [
            "accuracy",
            "accuracy_reason",
            "promptability",
            "promptability_reason",
            "catastrophic",
        ],
    },
}


_HALLUCINATION_TOOL = {
    "name": "submit_hallucination_check",
    "description": (
        "Submit the structured hallucination check for one candidate output."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "hallucination": {
                "type": "string",
                "enum": ["none", "minor_addition", "dropped_content", "fabricated"],
            },
            "hallucination_reason": {"type": "string"},
        },
        "required": ["hallucination", "hallucination_reason"],
    },
}


# ----------------- Cost tracking -----------------


@dataclass
class JudgeCostTracker:
    """Aggregate token counts + USD cost across all judge calls.

    Pricing for Anthropic Opus 4.7 (per Anthropic public pricing as of
    2026-05): $15 / Mtok input, $75 / Mtok output, with 90% discount on
    cache reads ($1.50 / Mtok) and 25% premium on cache writes
    ($18.75 / Mtok). We use the SDK's reported usage object as the source
    of truth — these constants are only used to convert to USD.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    calls: int = 0
    errors: int = 0

    # USD per 1M tokens
    PRICE_INPUT: float = 15.0
    PRICE_OUTPUT: float = 75.0
    PRICE_CACHE_WRITE: float = 18.75
    PRICE_CACHE_READ: float = 1.50

    def add(self, usage: Any) -> None:
        """Fold an SDK ``Usage`` object into the aggregate."""
        if usage is None:
            return
        self.input_tokens += getattr(usage, "input_tokens", 0) or 0
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.cache_creation_input_tokens += (
            getattr(usage, "cache_creation_input_tokens", 0) or 0
        )
        self.cache_read_input_tokens += (
            getattr(usage, "cache_read_input_tokens", 0) or 0
        )

    @property
    def total_usd(self) -> float:
        return (
            self.input_tokens / 1e6 * self.PRICE_INPUT
            + self.output_tokens / 1e6 * self.PRICE_OUTPUT
            + self.cache_creation_input_tokens / 1e6 * self.PRICE_CACHE_WRITE
            + self.cache_read_input_tokens / 1e6 * self.PRICE_CACHE_READ
        )

    def summary(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "errors": self.errors,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "total_usd": round(self.total_usd, 6),
        }


# ----------------- Judge client -----------------


@dataclass
class JudgeClient:
    """Async wrapper around ``anthropic.AsyncAnthropic`` with retries.

    ``concurrency`` controls the in-flight semaphore. Retries on 429 / 529
    / 5xx with exponential backoff (1s, 2s, 4s) up to ``max_retries``.
    """

    model: str = JUDGE_MODEL_DEFAULT
    concurrency: int = 8
    max_retries: int = 3
    cost: JudgeCostTracker = field(default_factory=JudgeCostTracker)

    def __post_init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it before running the evaluator."
            )
        self._client: anthropic.AsyncAnthropic = anthropic.AsyncAnthropic(api_key=api_key)
        self._sem: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

    async def aclose(self) -> None:
        await self._client.close()

    # ----- public API -----

    async def judge_accuracy(
        self,
        *,
        formatting_prompt: str,
        input_text: str,
        expected_output: str,
        actual_output: str,
        entity_class: str,
        variant: str,
    ) -> AccuracyJudgment:
        user_msg = _build_accuracy_user_message(
            formatting_prompt=formatting_prompt,
            input_text=input_text,
            expected_output=expected_output,
            actual_output=actual_output,
            entity_class=entity_class,
            variant=variant,
        )
        raw = await self._call(
            system=JUDGE_ACCURACY_SYSTEM,
            user=user_msg,
            tool=_ACCURACY_TOOL,
            tool_name="submit_judgment",
        )
        try:
            return AccuracyJudgment.model_validate(raw)
        except ValidationError as e:
            raise RuntimeError(
                f"Judge returned malformed accuracy payload: {raw!r} ({e})"
            ) from e

    async def judge_hallucination(
        self,
        *,
        input_text: str,
        actual_output: str,
    ) -> HallucinationJudgment:
        user_msg = _build_hallucination_user_message(
            input_text=input_text,
            actual_output=actual_output,
        )
        raw = await self._call(
            system=JUDGE_HALLUCINATION_SYSTEM,
            user=user_msg,
            tool=_HALLUCINATION_TOOL,
            tool_name="submit_hallucination_check",
        )
        try:
            return HallucinationJudgment.model_validate(raw)
        except ValidationError as e:
            raise RuntimeError(
                f"Judge returned malformed hallucination payload: {raw!r} ({e})"
            ) from e

    # ----- internals -----

    async def _call(
        self,
        *,
        system: str,
        user: str,
        tool: dict[str, Any],
        tool_name: str,
    ) -> dict[str, Any]:
        """One judge call with retries. Returns the parsed tool-use input dict."""
        async with self._sem:
            self.cost.calls += 1
            last_err: Exception | None = None
            for attempt in range(self.max_retries + 1):
                try:
                    # Newer Claude models (4.5+) reject the ``temperature``
                    # param entirely. Detect and retry without it. We start
                    # by omitting it for any model with "4.5" or higher in
                    # its slug; older slugs still receive ``temperature=0``
                    # for determinism.
                    # Place cache_control on BOTH the system block and the
                    # tool definition. Anthropic considers cached prefix as
                    # system + tools + ... so tagging tools extends the
                    # cached span. Note the prompts here are short (<1024
                    # tokens) so caching may not activate on Opus 4.7 until
                    # the prompts grow; the directives are correct either
                    # way and become effective when over threshold.
                    cached_tool = dict(tool)
                    cached_tool["cache_control"] = {"type": "ephemeral"}
                    create_kwargs: dict[str, Any] = dict(
                        model=self.model,
                        max_tokens=JUDGE_MAX_TOKENS,
                        system=[
                            {
                                "type": "text",
                                "text": system,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ],
                        tools=[cached_tool],
                        tool_choice={"type": "tool", "name": tool_name},
                        messages=[{"role": "user", "content": user}],
                    )
                    if not _is_temp_deprecated(self.model):
                        create_kwargs["temperature"] = JUDGE_TEMPERATURE
                    resp = await self._client.messages.create(**create_kwargs)
                    self.cost.add(resp.usage)
                    return _extract_tool_input(resp, tool_name)
                except RateLimitError as e:
                    last_err = e
                except APIStatusError as e:
                    status = getattr(e, "status_code", None)
                    if status in (408, 429, 529) or (status and 500 <= status < 600):
                        last_err = e
                    else:
                        self.cost.errors += 1
                        raise
                except Exception as e:  # network / parse / other transient
                    last_err = e
                # Backoff before retry.
                if attempt < self.max_retries:
                    delay = (2**attempt) + random.uniform(0, 0.25)
                    await asyncio.sleep(delay)
            self.cost.errors += 1
            assert last_err is not None
            raise last_err


# ----------------- helpers -----------------


def _is_temp_deprecated(model: str) -> bool:
    """True if this Claude model rejects the ``temperature`` param.

    Anthropic deprecated ``temperature`` for the 4.5+ family. We keep the
    rule conservative: any model whose slug contains ``4.5``, ``4.6``,
    ``4.7``, ``haiku-4.5``, ``opus-4.5``, ``sonnet-4.5``, etc.
    """
    s = model.lower()
    deprecated_markers = ("4-5", "4-6", "4-7", "4.5", "4.6", "4.7", "4.8", "5-0", "5.0")
    return any(m in s for m in deprecated_markers)


def _extract_tool_input(resp: Any, tool_name: str) -> dict[str, Any]:
    """Pull the ``input`` dict out of the first matching tool_use block.

    Anthropic's response is a list of content blocks; with ``tool_choice``
    set to a specific tool, the first block is the ``tool_use`` we asked
    for. We still defend against anomalies (e.g. an extra text block).
    """
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
            return dict(block.input)
    raise RuntimeError(
        f"Judge response had no tool_use block for {tool_name!r}. "
        f"Stop reason: {getattr(resp, 'stop_reason', None)!r}. "
        f"Blocks: {[getattr(b, 'type', None) for b in resp.content]}"
    )


def _build_accuracy_user_message(
    *,
    formatting_prompt: str,
    input_text: str,
    expected_output: str,
    actual_output: str,
    entity_class: str,
    variant: str,
) -> str:
    fp = formatting_prompt or "(none — default formatting only)"
    return (
        f"<entity_class>{entity_class}</entity_class>\n"
        f"<variant>{variant}</variant>\n"
        f"<formatting_instruction>{fp}</formatting_instruction>\n"
        f"<input_transcript>{input_text}</input_transcript>\n"
        f"<reference_output>{expected_output}</reference_output>\n"
        f"<candidate_output>{actual_output}</candidate_output>\n\n"
        "Score the candidate via the submit_judgment tool."
    )


def _build_hallucination_user_message(*, input_text: str, actual_output: str) -> str:
    return (
        f"<input_transcript>{input_text}</input_transcript>\n"
        f"<candidate_output>{actual_output}</candidate_output>\n\n"
        "Check for hallucinated, dropped, or fabricated content via the "
        "submit_hallucination_check tool."
    )


__all__ = [
    "AccuracyJudgment",
    "HallucinationJudgment",
    "JudgeClient",
    "JudgeCostTracker",
    "JUDGE_MODEL_DEFAULT",
]
