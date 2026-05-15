"""LLM-judge passes against Anthropic or OpenAI.

Two independent calls per row:

- ``judge_accuracy`` — sees reference + actual + optional formatting prompt.
- ``judge_hallucination`` — sees only input + actual (no reference).

The same ``JudgeClient`` can target either backend. The backend is picked
from the model slug:

- ``claude-...`` → Anthropic (Messages + tool_use).
- ``gpt-...`` / ``o3-...`` / ``o4-...`` → OpenAI (chat.completions + tool
  calling).

Both backends are forced into structured output via a synthetic
``submit_judgment`` / ``submit_hallucination_check`` tool so the response
is parsed deterministically into the same Pydantic models. Malformed
responses fail loudly.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
from dataclasses import dataclass, field
from typing import Any, Literal

import anthropic
import openai
from anthropic import APIStatusError, RateLimitError
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from evaluator.prompts import JUDGE_ACCURACY_SYSTEM, JUDGE_HALLUCINATION_SYSTEM


JUDGE_MODEL_DEFAULT = "claude-opus-4-7"
JUDGE_MODEL_SECONDARY_DEFAULT = "gpt-5.5"
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


# ----------------- Tool schemas (shared input_schema is reused for both
# Anthropic tool_use and OpenAI function-calling) -----------------


_ACCURACY_SCHEMA: dict[str, Any] = {
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
}

_HALLUCINATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "hallucination": {
            "type": "string",
            "enum": ["none", "minor_addition", "dropped_content", "fabricated"],
        },
        "hallucination_reason": {"type": "string"},
    },
    "required": ["hallucination", "hallucination_reason"],
}

_ACCURACY_TOOL_DESCRIPTION = (
    "Submit the structured accuracy + promptability + catastrophic "
    "judgment for one candidate output."
)
_HALLUCINATION_TOOL_DESCRIPTION = (
    "Submit the structured hallucination check for one candidate output."
)

_ANTHROPIC_ACCURACY_TOOL = {
    "name": "submit_judgment",
    "description": _ACCURACY_TOOL_DESCRIPTION,
    "input_schema": _ACCURACY_SCHEMA,
}
_ANTHROPIC_HALLUCINATION_TOOL = {
    "name": "submit_hallucination_check",
    "description": _HALLUCINATION_TOOL_DESCRIPTION,
    "input_schema": _HALLUCINATION_SCHEMA,
}

_OPENAI_ACCURACY_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_judgment",
        "description": _ACCURACY_TOOL_DESCRIPTION,
        "parameters": _ACCURACY_SCHEMA,
    },
}
_OPENAI_HALLUCINATION_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_hallucination_check",
        "description": _HALLUCINATION_TOOL_DESCRIPTION,
        "parameters": _HALLUCINATION_SCHEMA,
    },
}


# ----------------- Cost tracking -----------------


# Per-MM-token prices (USD). Sources: Anthropic public pricing (Opus 4.7),
# OpenAI public pricing (gpt-5.5). Cache-read = input tokens that hit the
# provider's prompt cache; on OpenAI this is the auto-discounted half-price
# tier (so PRICE_CACHE_WRITE == PRICE_INPUT and PRICE_CACHE_READ == 0.5 *
# PRICE_INPUT). Used only to render USD totals — the SDK usage object is
# the source of truth for token counts.
_PRICING: dict[str, dict[str, float]] = {
    # Anthropic
    "claude-opus-4-7": {
        "input": 15.0,
        "output": 75.0,
        "cache_write": 18.75,
        "cache_read": 1.50,
    },
    # OpenAI (cached input on OpenAI is auto-discounted; treat cache_read as
    # 0.5x input, cache_write as full input).
    "gpt-5.5": {
        "input": 1.25,
        "output": 10.00,
        "cache_write": 1.25,
        "cache_read": 0.625,
    },
    "gpt-5.5-mini": {
        "input": 0.25,
        "output": 2.00,
        "cache_write": 0.25,
        "cache_read": 0.125,
    },
    "gpt-5.4-mini": {
        "input": 0.15,
        "output": 0.60,
        "cache_write": 0.15,
        "cache_read": 0.075,
    },
}

_PRICING_FALLBACK = {"input": 0.0, "output": 0.0, "cache_write": 0.0, "cache_read": 0.0}


def _pricing_for(model: str) -> dict[str, float]:
    """Look up per-MM-token pricing for a judge model.

    Tolerates the Anthropic-style ``claude-opus-4-7`` and OpenAI-style
    ``gpt-5.5`` slugs. Unknown models get zeros (USD totals will read $0).
    """
    if model in _PRICING:
        return _PRICING[model]
    # Try common slug normalizations
    canon = model.replace("-", ".") if model.startswith("gpt") else model
    if canon in _PRICING:
        return _PRICING[canon]
    return _PRICING_FALLBACK


@dataclass
class JudgeCostTracker:
    """Aggregate token counts + USD cost across all judge calls.

    Pricing is per-instance so the tracker can serve any backend. Token
    counts are fed in from whichever SDK usage object we got — Anthropic's
    fields are mapped directly; OpenAI's ``prompt_tokens`` /
    ``completion_tokens`` / ``prompt_tokens_details.cached_tokens`` are
    mapped onto the same input / output / cache_read fields.
    """

    model: str = JUDGE_MODEL_DEFAULT
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    calls: int = 0
    errors: int = 0

    def __post_init__(self) -> None:
        p = _pricing_for(self.model)
        self.price_input: float = p["input"]
        self.price_output: float = p["output"]
        self.price_cache_write: float = p["cache_write"]
        self.price_cache_read: float = p["cache_read"]

    def add_anthropic(self, usage: Any) -> None:
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

    def add_openai(self, usage: dict[str, Any] | None) -> None:
        if not usage:
            return
        # OpenAI's cached_tokens are a *subset* of prompt_tokens. We split
        # them out so cache_read is priced at the discounted rate and the
        # remaining prompt_tokens at full input rate.
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        completion = int(usage.get("completion_tokens", 0) or 0)
        cached = 0
        details = usage.get("prompt_tokens_details") or {}
        if isinstance(details, dict):
            cached = int(details.get("cached_tokens", 0) or 0)
        cached = max(0, min(cached, prompt))
        self.input_tokens += prompt - cached
        self.cache_read_input_tokens += cached
        self.output_tokens += completion

    @property
    def total_usd(self) -> float:
        return (
            self.input_tokens / 1e6 * self.price_input
            + self.output_tokens / 1e6 * self.price_output
            + self.cache_creation_input_tokens / 1e6 * self.price_cache_write
            + self.cache_read_input_tokens / 1e6 * self.price_cache_read
        )

    def summary(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "calls": self.calls,
            "errors": self.errors,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "total_usd": round(self.total_usd, 6),
        }


# ----------------- Judge client -----------------


def _detect_backend(model: str) -> str:
    """Return ``"anthropic"`` or ``"openai"`` for a judge model slug."""
    s = model.lower()
    if s.startswith("claude"):
        return "anthropic"
    if s.startswith("gpt") or s.startswith("o3") or s.startswith("o4"):
        return "openai"
    # Default to anthropic — historical behavior.
    return "anthropic"


@dataclass
class JudgeClient:
    """Async judge wrapper. Routes to Anthropic or OpenAI by model slug.

    ``concurrency`` controls the in-flight semaphore. Retries on rate-limit
    / 5xx with exponential backoff (1s, 2s, 4s) up to ``max_retries``.
    """

    model: str = JUDGE_MODEL_DEFAULT
    concurrency: int = 8
    max_retries: int = 3
    cost: JudgeCostTracker = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.backend = _detect_backend(self.model)
        if self.cost is None:
            self.cost = JudgeCostTracker(model=self.model)
        if self.backend == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set. Export it before running the evaluator."
                )
            self._anthropic: anthropic.AsyncAnthropic = anthropic.AsyncAnthropic(api_key=api_key)
            self._openai: AsyncOpenAI | None = None
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set. Export it before running the evaluator with an OpenAI judge."
                )
            self._openai = AsyncOpenAI(api_key=api_key, max_retries=0, timeout=120.0)
            self._anthropic = None  # type: ignore[assignment]
        self._sem: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

    async def aclose(self) -> None:
        if self._anthropic is not None:
            await self._anthropic.close()
        if self._openai is not None:
            await self._openai.close()

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
        tool_name: str,
    ) -> dict[str, Any]:
        async with self._sem:
            self.cost.calls += 1
            last_err: Exception | None = None
            for attempt in range(self.max_retries + 1):
                try:
                    if self.backend == "anthropic":
                        return await self._call_anthropic(system, user, tool_name)
                    return await self._call_openai(system, user, tool_name)
                except RateLimitError as e:
                    last_err = e
                except APIStatusError as e:
                    status = getattr(e, "status_code", None)
                    if status in (408, 429, 529) or (status and 500 <= status < 600):
                        last_err = e
                    else:
                        self.cost.errors += 1
                        raise
                except (
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                    openai.InternalServerError,
                ) as e:
                    last_err = e
                except openai.APIStatusError as e:
                    status = getattr(e, "status_code", None)
                    if status in (408, 429, 529) or (status and 500 <= status < 600):
                        last_err = e
                    else:
                        self.cost.errors += 1
                        raise
                except Exception as e:  # network / parse / other transient
                    last_err = e
                if attempt < self.max_retries:
                    delay = (2**attempt) + random.uniform(0, 0.25)
                    await asyncio.sleep(delay)
            self.cost.errors += 1
            assert last_err is not None
            raise last_err

    async def _call_anthropic(
        self, system: str, user: str, tool_name: str
    ) -> dict[str, Any]:
        tool = (
            _ANTHROPIC_ACCURACY_TOOL
            if tool_name == "submit_judgment"
            else _ANTHROPIC_HALLUCINATION_TOOL
        )
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
        if not _is_anthropic_temp_deprecated(self.model):
            create_kwargs["temperature"] = JUDGE_TEMPERATURE
        resp = await self._anthropic.messages.create(**create_kwargs)
        self.cost.add_anthropic(resp.usage)
        return _extract_anthropic_tool_input(resp, tool_name)

    async def _call_openai(
        self, system: str, user: str, tool_name: str
    ) -> dict[str, Any]:
        tool = (
            _OPENAI_ACCURACY_TOOL
            if tool_name == "submit_judgment"
            else _OPENAI_HALLUCINATION_TOOL
        )
        params: dict[str, Any] = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": tool_name}},
            max_completion_tokens=JUDGE_MAX_TOKENS,
        )
        # gpt-5.5+ only accepts temperature=1; gpt-5.4-mini/older accept arbitrary.
        if not _is_openai_temp_deprecated(self.model):
            params["temperature"] = JUDGE_TEMPERATURE
        resp = await self._openai.chat.completions.create(**params)
        # Usage may be None on stream-only paths, but chat.completions
        # returns it on the final response object.
        usage_obj = getattr(resp, "usage", None)
        if usage_obj is not None:
            try:
                self.cost.add_openai(usage_obj.model_dump(exclude_none=True))
            except Exception:
                pass
        return _extract_openai_tool_input(resp, tool_name)


# ----------------- helpers -----------------


def _is_anthropic_temp_deprecated(model: str) -> bool:
    """True if this Claude model rejects the ``temperature`` param."""
    s = model.lower()
    deprecated_markers = ("4-5", "4-6", "4-7", "4.5", "4.6", "4.7", "4.8", "5-0", "5.0")
    return any(m in s for m in deprecated_markers)


def _is_openai_temp_deprecated(model: str) -> bool:
    """gpt-5.5+ and o-series only accept temperature=1 (i.e. unset)."""
    s = model.lower()
    if s.startswith("o3") or s.startswith("o4"):
        return True
    if s.startswith("gpt-5.5") or s.startswith("gpt-5-5"):
        return True
    return False


def _extract_anthropic_tool_input(resp: Any, tool_name: str) -> dict[str, Any]:
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
            return dict(block.input)
    raise RuntimeError(
        f"Anthropic judge response had no tool_use block for {tool_name!r}. "
        f"Stop reason: {getattr(resp, 'stop_reason', None)!r}. "
        f"Blocks: {[getattr(b, 'type', None) for b in resp.content]}"
    )


def _extract_openai_tool_input(resp: Any, tool_name: str) -> dict[str, Any]:
    """Pull the JSON-decoded ``arguments`` of the forced tool call."""
    choices = getattr(resp, "choices", None) or []
    if not choices:
        raise RuntimeError("OpenAI judge response had no choices.")
    msg = getattr(choices[0], "message", None)
    if msg is None:
        raise RuntimeError("OpenAI judge response had no message on choice[0].")
    tool_calls = getattr(msg, "tool_calls", None) or []
    for call in tool_calls:
        fn = getattr(call, "function", None)
        if fn is not None and getattr(fn, "name", None) == tool_name:
            args = getattr(fn, "arguments", None) or "{}"
            try:
                return json.loads(args)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"OpenAI judge returned non-JSON tool arguments: {args!r} ({e})"
                ) from e
    finish = getattr(choices[0], "finish_reason", None)
    raise RuntimeError(
        f"OpenAI judge response had no tool_call for {tool_name!r}. "
        f"finish_reason={finish!r}."
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
    "JUDGE_MODEL_SECONDARY_DEFAULT",
]
