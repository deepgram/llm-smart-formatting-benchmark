"""Impeller -> Stem smart-formatting baseline runner."""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
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

from runner.checkpoint import append_response, ensure_responses_header, load_completed
from runner.runner import Sample, dataset_checksum, load_samples, make_run_id


console = Console()
BASELINE_MODEL_ID = "impeller-stem-baseline"
BASELINE_PROVIDER = "deepgram"
BASELINE_PROMPT_HASH = hashlib.sha256(
    b"impeller-v2-read-to-stem-dev-format-entities-v1"
).hexdigest()[:16]


@dataclass(frozen=True)
class Entity:
    label: str
    start: int
    end: int
    confidence: float


@dataclass(frozen=True)
class TokenSpan:
    text: str
    start: int
    end: int


@dataclass
class BaselineStats:
    total: int = 0
    done: int = 0
    errors: int = 0


_TOKEN_RE = re.compile(r"\S+")
_LABEL_BOUNDARY_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _normalize_label(label: str) -> str:
    label = label.strip().replace("-", "_")
    if "_" in label or label.upper() == label:
        return label.upper()
    return _LABEL_BOUNDARY_RE.sub("_", label).upper()


def _numeric_field(raw: dict[str, Any], names: tuple[str, ...]) -> int | None:
    for name in names:
        value = raw.get(name)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _entities_from_result(result: dict[str, Any], text: str) -> list[Entity]:
    raw_entities = result.get("entities")
    if raw_entities is None:
        raw_entities = result.get("detected_entities")
    if not isinstance(raw_entities, list):
        return []

    entities: list[Entity] = []
    for raw in raw_entities:
        if not isinstance(raw, dict):
            continue
        label = raw.get("label") or raw.get("type") or raw.get("entity_type")
        if not label:
            continue

        start = _numeric_field(raw, ("start", "start_char", "start_index", "begin"))
        end = _numeric_field(raw, ("end", "end_char", "end_index", "stop"))
        value = raw.get("value") or raw.get("text")
        if (start is None or end is None) and isinstance(value, str) and value:
            match_start = text.find(value)
            if match_start >= 0:
                start = match_start
                end = match_start + len(value)
        if start is None or end is None or end <= start:
            continue

        confidence = raw.get("confidence", raw.get("score", 0.0))
        try:
            confidence_float = float(confidence)
        except (TypeError, ValueError):
            confidence_float = 0.0

        entities.append(
            Entity(
                label=_normalize_label(str(label)),
                start=max(0, start),
                end=min(len(text), end),
                confidence=confidence_float,
            )
        )
    return entities


def extract_entities(payload: dict[str, Any], sample_index: int, text: str) -> list[Entity]:
    results = payload.get("results")
    if isinstance(results, list) and sample_index < len(results):
        result = results[sample_index]
        if isinstance(result, dict):
            return _entities_from_result(result, text)
    return []


def weave_entity_tags(text: str, entities: list[Entity]) -> str:
    tokens = [
        TokenSpan(match.group(0), match.start(), match.end())
        for match in _TOKEN_RE.finditer(text)
    ]
    if not tokens:
        return text

    spans: list[tuple[int, int, Entity]] = []
    for entity in sorted(entities, key=lambda item: item.confidence, reverse=True):
        first = next((idx for idx, token in enumerate(tokens) if token.end > entity.start), None)
        last = next(
            (
                idx
                for idx in range(len(tokens) - 1, -1, -1)
                if tokens[idx].start < entity.end
            ),
            None,
        )
        if first is None or last is None or first > last:
            continue
        if any(not (last < span_first or first > span_last) for span_first, span_last, _ in spans):
            continue
        spans.append((first, last, entity))

    spans.sort(key=lambda item: item[0])
    opens: dict[int, list[str]] = {}
    closes: dict[int, list[str]] = {}
    for first, last, entity in spans:
        opens.setdefault(first, []).append("<entity>")
        closes.setdefault(last, []).append(f"</entity_{entity.label}>")

    out: list[str] = []
    for idx, token in enumerate(tokens):
        out.extend(opens.get(idx, []))
        out.append(token.text)
        out.extend(closes.get(idx, []))
    return " ".join(out)


async def _format_one(
    client: httpx.AsyncClient,
    *,
    impeller_url: str,
    stem_url: str,
    sample: Sample,
    run_id: str,
) -> dict[str, Any]:
    attempted_at = dt.datetime.now(dt.timezone.utc).isoformat()
    start_time = time.perf_counter()
    error = ""
    actual_output = ""
    finish_reason = "stop"

    try:
        ner_response = await client.post(
            f"{impeller_url.rstrip('/')}/read",
            json={"texts": [sample.input_text], "detect_entities": {}},
        )
        ner_response.raise_for_status()
        ner_payload = ner_response.json()
        entities = extract_entities(ner_payload, 0, sample.input_text)
        tagged_text = weave_entity_tags(sample.input_text, entities)

        format_response = await client.post(
            f"{stem_url.rstrip('/')}/dev/format-entities",
            json={"entity_tagged_text": tagged_text},
        )
        format_response.raise_for_status()
        format_payload = format_response.json()
        actual_output = str(format_payload.get("formatted_text", ""))
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        finish_reason = "error"

    completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
    latency_total_ms = (time.perf_counter() - start_time) * 1000.0
    return {
        "run_id": run_id,
        "model_id": BASELINE_MODEL_ID,
        "provider": BASELINE_PROVIDER,
        "sample_id": sample.sample_id,
        "base_prompt_hash": BASELINE_PROMPT_HASH,
        "formatting_prompt": sample.formatting_prompt,
        "input_text": sample.input_text,
        "expected_output": sample.expected_output,
        "actual_output": actual_output,
        "latency_total_ms": f"{latency_total_ms:.2f}",
        "latency_ttft_ms": "",
        "tokens_in": "",
        "tokens_out": "",
        "cost_usd": "0",
        "finish_reason": finish_reason,
        "error": error,
        "attempted_at": attempted_at,
        "completed_at": completed_at,
    }


