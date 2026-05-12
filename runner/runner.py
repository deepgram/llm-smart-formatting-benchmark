"""Orchestration: load CSV, iterate models x samples, write results."""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from runner.checkpoint import (
    DETERMINISM_FIELDS,
    append_determinism_row,
    append_response,
    determinism_csv_path,
    ensure_determinism_header,
    ensure_responses_header,
    load_completed,
    load_completed_determinism,
    responses_csv_path,
)
from runner.models import ModelEntry
from runner.openrouter import (
    CompletionResult,
    OpenRouterClient,
    build_request_body,
)
from runner.prompts import BASE_PROMPT, base_prompt_hash, build_messages


# ----------------- Client dispatch by route -----------------


def _build_clients(models: list[ModelEntry]) -> dict[str, Any]:
    """Build only the clients we actually need for this run."""
    routes_needed = {m.get("route", "openrouter") for m in models}
    clients: dict[str, Any] = {}
    if "openrouter" in routes_needed:
        clients["openrouter"] = OpenRouterClient.from_env()
    if "anthropic" in routes_needed:
        from runner.anthropic_client import AnthropicClient

        clients["anthropic"] = AnthropicClient.from_env()
    if "openai" in routes_needed:
        from runner.openai_client import OpenAIClient

        clients["openai"] = OpenAIClient.from_env()
    if "google" in routes_needed:
        from runner.google_client import GoogleClient

        clients["google"] = GoogleClient.from_env()
    return clients


async def _aclose_clients(clients: dict[str, Any]) -> None:
    for c in clients.values():
        try:
            await c.aclose()
        except Exception:
            pass


console = Console()


# ----------------- Sample loading -----------------


@dataclass(frozen=True)
class Sample:
    sample_id: str
    formatting_prompt: str
    input_text: str
    expected_output: str


def load_samples(dataset_path: Path, *, limit: int | None = None) -> list[Sample]:
    df = pd.read_csv(dataset_path, dtype=str, keep_default_na=False)
    required = {"id", "prompt", "input_text", "expected_output"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"dataset missing columns: {missing}")
    out: list[Sample] = []
    for _, row in df.iterrows():
        out.append(
            Sample(
                sample_id=str(row["id"]),
                formatting_prompt=str(row["prompt"] or ""),
                input_text=str(row["input_text"] or ""),
                expected_output=str(row["expected_output"] or ""),
            )
        )
    if limit is not None:
        out = out[:limit]
    return out


def dataset_checksum(dataset_path: Path) -> str:
    h = hashlib.sha256()
    with dataset_path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


# ----------------- Run id + manifest -----------------


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(s: str) -> str:
    s = s.lower()
    s = _SLUG_RE.sub("-", s).strip("-")
    return s[:24] or "run"


def make_run_id(spec: str | None) -> str:
    if spec and spec != "auto":
        return spec
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Append a tiny random-ish slug from time microseconds for uniqueness.
    micro = dt.datetime.now().strftime("%f")[:4]
    return f"{ts}-{_slugify(micro)}"


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return None


def write_manifest(
    run_dir: Path,
    *,
    run_id: str,
    models: list[ModelEntry],
    sampling_defaults: dict[str, Any],
    dataset_path: Path,
    base_prompt: str,
    parallel_models: int,
    concurrency: int,
    limit: int | None,
) -> Path:
    manifest = {
        "run_id": run_id,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "dataset_path": str(dataset_path),
        "dataset_checksum": dataset_checksum(dataset_path),
        "dataset_limit": limit,
        "base_prompt": base_prompt,
        "base_prompt_hash": base_prompt_hash(),
        "sampling_defaults": sampling_defaults,
        "concurrency": concurrency,
        "parallel_models": parallel_models,
        "models": [
            {
                "model_id": m["model_id"],
                "provider": m["provider"],
                "openrouter_slug": m["openrouter_slug"],
                "temperature": m.get("temperature"),
                "top_p": m.get("top_p"),
                "max_tokens": m.get("max_tokens"),
                "extra_body": m.get("extra_body") or {},
                "provider_routing": m.get("provider_routing") or {},
                "supports_streaming": m.get("supports_streaming", True),
                "notes": m.get("notes", ""),
            }
            for m in models
        ],
    }
    path = run_dir / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


# ----------------- Dry run -----------------


