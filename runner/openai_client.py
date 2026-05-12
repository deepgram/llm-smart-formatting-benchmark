"""Async direct OpenAI API client. Mirrors OpenRouterClient.complete()."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import openai
from openai import AsyncOpenAI

from runner.models import ModelEntry
from runner.openrouter import CompletionResult
from runner.prompts import ChatMessage


# Per-million-token pricing (USD). Verify before any real run.
# Tuple = (input, output). OpenAI auto-discounts cached input — no separate field.
OPENAI_PRICING: dict[str, tuple[float, float]] = {
    "gpt-5.5": (1.25, 10.00),       # TODO: verify
    "gpt-5.5-mini": (0.25, 2.00),   # TODO: verify
    "gpt-5.4-mini": (0.15, 0.60),   # TODO: verify
}


def _compute_cost(model: str, usage: dict[str, Any]) -> float | None:
    rates = OPENAI_PRICING.get(model)
    if not rates:
        return None
    in_rate, out_rate = rates
    in_tok = usage.get("prompt_tokens", 0) or 0
    out_tok = usage.get("completion_tokens", 0) or 0
    return in_tok * in_rate / 1e6 + out_tok * out_rate / 1e6


class OpenAIClient:
    """Direct OpenAI API client. Same .complete() signature as OpenRouterClient."""

    def __init__(
        self, api_key: str, *, max_retries: int = 3, timeout: float = 120.0
    ) -> None:
        self.max_retries = max_retries
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=0)

    async def aclose(self) -> None:
        await self._client.close()

    @staticmethod
    def from_env() -> "OpenAIClient":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        return OpenAIClient(key)

    async def complete(
        self, entry: ModelEntry, messages: list[ChatMessage]
    ) -> CompletionResult:
        oa_model = entry.get("native_model") or entry["model_id"]
        params: dict[str, Any] = {
            "model": oa_model,
            "messages": list(messages),
            # GPT-5.x rejects max_tokens; the modern param is max_completion_tokens.
            "max_completion_tokens": entry.get("max_tokens", 1024),
            "top_p": entry.get("top_p", 1.0),
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        # gpt-5.5+ (and o-series reasoning models) only accept temperature=1.
        # Older models (gpt-5.4-mini etc.) still accept arbitrary temperature.
        if not (oa_model.startswith("gpt-5.5") or oa_model.startswith("o3") or oa_model.startswith("o4")):
            params["temperature"] = entry.get("temperature", 0.0)
        # extra_body uses OpenRouter-style {"reasoning": {"effort": "low"}}; map
        # that to the OpenAI-native reasoning_effort param when present.
        extra = entry.get("extra_body") or {}
        if "reasoning" in extra:
            r = extra["reasoning"]
            if isinstance(r, dict) and r.get("effort"):
                params["reasoning_effort"] = r["effort"]

        for attempt in range(self.max_retries + 1):
            try:
                return await self._stream_once(params, oa_model)
            except (
                openai.RateLimitError,
                openai.APIConnectionError,
                openai.APITimeoutError,
                openai.InternalServerError,
            ) as e:
                if attempt >= self.max_retries:
                    return CompletionResult(error=f"{type(e).__name__}: {e}")
                await asyncio.sleep(2**attempt)
            except Exception as e:
                return CompletionResult(error=f"{type(e).__name__}: {e}")
        return CompletionResult(error="retries exhausted")

    async def _stream_once(
        self, params: dict[str, Any], oa_model: str
    ) -> CompletionResult:
        started = time.perf_counter()
        first_token_at: float | None = None
        content_parts: list[str] = []
        finish_reason: str | None = None
        usage: dict[str, Any] = {}

        stream = await self._client.chat.completions.create(**params)
        async for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if choices:
                delta = getattr(choices[0], "delta", None)
                if delta is not None:
                    text = getattr(delta, "content", None) or ""
                    if text:
                        if first_token_at is None:
                            first_token_at = time.perf_counter()
                        content_parts.append(text)
                fr = getattr(choices[0], "finish_reason", None)
                if fr:
                    finish_reason = fr
            cu = getattr(chunk, "usage", None)
            if cu is not None:
                try:
                    usage.update(cu.model_dump(exclude_none=True))
                except Exception:
                    pass

        finished = time.perf_counter()
        ttft_ms = (
            (first_token_at - started) * 1000.0 if first_token_at is not None else None
        )
        return CompletionResult(
            actual_output="".join(content_parts),
            latency_total_ms=(finished - started) * 1000.0,
            latency_ttft_ms=ttft_ms,
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
            cost_usd=_compute_cost(oa_model, usage),
            finish_reason=finish_reason,
            raw_provider="openai",
        )
