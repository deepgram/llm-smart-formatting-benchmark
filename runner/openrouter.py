"""Async OpenRouter client with streaming + latency capture."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import BaseModel

from runner.models import ModelEntry
from runner.prompts import ChatMessage


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CHAT_COMPLETIONS_PATH = "/chat/completions"

# OpenRouter recommends setting these headers for app attribution.
DEFAULT_REFERER = "https://github.com/cresta/smart-formatting-llm-benchmark"
DEFAULT_TITLE = "smart-formatting-llm-benchmark"


class CompletionResult(BaseModel):
    """What the runner needs back from a single API call."""

    actual_output: str = ""
    latency_total_ms: float | None = None
    latency_ttft_ms: float | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None
    finish_reason: str | None = None
    error: str | None = None
    raw_provider: str | None = None  # whatever provider OpenRouter actually routed to


@dataclass
class StreamAccumulator:
    """Collects streamed chunks and tracks latency."""

    started_at: float
    first_token_at: float | None = None
    finished_at: float | None = None
    content_parts: list[str] = field(default_factory=list)
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    raw_provider: str | None = None

    def record_chunk(self, chunk: dict[str, Any]) -> None:
        # Provider attribution (OpenRouter sometimes includes this).
        if self.raw_provider is None and chunk.get("provider"):
            self.raw_provider = chunk["provider"]
        choices = chunk.get("choices") or []
        if choices:
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                if self.first_token_at is None:
                    self.first_token_at = time.perf_counter()
                self.content_parts.append(content)
            fr = choices[0].get("finish_reason")
            if fr:
                self.finish_reason = fr
        usage = chunk.get("usage")
        if usage:
            self.usage = usage


def build_request_body(
    entry: ModelEntry,
    messages: list[ChatMessage],
    *,
    stream: bool,
) -> dict[str, Any]:
    """Assemble the JSON body for OpenRouter."""
    body: dict[str, Any] = {
        "model": entry["openrouter_slug"],
        "messages": list(messages),
        "temperature": entry.get("temperature", 0.0),
        "top_p": entry.get("top_p", 1.0),
        "max_tokens": entry.get("max_tokens", 1024),
        "stream": stream,
        # Ask OpenRouter to include usage + cost in the response.
        "usage": {"include": True},
    }
    if entry.get("provider_routing"):
        body["provider"] = dict(entry["provider_routing"])
    extra = entry.get("extra_body") or {}
    for k, v in extra.items():
        body[k] = v
    return body


class OpenRouterClient:
    """Thin async client around the OpenRouter chat completions endpoint."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 120.0,
        max_retries: int = 3,
        referer: str = DEFAULT_REFERER,
        title: str = DEFAULT_TITLE,
    ) -> None:
        self.api_key = api_key
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=OPENROUTER_BASE_URL,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": referer,
                "X-Title": title,
                "Content-Type": "application/json",
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def from_env() -> OpenRouterClient:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Export it before running."
            )
        return OpenRouterClient(key)

    async def complete(
        self,
        entry: ModelEntry,
        messages: list[ChatMessage],
    ) -> CompletionResult:
        """Run one completion. Tries streaming first; falls back to non-stream
        on 4xx that look like 'streaming not supported'. Retries on 429/5xx.
        """
        if entry.get("supports_streaming", True):
            try:
                return await self._with_retries(
                    self._complete_streaming, entry, messages
                )
            except _StreamingUnsupported:
                # Fall through to non-streaming.
                pass
        return await self._with_retries(self._complete_nonstreaming, entry, messages)

    async def _with_retries(self, fn, entry, messages) -> CompletionResult:  # type: ignore[no-untyped-def]
        last_err: str | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await fn(entry, messages)
            except _StreamingUnsupported:
                raise
            except _RetryableError as e:
                last_err = str(e)
                if attempt >= self.max_retries:
                    break
                # Exponential backoff: 1s, 2s, 4s, ...
                await asyncio.sleep(2**attempt)
            except Exception as e:  # non-retryable
                return CompletionResult(error=f"{type(e).__name__}: {e}")
        return CompletionResult(error=last_err or "unknown error after retries")

    async def _complete_streaming(
        self, entry: ModelEntry, messages: list[ChatMessage]
    ) -> CompletionResult:
        body = build_request_body(entry, messages, stream=True)
        acc = StreamAccumulator(started_at=time.perf_counter())
        try:
            async with self._client.stream(
                "POST", CHAT_COMPLETIONS_PATH, json=body
            ) as resp:
                if resp.status_code == 400:
                    text = (await resp.aread()).decode("utf-8", "replace")
                    if "stream" in text.lower() and "support" in text.lower():
                        raise _StreamingUnsupported(text)
                    return CompletionResult(error=f"400: {text[:500]}")
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    text = (await resp.aread()).decode("utf-8", "replace")
                    raise _RetryableError(f"{resp.status_code}: {text[:300]}")
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", "replace")
                    return CompletionResult(
                        error=f"{resp.status_code}: {text[:500]}"
                    )

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith(":"):  # SSE comment / keep-alive
                        continue
                    if line.startswith("data: "):
                        payload = line[len("data: "):]
                    else:
                        payload = line
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    if "error" in chunk:
                        err = chunk["error"]
                        msg = err.get("message") if isinstance(err, dict) else str(err)
                        code = err.get("code") if isinstance(err, dict) else None
                        if code in (429,) or (
                            isinstance(code, int) and 500 <= code < 600
                        ):
                            raise _RetryableError(f"stream-error {code}: {msg}")
                        return CompletionResult(error=f"stream-error: {msg}")
                    acc.record_chunk(chunk)
            acc.finished_at = time.perf_counter()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            raise _RetryableError(f"network: {e}") from e

        return _result_from_accumulator(acc)

    async def _complete_nonstreaming(
        self, entry: ModelEntry, messages: list[ChatMessage]
    ) -> CompletionResult:
        body = build_request_body(entry, messages, stream=False)
        started = time.perf_counter()
        try:
            resp = await self._client.post(CHAT_COMPLETIONS_PATH, json=body)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            raise _RetryableError(f"network: {e}") from e
        finished = time.perf_counter()
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            raise _RetryableError(f"{resp.status_code}: {resp.text[:300]}")
        if resp.status_code >= 400:
            return CompletionResult(error=f"{resp.status_code}: {resp.text[:500]}")
        try:
            data = resp.json()
        except json.JSONDecodeError:
            return CompletionResult(error=f"non-json response: {resp.text[:300]}")
        choices = data.get("choices") or []
        content = ""
        finish_reason = None
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content") or ""
            finish_reason = choices[0].get("finish_reason")
        usage = data.get("usage") or {}
        return CompletionResult(
            actual_output=content,
            latency_total_ms=(finished - started) * 1000.0,
            latency_ttft_ms=None,
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
            cost_usd=usage.get("cost") or usage.get("total_cost"),
            finish_reason=finish_reason,
            raw_provider=data.get("provider"),
        )


def _result_from_accumulator(acc: StreamAccumulator) -> CompletionResult:
    end = acc.finished_at or time.perf_counter()
    total_ms = (end - acc.started_at) * 1000.0
    ttft_ms: float | None = None
    if acc.first_token_at is not None:
        ttft_ms = (acc.first_token_at - acc.started_at) * 1000.0
    usage = acc.usage or {}
    return CompletionResult(
        actual_output="".join(acc.content_parts),
        latency_total_ms=total_ms,
        latency_ttft_ms=ttft_ms,
        tokens_in=usage.get("prompt_tokens"),
        tokens_out=usage.get("completion_tokens"),
        cost_usd=usage.get("cost") or usage.get("total_cost"),
        finish_reason=acc.finish_reason,
        raw_provider=acc.raw_provider,
    )


class _RetryableError(Exception):
    """Raised on 429/5xx/transient network errors so the caller can back off."""


class _StreamingUnsupported(Exception):
    """Raised when the model rejects streaming so the caller can retry without."""