def dry_run_preview(
    models: list[ModelEntry],
    samples: list[Sample],
    *,
    n: int = 3,
) -> None:
    """Print the first ``n`` fully-rendered request payloads. No API calls."""
    console.rule("[bold cyan]DRY RUN — no API calls will be made[/bold cyan]")
    console.print(f"Base prompt hash: [bold]{base_prompt_hash()}[/bold]")
    console.print(f"Models selected ({len(models)}):")
    for m in models:
        thinking = "thinking" in (m.get("extra_body") or {}) or "reasoning" in (
            m.get("extra_body") or {}
        )
        console.print(
            f"  - [bold]{m['model_id']}[/bold] -> "
            f"{m['openrouter_slug']} "
            f"(provider={m['provider']}, max_tokens={m.get('max_tokens')}, "
            f"thinking={thinking}, "
            f"provider_routing={m.get('provider_routing') or 'default'})"
        )
    console.rule(f"[bold]First {n} request payloads (using first model)[/bold]")
    if not models:
        console.print("[red]No models selected.[/red]")
        return
    head_model = models[0]
    for sample in samples[:n]:
        messages = build_messages(sample.input_text, sample.formatting_prompt)
        body = build_request_body(head_model, messages, stream=True)
        console.print(f"[bold yellow]sample_id={sample.sample_id}[/bold yellow]")
        console.print(f"  formatting_prompt: {sample.formatting_prompt!r}")
        console.print(f"  expected_output:   {sample.expected_output!r}")
        console.print("  request body:")
        console.print(json.dumps(body, indent=2, ensure_ascii=False))
        console.rule()


# ----------------- Main run loop -----------------


@dataclass
class RunStats:
    total: int = 0
    done: int = 0
    errors: int = 0
    cost_usd: float = 0.0


async def _run_one(
    clients: dict[str, Any],
    sem: asyncio.Semaphore,
    entry: ModelEntry,
    sample: Sample,
    run_id: str,
    run_dir: Path,
    stats: RunStats,
    progress: Progress,
    task_id: int,
) -> None:
    async with sem:
        attempted_at = dt.datetime.now(dt.timezone.utc).isoformat()
        messages = build_messages(sample.input_text, sample.formatting_prompt)
        route = entry.get("route", "openrouter")
        client = clients.get(route)
        if client is None:
            result = CompletionResult(error=f"no client for route={route!r}")
            completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
            stats.errors += 1
            stats.done += 1
            row = _row_from_result(entry, sample, run_id, attempted_at, completed_at, result)
            append_response(run_dir, row)
            progress.update(task_id, advance=1)
            return
        try:
            result = await client.complete(entry, messages)
        except Exception as e:  # last-resort safety net
            result = CompletionResult(error=f"unhandled: {type(e).__name__}: {e}")
        completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
        if result.cost_usd:
            try:
                stats.cost_usd += float(result.cost_usd)
            except (TypeError, ValueError):
                pass
        if result.error:
            stats.errors += 1
        stats.done += 1
        row = _row_from_result(entry, sample, run_id, attempted_at, completed_at, result)
        append_response(run_dir, row)
        progress.update(
            task_id,
            advance=1,
            description=(
                f"[cyan]{entry['model_id']}[/cyan] "
                f"err={stats.errors} ${stats.cost_usd:.4f}"
            ),
        )


def _row_from_result(
    entry: ModelEntry,
    sample: Sample,
    run_id: str,
    attempted_at: str,
    completed_at: str,
    result: CompletionResult,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "model_id": entry["model_id"],
        "provider": entry["provider"],
        "sample_id": sample.sample_id,
        "base_prompt_hash": base_prompt_hash(),
        "formatting_prompt": sample.formatting_prompt,
        "input_text": sample.input_text,
        "expected_output": sample.expected_output,
        "actual_output": result.actual_output,
        "latency_total_ms": (
            f"{result.latency_total_ms:.2f}"
            if result.latency_total_ms is not None
            else ""
        ),
        "latency_ttft_ms": (
            f"{result.latency_ttft_ms:.2f}"
            if result.latency_ttft_ms is not None
            else ""
        ),
        "tokens_in": result.tokens_in if result.tokens_in is not None else "",
        "tokens_out": result.tokens_out if result.tokens_out is not None else "",
        "cost_usd": result.cost_usd if result.cost_usd is not None else "",
        "finish_reason": result.finish_reason or "",
        "error": result.error or "",
        "attempted_at": attempted_at,
        "completed_at": completed_at,
    }


async def run_model(
    clients: dict[str, Any],
    entry: ModelEntry,
    samples: list[Sample],
    run_id: str,
    run_dir: Path,
    *,
    concurrency: int,
    progress: Progress,
    stats: RunStats,
) -> None:
    completed = load_completed(run_dir)
    todo = [s for s in samples if (entry["model_id"], s.sample_id) not in completed]
    if not todo:
        console.print(
            f"[green]{entry['model_id']}: all {len(samples)} samples already done — skipping.[/green]"
        )
        return
    sem = asyncio.Semaphore(concurrency)
    task_id = progress.add_task(
        f"[cyan]{entry['model_id']}[/cyan]", total=len(todo)
    )
    tasks = [
        asyncio.create_task(
            _run_one(
                clients, sem, entry, s, run_id, run_dir, stats, progress, task_id
            )
        )
        for s in todo
    ]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        raise