def write_baseline_manifest(
    run_dir: Path,
    *,
    run_id: str,
    dataset_path: Path,
    limit: int | None,
    concurrency: int,
    impeller_url: str,
    stem_url: str,
) -> Path:
    manifest = {
        "run_id": run_id,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "dataset_checksum": dataset_checksum(dataset_path),
        "dataset_limit": limit,
        "base_prompt": "Impeller /v2/read entity detection + Stem /dev/format-entities",
        "base_prompt_hash": BASELINE_PROMPT_HASH,
        "sampling_defaults": {},
        "concurrency": concurrency,
        "parallel_models": 1,
        "models": [
            {
                "model_id": BASELINE_MODEL_ID,
                "provider": BASELINE_PROVIDER,
                "openrouter_slug": "",
                "temperature": None,
                "top_p": None,
                "max_tokens": None,
                "extra_body": {},
                "provider_routing": {},
                "supports_streaming": False,
                "notes": "Existing Deepgram smart-formatting pipeline baseline.",
            }
        ],
        "baseline": {
            "impeller_url": impeller_url,
            "stem_url": stem_url,
        },
    }
    path = run_dir / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


async def run_baseline(
    *,
    run_id: str,
    run_dir: Path,
    samples: list[Sample],
    concurrency: int,
    impeller_url: str,
    stem_url: str,
    timeout: float,
) -> BaselineStats:
    ensure_responses_header(run_dir)
    completed = load_completed(run_dir)
    todo = [
        sample
        for sample in samples
        if (BASELINE_MODEL_ID, sample.sample_id) not in completed
    ]
    stats = BaselineStats(total=len(samples), done=len(samples) - len(todo))
    if not todo:
        console.print(f"[green]{BASELINE_MODEL_ID}: all {len(samples)} samples already done.[/green]")
        return stats

    sem = asyncio.Semaphore(concurrency)
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

    async with httpx.AsyncClient(timeout=timeout) as client:
        with progress:
            task_id = progress.add_task(f"[cyan]{BASELINE_MODEL_ID}[/cyan]", total=len(todo))

            async def bounded(sample: Sample) -> None:
                async with sem:
                    row = await _format_one(
                        client,
                        impeller_url=impeller_url,
                        stem_url=stem_url,
                        sample=sample,
                        run_id=run_id,
                    )
                    if row["error"]:
                        stats.errors += 1
                    stats.done += 1
                    append_response(run_dir, row)
                    progress.update(
                        task_id,
                        advance=1,
                        description=f"[cyan]{BASELINE_MODEL_ID}[/cyan] err={stats.errors}",
                    )

            await asyncio.gather(*(bounded(sample) for sample in todo))

    return stats


def run_baseline_sync(
    *,
    dataset: Path,
    run_id_spec: str,
    results_root: Path,
    limit: int | None,
    concurrency: int,
    impeller_url: str,
    stem_url: str,
    timeout: float,
) -> Path:
    samples = load_samples(dataset, limit=limit)
    rid = make_run_id(run_id_spec)
    run_dir = results_root / rid
    run_dir.mkdir(parents=True, exist_ok=True)
    write_baseline_manifest(
        run_dir,
        run_id=rid,
        dataset_path=dataset,
        limit=limit,
        concurrency=concurrency,
        impeller_url=impeller_url,
        stem_url=stem_url,
    )
    console.print(
        f"Loaded [bold]{len(samples)}[/bold] samples from {dataset}; "
        f"running [bold]{BASELINE_MODEL_ID}[/bold]."
    )
    console.print(f"Run id: [bold]{rid}[/bold]")
    console.print(f"Run dir: [bold]{run_dir}[/bold]")
    stats = asyncio.run(
        run_baseline(
            run_id=rid,
            run_dir=run_dir,
            samples=samples,
            concurrency=concurrency,
            impeller_url=impeller_url,
            stem_url=stem_url,
            timeout=timeout,
        )
    )
    console.rule("[bold]Baseline complete[/bold]")
    console.print(f"Output: [bold]{run_dir / 'responses.csv'}[/bold]")
    console.print(f"Manifest: [bold]{run_dir / 'run_manifest.json'}[/bold]")
    console.print(f"Total rows attempted: {stats.done}/{stats.total}")
    console.print(f"Errors: [red]{stats.errors}[/red]")
    return run_dir
