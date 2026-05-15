"""Async inference over the eval set, writing the parent-runner schema.

Output: ``results/<run_id>/responses.csv`` with the same columns as
``runner/checkpoint.py::RESPONSES_FIELDS`` — so the parent evaluator can
score it without modification:

    uv run evaluator score --responses results/<run_id>
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from finetune.dataset import Row
from finetune.prompts import build_messages, prompt_hash
from runner.checkpoint import (
    RESPONSES_FIELDS,
    append_response,
    ensure_responses_header,
    load_completed,
)


console = Console()


@dataclass
class InferConfig:
    model_id: str            # logical id we write to responses.csv (e.g. "ft-llama-3.2-3b-iter1")
    together_model: str      # actual Together model name to call
    run_dir: Path
    run_id: str
    concurrency: int = 8
    max_tokens: int = 1024
    temperature: float = 0.0


async def _one_call(
    cfg: InferConfig,
    row: Row,
    sem: asyncio.Semaphore,
    progress: Progress,
    task_id: int,
) -> None:
    """One inference call, written straight to responses.csv."""
    # Lazy import so the SDK is only loaded when we actually infer.
    from finetune.together_client import _client

    client = _client()
    messages = build_messages(row.input_text, row.formatting_prompt)

    attempted = dt.datetime.now(dt.timezone.utc).isoformat()
    actual_output = ""
    finish_reason = ""
    error = ""
    tokens_in = 0
    tokens_out = 0
    req_started: float | None = None
    req_finished: float | None = None
    first_token_at: float | None = None

    def _stream_call() -> tuple[str, str, int, int, float, float, float | None]:
        # Timings captured INSIDE the thread so they exclude:
        #   - asyncio semaphore queue wait
        #   - asyncio.to_thread dispatch
        # latency_total_ms = req_finished - req_started  (request sent → stream closed)
        # latency_ttft_ms  = first_token_at - req_started (request sent → first content chunk)
        # perf_counter is monotonic per-process and safe to read across threads.
        parts: list[str] = []
        fr = ""
        t_in = 0
        t_out = 0
        ft: float | None = None
        # `chat_template_kwargs={"enable_thinking": False}` forces no <think> blocks
        # on Qwen3/Qwen3.5; no-op for chat templates that don't reference the var.
        # Together SDK has no `stream_options` param; usage may or may not appear
        # in the final chunk depending on backend. We populate token counts when
        # present, leave 0 when not.
        started = time.perf_counter()
        stream = client.chat.completions.create(
            model=cfg.together_model,
            messages=messages,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            stream=True,
            chat_template_kwargs={"enable_thinking": False},
        )
        for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if choices:
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    if ft is None:
                        ft = time.perf_counter()
                    parts.append(content)
                cfr = getattr(choices[0], "finish_reason", None)
                if cfr:
                    fr = str(cfr)
            usage = getattr(chunk, "usage", None)
            if usage is not None:
                t_in = int(getattr(usage, "prompt_tokens", 0) or 0)
                t_out = int(getattr(usage, "completion_tokens", 0) or 0)
        finished = time.perf_counter()
        return "".join(parts), fr, t_in, t_out, started, finished, ft

    async with sem:
        try:
            text, finish_reason, tokens_in, tokens_out, req_started, req_finished, first_token_at = await asyncio.to_thread(_stream_call)
            actual_output = text.strip()
        except Exception as e:  # noqa: BLE001
            error = f"{type(e).__name__}: {e}"

    if req_started is not None and req_finished is not None:
        latency_ms: int | str = int((req_finished - req_started) * 1000)
        ttft_ms: int | str = (
            int((first_token_at - req_started) * 1000) if first_token_at is not None else ""
        )
    else:
        latency_ms = ""
        ttft_ms = ""
    completed = dt.datetime.now(dt.timezone.utc).isoformat()

    append_response(
        cfg.run_dir,
        {
            "run_id": cfg.run_id,
            "model_id": cfg.model_id,
            "provider": "together",
            "sample_id": row.sample_id,
            "base_prompt_hash": prompt_hash(),
            "formatting_prompt": row.formatting_prompt,
            "input_text": row.input_text,
            "expected_output": row.expected_output,
            "actual_output": actual_output,
            "latency_total_ms": latency_ms,
            "latency_ttft_ms": ttft_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": "",  # not returned per-call
            "finish_reason": finish_reason,
            "error": error,
            "attempted_at": attempted,
            "completed_at": completed,
        },
    )
    progress.update(task_id, advance=1)


async def run_inference(cfg: InferConfig, rows: list[Row]) -> None:
    """Resumable: rows already present in responses.csv for this model are skipped."""
    ensure_responses_header(cfg.run_dir)
    done = load_completed(cfg.run_dir)
    todo = [r for r in rows if (cfg.model_id, r.sample_id) not in done]
    if not todo:
        console.print(
            f"[yellow]All {len(rows)} rows already done for "
            f"model_id={cfg.model_id}; nothing to do.[/yellow]"
        )
        return

    sem = asyncio.Semaphore(cfg.concurrency)
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[bold]{cfg.model_id}[/bold]"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(cfg.model_id, total=len(todo))
        await asyncio.gather(*(_one_call(cfg, r, sem, progress, task_id) for r in todo))

    console.print(
        f"[green]Inference done — {len(todo)} new rows written to "
        f"{cfg.run_dir / 'responses.csv'}[/green]"
    )


def run_inference_sync(cfg: InferConfig, rows: list[Row]) -> None:
    asyncio.run(run_inference(cfg, rows))