async def run_benchmark(
    *,
    run_id: str,
    run_dir: Path,
    models: list[ModelEntry],
    samples: list[Sample],
    concurrency: int,
    parallel_models: int,
) -> RunStats:
    ensure_responses_header(run_dir)
    stats = RunStats(total=len(models) * len(samples))
    clients = _build_clients(models)
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("ETA"),
        TimeRemainingColumn(),
        console=console,
    )
    try:
        with progress:
            if parallel_models <= 1:
                for entry in models:
                    await run_model(
                        clients,
                        entry,
                        samples,
                        run_id,
                        run_dir,
                        concurrency=concurrency,
                        progress=progress,
                        stats=stats,
                    )
            else:
                model_sem = asyncio.Semaphore(parallel_models)

                async def bounded(entry: ModelEntry) -> None:
                    async with model_sem:
                        await run_model(
                            clients,
                            entry,
                            samples,
                            run_id,
                            run_dir,
                            concurrency=concurrency,
                            progress=progress,
                            stats=stats,
                        )

                await asyncio.gather(*(bounded(m) for m in models))
    finally:
        await _aclose_clients(clients)
    return stats


def summarize_run(run_dir: Path, stats: RunStats) -> None:
    console.rule("[bold]Run complete[/bold]")
    console.print(f"Output: [bold]{responses_csv_path(run_dir)}[/bold]")
    console.print(f"Manifest: [bold]{run_dir / 'run_manifest.json'}[/bold]")
    console.print(f"Total rows attempted: {stats.done}/{stats.total}")
    console.print(f"Errors: [red]{stats.errors}[/red]")
    console.print(f"Total cost (from OpenRouter usage): [bold]${stats.cost_usd:.4f}[/bold]")


# ============================================================
# Determinism eval — N trials of each (model, sample) at fixed input
# ============================================================


@dataclass(frozen=True)
class DetSample:
    """A determinism subset Sample (decoupled from runner.Sample so we can
    carry entity_class / source through to the responses CSV downstream."""

    sample_id: str
    formatting_prompt: str
    input_text: str
    expected_output: str


async def _run_one_determinism(
    *,
    clients: dict[str, Any],
    sem: asyncio.Semaphore,
    entry: ModelEntry,
    sample: DetSample,
    trial: int,
    system_prompt: str,
    run_id: str,
    run_dir: Path,
    stats: RunStats,
    progress: Progress,
    task_id: int,
) -> None:
    async with sem:
        attempted_at = dt.datetime.now(dt.timezone.utc).isoformat()
        # Compose messages with the explicit system prompt (overrides BASE_PROMPT
        # for determinism runs so we can pin to e.g. iter-009).
        fp = (sample.formatting_prompt or "").strip()
        system = system_prompt if not fp else f"{system_prompt}\n\nFormatting instructions:\n{fp}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": sample.input_text},
        ]
        route = entry.get("route", "openrouter")
        client = clients.get(route)
        if client is None:
            result = CompletionResult(error=f"no client for route={route!r}")
        else:
            try:
                result = await client.complete(entry, messages)
            except Exception as e:  # last-resort safety net
                result = CompletionResult(error=f"unhandled: {type(e).__name__}: {e}")
        completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
        if result.cost_usd:
            try:
                stats.cost_usd += float(result.cost_usd)
            except (TypeError, ValueError):
                pass
        if result.error:
            stats.errors += 1
        stats.done += 1
        row: dict[str, Any] = {
            "run_id": run_id,
            "model_id": entry["model_id"],
            "provider": entry["provider"],
            "sample_id": sample.sample_id,
            "trial": trial,
            "base_prompt_hash": hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:12],
            "formatting_prompt": sample.formatting_prompt,
            "input_text": sample.input_text,
            "expected_output": sample.expected_output,
            "actual_output": result.actual_output,
            "latency_total_ms": (
                f"{result.latency_total_ms:.2f}"
                if result.latency_total_ms is not None
                else ""
            ),
            "latency_ttft_ms": (
                f"{result.latency_ttft_ms:.2f}"
                if result.latency_ttft_ms is not None
                else ""
            ),
            "tokens_in": result.tokens_in if result.tokens_in is not None else "",
            "tokens_out": result.tokens_out if result.tokens_out is not None else "",
            "cost_usd": result.cost_usd if result.cost_usd is not None else "",
            "finish_reason": result.finish_reason or "",
            "error": result.error or "",
            "attempted_at": attempted_at,
            "completed_at": completed_at,
        }
        append_determinism_row(run_dir, row)
        progress.update(
            task_id,
            advance=1,
            description=(
                f"[cyan]{entry['model_id']}[/cyan] "
                f"err={stats.errors} ${stats.cost_usd:.4f}"
            ),
        )


