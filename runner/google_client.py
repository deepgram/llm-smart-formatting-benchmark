"""Async direct Google Gemini API client. Mirrors OpenRouterClient.complete()."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from google import genai
from google.genai import types

from runner.models import ModelEntry
from runner.openrouter import CompletionResult
from runner.prompts import ChatMessage


# Per-million-token pricing (USD). Verify before any real run.
# Tuple = (input, output).
GOOGLE_PRICING: dict[str, tuple[float, float]] = {
    "gemini-3.1-pro": (1.25, 10.00),    # TODO: verify
    "gemini-3.1-flash": (0.075, 0.30),  # TODO: verify
}


def _compute_cost(model: str, usage: dict[str, Any]) -> float | None:
    rates = GOOGLE_PRICING.get(model)
    if not rates:
        return None
    in_rate, out_rate = rates
    in_tok = usage.get("prompt_token_count", 0) or 0
    out_tok = usage.get("candidates_token_count", 0) or 0
    return in_tok * in_rate / 1e6 + out_tok * out_rate / 1e6


class GoogleClient:
    """Direct Google Gemini API client. Same .complete() signature as OpenRouterClient."""

    def __init__(self, api_key: str, *, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self._client = genai.Client(api_key=api_key)

    async def aclose(self) -> None:
        # google-genai async client has no explicit close method.
        return None

    @staticmethod
    def from_env() -> "GoogleClient":
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set.")
        return GoogleClient(key)

    async def complete(
        self, entry: ModelEntry, messages: list[ChatMessage]
    ) -> CompletionResult:
        # Gemini takes system_instruction separately and a single contents string.
        system_text = "\n\n".join(
            m["content"] for m in messages if m["role"] == "system"
        )
        user_text = "\n\n".join(m["content"] for m in messages if m["role"] == "user")
        gem_model = entry.get("native_model") or entry["model_id"]

        config_kwargs: dict[str, Any] = {
            "temperature": entry.get("temperature", 0.0),
            "top_p": entry.get("top_p", 1.0),
            "max_output_tokens": entry.get("max_tokens", 1024),
        }
        if system_text:
            config_kwargs["system_instruction"] = system_text
        # extra_body uses OpenRouter-style {"reasoning": {"effort": ...}}; map to
        # Gemini ThinkingConfig.
        extra = entry.get("extra_body") or {}
        if "reasoning" in extra:
            r = extra["reasoning"]
            if isinstance(r, dict) and r.get("effort"):
                effort_to_budget = {"low": 1024, "medium": 4096, "high": 8192}
                budget = effort_to_budget.get(r["effort"], 1024)
                try:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(
                        thinking_budget=budget
                    )
                except Exception:
                    pass

        cfg = types.GenerateContentConfig(**config_kwargs)

        for attempt in range(self.max_retries + 1):
            try:
                return await self._stream_once(gem_model, user_text, cfg)
            except Exception as e:
                # google-genai does not expose granular exception classes
                # consistently across versions — match on the message.
                msg = str(e).lower()
                transient = any(
                    s in msg
                    for s in (
                        "rate",
                        "429",
                        "503",
                        "504",
                        "timeout",
                        "deadline",
                        "unavailable",
                    )
                )
                if not transient or attempt >= self.max_retries:
                    return CompletionResult(error=f"{type(e).__name__}: {e}")
                await asyncio.sleep(2**attempt)
        return CompletionResult(error="retries exhausted")

    async def _stream_once(
        self, model: str, user_text: str, cfg: Any
    ) -> CompletionResult:
        started = time.perf_counter()
        first_token_at: float | None = None
        content_parts: list[str] = []
        finish_reason: str | None = None
        usage: dict[str, Any] = {}

        stream = await self._client.aio.models.generate_content_stream(
            model=model, contents=user_text, config=cfg
        )
        async for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                content_parts.append(text)
            cands = getattr(chunk, "candidates", None) or []
            if cands:
                fr = getattr(cands[0], "finish_reason", None)
                if fr:
                    finish_reason = str(fr)
            um = getattr(chunk, "usage_metadata", None)
            if um is not None:
                for k in ("prompt_token_count", "candidates_token_count", "total_token_count"):
                    v = getattr(um, k, None)
                    if v is not None:
                        usage[k] = v

        finished = time.perf_counter()
        ttft_ms = (
            (first_token_at - started) * 1000.0 if first_token_at is not None else None
        )
        return CompletionResult(
            actual_output="".join(content_parts),
            latency_total_ms=(finished - started) * 1000.0,
            latency_ttft_ms=ttft_ms,
            tokens_in=usage.get("prompt_token_count"),
            tokens_out=usage.get("candidates_token_count"),
            cost_usd=_compute_cost(model, usage),
            finish_reason=finish_reason,
            raw_provider="google",
        )
