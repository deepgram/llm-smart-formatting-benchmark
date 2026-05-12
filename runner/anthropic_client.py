"""Async direct Anthropic API client. Mirrors OpenRouterClient.complete()."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import anthropic
from anthropic import AsyncAnthropic

from runner.models import ModelEntry
from runner.openrouter import CompletionResult
from runner.prompts import ChatMessage


# Per-million-token pricing (USD). Verify before any real run.
# Tuple = (input, output, cache_write, cache_read).
ANTHROPIC_PRICING: dict[str, tuple[float, float, float, float]] = {
    "claude-opus-4-7": (15.00, 75.00, 18.75, 1.50),    # TODO: verify
    "claude-sonnet-4-6": (3.00, 15.00, 3.75, 0.30),    # TODO: verify
    "claude-haiku-4-5": (1.00, 5.00, 1.25, 0.10),      # TODO: verify
}


def _compute_cost(model: str, usage: dict[str, Any]) -> float | None:
    rates = ANTHROPIC_PRICING.get(model)
    if not rates:
        return None
    in_rate, out_rate, cw_rate, cr_rate = rates
    in_tok = usage.get("input_tokens", 0) or 0
    out_tok = usage.get("output_tokens", 0) or 0
    cw_tok = usage.get("cache_creation_input_tokens", 0) or 0
    cr_tok = usage.get("cache_read_input_tokens", 0) or 0
    return (
        in_tok * in_rate / 1e6
        + out_tok * out_rate / 1e6
        + cw_tok * cw_rate / 1e6
        + cr_tok * cr_rate / 1e6
    )


class AnthropicClient:
    """Direct Anthropic API client. Same .complete() signature as OpenRouterClient."""

    def __init__(
        self, api_key: str, *, max_retries: int = 3, timeout: float = 120.0
    ) -> None:
        self.max_retries = max_retries
        # SDK has its own retry; we disable so our retry loop owns backoff.
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout, max_retries=0)

    async def aclose(self) -> None:
        await self._client.close()

    @staticmethod
    def from_env() -> "AnthropicClient":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        return AnthropicClient(key)

    async def complete(
        self, entry: ModelEntry, messages: list[ChatMessage]
    ) -> CompletionResult:
        system_msgs = [m for m in messages if m["role"] == "system"]
        user_msgs = [m for m in messages if m["role"] != "system"]

        # System as block list with prompt caching on the last block — base
        # prompt is identical across all rows so cache hit-rate should be high.
        system_blocks: list[dict[str, Any]] = []
        for sm in system_msgs:
            system_blocks.append({"type": "text", "text": sm["content"]})
        if system_blocks:
            system_blocks[-1]["cache_control"] = {"type": "ephemeral"}

        anthropic_msgs = [
            {"role": m["role"], "content": m["content"]} for m in user_msgs
        ]
        anth_model = entry.get("native_model") or entry["model_id"]
        params: dict[str, Any] = {
            "model": anth_model,
            "messages": anthropic_msgs,
            "max_tokens": entry.get("max_tokens", 1024),
        }
        # Opus 4.7 (and likely future Claude models) reject the temperature
        # param entirely — Anthropic deprecated it. Older models still accept it.
        if not anth_model.startswith("claude-opus-4-7"):
            params["temperature"] = entry.get("temperature", 0.0)
        if system_blocks:
            params["system"] = system_blocks
        extra = entry.get("extra_body") or {}
        if "thinking" in extra:
            params["thinking"] = extra["thinking"]

        for attempt in range(self.max_retries + 1):
            try:
                return await self._stream_once(params, anth_model)
            except (
                anthropic.RateLimitError,
                anthropic.InternalServerError,
                anthropic.APIConnectionError,
                anthropic.APITimeoutError,
            ) as e:
                if attempt >= self.max_retries:
                    return CompletionResult(error=f"{type(e).__name__}: {e}")
                await asyncio.sleep(2**attempt)
            except Exception as e:
                return CompletionResult(error=f"{type(e).__name__}: {e}")
        return CompletionResult(error="retries exhausted")

    async def _stream_once(
        self, params: dict[str, Any], anth_model: str
    ) -> CompletionResult:
        started = time.perf_counter()
        first_token_at: float | None = None
        content_parts: list[str] = []
        finish_reason: str | None = None
        usage: dict[str, Any] = {}

        async with self._client.messages.stream(**params) as stream:
            async for event in stream:
                et = getattr(event, "type", None)
                if et == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    if delta and getattr(delta, "type", None) == "text_delta":
                        text = getattr(delta, "text", "") or ""
                        if text:
                            if first_token_at is None:
                                first_token_at = time.perf_counter()
                            content_parts.append(text)
                elif et == "message_delta":
                    d = getattr(event, "delta", None)
                    if d and getattr(d, "stop_reason", None):
                        finish_reason = d.stop_reason
                    u = getattr(event, "usage", None)
                    if u is not None:
                        try:
                            usage.update(u.model_dump(exclude_none=True))
                        except Exception:
                            pass
            final = await stream.get_final_message()
            if final and final.usage:
                try:
                    usage.update(final.usage.model_dump(exclude_none=True))
                except Exception:
                    pass
            if final and final.stop_reason:
                finish_reason = final.stop_reason

        finished = time.perf_counter()
        ttft_ms = (
            (first_token_at - started) * 1000.0 if first_token_at is not None else None
        )
        return CompletionResult(
            actual_output="".join(content_parts),
            latency_total_ms=(finished - started) * 1000.0,
            latency_ttft_ms=ttft_ms,
            tokens_in=usage.get("input_tokens"),
            tokens_out=usage.get("output_tokens"),
            cost_usd=_compute_cost(anth_model, usage),
            finish_reason=finish_reason,
            raw_provider="anthropic",
        )