async def run_determinism(
    *,
    run_id: str,
    run_dir: Path,
    models: list[ModelEntry],
    samples: list[DetSample],
    trials: int,
    system_prompt: str,
    concurrency: int,
    parallel_models: int,
) -> RunStats:
    """Run each (model, sample) `trials` times. Append rows as they complete."""
    ensure_determinism_header(run_dir)
    completed = load_completed_determinism(run_dir)
    stats = RunStats(total=len(models) * len(samples) * trials)
    # Subtract already-done from the "todo" count so progress totals are correct.
    stats.done = len(completed)

    clients = _build_clients(models)
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("ETA"),
        TimeRemainingColumn(),
        console=console,
    )

    async def run_model_det(entry: ModelEntry) -> None:
        todo: list[tuple[DetSample, int]] = []
        for s in samples:
            for t in range(1, trials + 1):
                if (entry["model_id"], s.sample_id, t) not in completed:
                    todo.append((s, t))
        if not todo:
            console.print(
                f"[green]{entry['model_id']}: all {len(samples) * trials} trials already done — skipping.[/green]"
            )
            return
        sem = asyncio.Semaphore(concurrency)
        task_id = progress.add_task(
            f"[cyan]{entry['model_id']}[/cyan]", total=len(todo)
        )
        tasks = [
            asyncio.create_task(
                _run_one_determinism(
                    clients=clients,
                    sem=sem,
                    entry=entry,
                    sample=s,
                    trial=t,
                    system_prompt=system_prompt,
                    run_id=run_id,
                    run_dir=run_dir,
                    stats=stats,
                    progress=progress,
                    task_id=task_id,
                )
            )
            for s, t in todo
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for t in tasks:
                t.cancel()
            raise

    try:
        with progress:
            if parallel_models <= 1:
                for entry in models:
                    await run_model_det(entry)
            else:
                model_sem = asyncio.Semaphore(parallel_models)

                async def bounded(entry: ModelEntry) -> None:
                    async with model_sem:
                        await run_model_det(entry)

                await asyncio.gather(*(bounded(m) for m in models))
    finally:
        await _aclose_clients(clients)
    return stats


def write_determinism_manifest(
    run_dir: Path,
    *,
    run_id: str,
    models: list[ModelEntry],
    sampling_defaults: dict[str, Any],
    dataset_path: Path,
    system_prompt: str,
    system_prompt_path: str,
    trials: int,
    concurrency: int,
    parallel_models: int,
    n_samples: int,
) -> Path:
    manifest = {
        "run_id": run_id,
        "kind": "determinism",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "dataset_path": str(dataset_path),
        "dataset_checksum": dataset_checksum(dataset_path),
        "system_prompt_path": system_prompt_path,
        "system_prompt": system_prompt,
        "system_prompt_hash": hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:12],
        "trials": trials,
        "n_samples": n_samples,
        "concurrency": concurrency,
        "parallel_models": parallel_models,
        "sampling_defaults": sampling_defaults,
        "models": [
            {
                "model_id": m["model_id"],
                "provider": m["provider"],
                "openrouter_slug": m["openrouter_slug"],
                "temperature": m.get("temperature"),
                "top_p": m.get("top_p"),
                "max_tokens": m.get("max_tokens"),
                "extra_body": m.get("extra_body") or {},
                "provider_routing": m.get("provider_routing") or {},
                "notes": m.get("notes", ""),
            }
            for m in models
        ],
    }
    path = run_dir / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


def summarize_determinism_run(run_dir: Path, stats: RunStats) -> None:
    console.rule("[bold]Determinism run complete[/bold]")
    console.print(f"Output: [bold]{determinism_csv_path(run_dir)}[/bold]")
    console.print(f"Manifest: [bold]{run_dir / 'run_manifest.json'}[/bold]")
    console.print(f"Total trials attempted: {stats.done}/{stats.total}")
    console.print(f"Errors: [red]{stats.errors}[/red]")
    console.print(f"Total cost (from OpenRouter usage): [bold]${stats.cost_usd:.4f}[/bold]")
    console.print(
        "[dim]Score with: [bold]uv run evaluator determinism --responses "
        f"{determinism_csv_path(run_dir)}[/bold][/dim]"
    )
