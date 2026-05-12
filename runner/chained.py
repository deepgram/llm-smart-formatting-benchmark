"""Chained Impeller -> Stem -> LLM benchmark runner."""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import hashlib
import json
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
    TimeRemainingColumn,
)

from runner.baseline import BASELINE_MODEL_ID, run_baseline, write_baseline_manifest
from runner.checkpoint import RESPONSES_FIELDS
from runner.models import ModelEntry
from runner.openrouter import CompletionResult, OpenRouterClient
from runner.runner import Sample, dataset_checksum, load_samples, make_run_id


console = Console()

CHAIN_RESPONSE_FIELDS: list[str] = RESPONSES_FIELDS + [
    "chain_input_text",
    "baseline_model_id",
    "baseline_error",
]


@dataclass
class ChainedStats:
    total: int = 0
    done: int = 0
    errors: int = 0
    cost_usd: float = 0.0


def _prompt_hash(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:12]


def _build_messages(
    system_prompt: str, formatting_prompt: str, input_text: str
) -> list[dict[str, str]]:
    fp = (formatting_prompt or "").strip()
    system = (
        f"{system_prompt}\n\nFormatting instructions:\n{fp}"
        if fp
        else system_prompt
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"<transcript>\n{input_text}\n</transcript>"},
    ]


def _responses_path(run_dir: Path) -> Path:
    return run_dir / "responses.csv"


def _ensure_chain_header(run_dir: Path) -> None:
    path = _responses_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CHAIN_RESPONSE_FIELDS).writeheader()


def _load_completed(run_dir: Path) -> set[tuple[str, str]]:
    path = _responses_path(run_dir)
    if not path.exists():
        return set()
    with path.open("r", newline="", encoding="utf-8") as f:
        return {
            (row.get("model_id", ""), row.get("sample_id", ""))
            for row in csv.DictReader(f)
        }


def _load_baseline_rows(baseline_dir: Path) -> dict[str, dict[str, str]]:
    path = baseline_dir / "responses.csv"
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as f:
        return {row.get("sample_id", ""): row for row in csv.DictReader(f)}


def _append_chain_row(run_dir: Path, row: dict[str, Any]) -> None:
    out = {k: ("" if row.get(k) is None else row.get(k)) for k in CHAIN_RESPONSE_FIELDS}
    with _responses_path(run_dir).open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CHAIN_RESPONSE_FIELDS).writerow(out)
        f.flush()


def write_chained_manifest(
    run_dir: Path,
    *,
    run_id: str,
    dataset_path: Path,
    limit: int | None,
    models: list[ModelEntry],
    prompt_path: Path,
    prompt_text: str,
    chain_concurrency: int,
    baseline_concurrency: int,
    impeller_url: str,
    stem_url: str,
    baseline_dir: Path,
) -> Path:
    manifest = {
        "run_id": run_id,
        "kind": "impeller_stem_then_llm",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "dataset_checksum": dataset_checksum(dataset_path),
        "dataset_limit": limit,
        "system_prompt_path": str(prompt_path),
        "system_prompt": prompt_text,
        "system_prompt_hash": _prompt_hash(prompt_text),
        "concurrency": chain_concurrency,
        "baseline_concurrency": baseline_concurrency,
        "baseline_dir": str(baseline_dir),
        "baseline": {
            "model_id": BASELINE_MODEL_ID,
            "impeller_url": impeller_url,
            "stem_url": stem_url,
        },
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


async def run_chained_llm(
    *,
    run_id: str,
    run_dir: Path,
    samples: list[Sample],
    models: list[ModelEntry],
    baseline_rows: dict[str, dict[str, str]],
    system_prompt: str,
    concurrency: int,
) -> ChainedStats:
    _ensure_chain_header(run_dir)
    completed = _load_completed(run_dir)
    stats = ChainedStats(total=len(samples) * len(models), done=len(completed))
    write_lock = asyncio.Lock()
    sem = asyncio.Semaphore(concurrency)
    client = OpenRouterClient.from_env()

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

    async def run_one(entry: ModelEntry, sample: Sample, task_id: int) -> None:
        if (entry["model_id"], sample.sample_id) in completed:
            return
        async with sem:
            attempted_at = dt.datetime.now(dt.timezone.utc).isoformat()
            baseline = baseline_rows.get(sample.sample_id, {})
            chain_input = baseline.get("actual_output", "")
            baseline_error = baseline.get("error", "")
            result: CompletionResult
            if baseline_error:
                result = CompletionResult(error=f"baseline error: {baseline_error}")
            elif not chain_input and sample.input_text:
                result = CompletionResult(error="missing baseline output")
            else:
                messages = _build_messages(
                    system_prompt, sample.formatting_prompt, chain_input
                )
                try:
                    result = await client.complete(entry, messages)
                except Exception as exc:  # noqa: BLE001
                    result = CompletionResult(
                        error=f"unhandled: {type(exc).__name__}: {exc}"
                    )

            completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
            if result.cost_usd is not None:
                try:
                    stats.cost_usd += float(result.cost_usd)
                except (TypeError, ValueError):
                    pass
            if result.error:
                stats.errors += 1
            stats.done += 1
            row = {
                "run_id": run_id,
                "model_id": entry["model_id"],
                "provider": f"impeller-stem+{entry['provider']}",
                "sample_id": sample.sample_id,
                "base_prompt_hash": _prompt_hash(system_prompt),
                "formatting_prompt": sample.formatting_prompt,
                # Keep original input for evaluator semantics; preserve the
                # actual LLM input separately for chain debugging.
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
                "chain_input_text": chain_input,
                "baseline_model_id": BASELINE_MODEL_ID,
                "baseline_error": baseline_error,
            }
            async with write_lock:
                _append_chain_row(run_dir, row)
            progress.update(
                task_id,
                advance=1,
                description=(
                    f"[cyan]{entry['model_id']}[/cyan] "
                    f"err={stats.errors} ${stats.cost_usd:.4f}"
                ),
            )

    try:
        with progress:
            for entry in models:
                todo = [
                    s
                    for s in samples
                    if (entry["model_id"], s.sample_id) not in completed
                ]
                if not todo:
                    console.print(
                        f"[green]{entry['model_id']}: all {len(samples)} samples already done.[/green]"
                    )
                    continue
                task_id = progress.add_task(
                    f"[cyan]{entry['model_id']}[/cyan]", total=len(todo)
                )
                await asyncio.gather(*(run_one(entry, s, task_id) for s in todo))
    finally:
        await client.aclose()

    return stats


def run_chained_sync(
    *,
    dataset: Path,
    prompt: Path,
    models: list[ModelEntry],
    run_id_spec: str,
    results_root: Path,
    limit: int | None,
    baseline_concurrency: int,
    llm_concurrency: int,
    impeller_url: str,
    stem_url: str,
    timeout: float,
) -> Path:
    samples = load_samples(dataset, limit=limit)
    prompt_text = prompt.read_text(encoding="utf-8").strip()
    rid = make_run_id(run_id_spec)
    run_dir = results_root / rid
    baseline_dir = run_dir / "impeller_stem"
    run_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir.mkdir(parents=True, exist_ok=True)

    write_chained_manifest(
        run_dir,
        run_id=rid,
        dataset_path=dataset,
        limit=limit,
        models=models,
        prompt_path=prompt,
        prompt_text=prompt_text,
        chain_concurrency=llm_concurrency,
        baseline_concurrency=baseline_concurrency,
        impeller_url=impeller_url,
        stem_url=stem_url,
        baseline_dir=baseline_dir,
    )
    write_baseline_manifest(
        baseline_dir,
        run_id=f"{rid}-impeller-stem",
        dataset_path=dataset,
        limit=limit,
        concurrency=baseline_concurrency,
        impeller_url=impeller_url,
        stem_url=stem_url,
    )

    console.print(
        f"Loaded [bold]{len(samples)}[/bold] samples from {dataset}; "
        f"running Impeller -> Stem -> [bold]{len(models)}[/bold] LLM model(s)."
    )
    console.print(f"Run id: [bold]{rid}[/bold]")
    console.print(f"Run dir: [bold]{run_dir}[/bold]")

    baseline_stats = asyncio.run(
        run_baseline(
            run_id=f"{rid}-impeller-stem",
            run_dir=baseline_dir,
            samples=samples,
            concurrency=baseline_concurrency,
            impeller_url=impeller_url,
            stem_url=stem_url,
            timeout=timeout,
        )
    )
    console.print(
        f"Baseline rows: {baseline_stats.done}/{baseline_stats.total} "
        f"errors={baseline_stats.errors}"
    )

    stats = asyncio.run(
        run_chained_llm(
            run_id=rid,
            run_dir=run_dir,
            samples=samples,
            models=models,
            baseline_rows=_load_baseline_rows(baseline_dir),
            system_prompt=prompt_text,
            concurrency=llm_concurrency,
        )
    )
    console.rule("[bold]Chained run complete[/bold]")
    console.print(f"Output: [bold]{run_dir / 'responses.csv'}[/bold]")
    console.print(f"Intermediate baseline: [bold]{baseline_dir / 'responses.csv'}[/bold]")
    console.print(f"Manifest: [bold]{run_dir / 'run_manifest.json'}[/bold]")
    console.print(f"Total rows attempted: {stats.done}/{stats.total}")
    console.print(f"Errors: [red]{stats.errors}[/red]")
    console.print(f"Total LLM cost: [bold]${stats.cost_usd:.4f}[/bold]")
    return run_dir
