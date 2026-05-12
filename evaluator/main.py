"""Typer CLI for the evaluator.

Reads a runner ``responses.csv``, applies four scoring methods, and writes
``scored.csv`` + ``summary.csv`` + ``canonical.csv`` + ``report.md`` next
to it.
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from evaluator.aggregate import (
    SCORE_COLUMNS,
    aggregate_canonical,
    aggregate_summary,
    classify_disagreement,
    load_metadata,
    scored_csv_columns,
    write_canonical_csv,
    write_summary_csv,
)
from evaluator.judge import JudgeClient, JUDGE_MODEL_DEFAULT
from evaluator.report import render_report, write_report
from evaluator.scorers import exact_match, regex_pass


app = typer.Typer(
    name="evaluator",
    help="Score runner responses for the smart-formatting benchmark.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command("version")
def version_cmd() -> None:
    """Print the evaluator version."""
    console.print("evaluator 0.1.0")


# ----------------- IO helpers -----------------


def _load_dataset(dataset_path: Path) -> pd.DataFrame:
    return pd.read_csv(dataset_path, dtype=str, keep_default_na=False)


def _load_responses(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df


def _load_existing_scored(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    if path.stat().st_size == 0:
        return None
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        str(row.get("run_id", "")),
        str(row.get("model_id", "")),
        str(row.get("sample_id", "")),
    )


def _resolve_responses_path(p: Path) -> Path:
    """Accept either the run dir or the responses.csv path itself."""
    if p.is_dir():
        return p / "responses.csv"
    return p


# ----------------- Per-row scoring -----------------


@dataclass
class _Row:
    """Mutable per-row record we accumulate scores into."""

    base: dict[str, str]
    scored: dict[str, str]


async def _score_one(
    judge: JudgeClient,
    row: _Row,
    dataset_lookup: dict[str, dict[str, str]],
) -> None:
    base = row.base
    sample_id = base.get("sample_id", "")
    actual = base.get("actual_output", "") or ""
    expected = base.get("expected_output", "") or ""
    formatting_prompt = base.get("formatting_prompt", "") or ""
    input_text = base.get("input_text", "") or ""

    meta = dataset_lookup.get(sample_id, {})
    entity_class = meta.get("entity_class", "")
    variant = meta.get("variant", "")

    # Method 1: exact match.
    em = exact_match(actual, expected)
    # Method 2: regex.
    rp, rc = regex_pass(actual, entity_class, formatting_prompt)

    # Methods 3 + 4: two independent judge calls, in parallel.
    error_msg = ""
    judge_accuracy = ""
    judge_accuracy_reason = ""
    judge_promptability = ""
    judge_promptability_reason = ""
    judge_catastrophic = ""
    judge_hallucination = ""
    judge_hallucination_reason = ""

    if base.get("error"):
        # Runner row already errored; skip judge calls.
        judge_accuracy = "other"
        judge_accuracy_reason = f"runner error: {base['error'][:120]}"
        judge_promptability = "n_a" if not formatting_prompt else "ignored"
        judge_promptability_reason = "no candidate output"
        judge_catastrophic = "False"
        judge_hallucination = "none"
        judge_hallucination_reason = "no candidate output"
    else:
        try:
            acc_task = judge.judge_accuracy(
                formatting_prompt=formatting_prompt,
                input_text=input_text,
                expected_output=expected,
                actual_output=actual,
                entity_class=entity_class,
                variant=variant,
            )
            hal_task = judge.judge_hallucination(
                input_text=input_text,
                actual_output=actual,
            )
            acc, hal = await asyncio.gather(acc_task, hal_task)
            judge_accuracy = acc.accuracy
            judge_accuracy_reason = acc.accuracy_reason
            judge_promptability = acc.promptability
            judge_promptability_reason = acc.promptability_reason
            judge_catastrophic = "True" if acc.catastrophic else "False"
            judge_hallucination = hal.hallucination
            judge_hallucination_reason = hal.hallucination_reason
        except Exception as e:  # capture for the row, do not crash whole run
            error_msg = f"{type(e).__name__}: {e}"

    methods_agree, disagreement_kind = classify_disagreement(em, rp, judge_accuracy)

    row.scored = {
        "exact_match": "True" if em else "False",
        "regex_pass": "" if rp is None else ("True" if rp else "False"),
        "regex_check_used": rc or "",
        "judge_accuracy": judge_accuracy,
        "judge_accuracy_reason": judge_accuracy_reason,
        "judge_promptability": judge_promptability,
        "judge_promptability_reason": judge_promptability_reason,
        "judge_catastrophic": judge_catastrophic,
        "judge_hallucination": judge_hallucination,
        "judge_hallucination_reason": judge_hallucination_reason,
        "methods_agree": "True" if methods_agree else "False",
        "disagreement_kind": disagreement_kind,
        "judge_error": error_msg,
    }


# ----------------- Append-as-you-go scored.csv writer -----------------


class _ScoredWriter:
    def __init__(self, path: Path, columns: list[str]) -> None:
        self.path = path
        self.columns = columns
        self._lock = asyncio.Lock()
        if not path.exists() or path.stat().st_size == 0:
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()

    async def write(self, base: dict[str, str], scored: dict[str, str]) -> None:
        merged: dict[str, str] = {c: "" for c in self.columns}
        for k, v in base.items():
            if k in merged:
                merged[k] = "" if v is None else str(v)
        for k, v in scored.items():
            if k in merged:
                merged[k] = "" if v is None else str(v)
        async with self._lock:
            with self.path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writerow(merged)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass


# ----------------- Score command -----------------


@app.command("score")
def score_cmd(
    responses: Path = typer.Option(
        ...,
        "--responses",
        help="Path to responses.csv (or the containing run dir).",
    ),
    dataset: Path = typer.Option(
        Path("synthetic_data.csv"),
        "--dataset",
        help="Path to the synthetic dataset (for entity_class / variant lookups).",
    ),
    judge_model: str = typer.Option(
        JUDGE_MODEL_DEFAULT,
        "--judge-model",
        help="Anthropic model id to use for the judge (e.g. claude-opus-4-7).",
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Cap the number of response rows to score (smoke tests)."
    ),
    models: Optional[str] = typer.Option(
        None,
        "--models",
        help="Comma-separated model_ids to filter on (default: score all).",
    ),
    concurrency: int = typer.Option(
        8, "--concurrency", help="Concurrent in-flight judge calls."
    ),
    metadata: Path = typer.Option(
        Path("models_metadata.csv"),
        "--metadata",
        help="Path to models_metadata.csv (vendor / params / license / release_date). "
             "Joined onto results for grouped reporting.",
    ),
) -> None:
    """Run all four scoring methods on a responses.csv and emit reports."""
    responses_path = _resolve_responses_path(responses)
    if not responses_path.exists():
        console.print(f"[red]responses.csv not found:[/red] {responses_path}")
        raise typer.Exit(code=2)
    if not dataset.exists():
        console.print(f"[red]dataset not found:[/red] {dataset}")
        raise typer.Exit(code=2)

    run_dir = responses_path.parent
    scored_path = run_dir / "scored.csv"
    summary_path = run_dir / "summary.csv"
    canonical_path = run_dir / "canonical.csv"
    report_path = run_dir / "report.md"
    metadata_path: Path | None = metadata if metadata.exists() else None
    if metadata_path is None:
        console.print(
            f"[yellow]models_metadata.csv not found at {metadata}; "
            f"reports will skip metadata-grouped sections.[/yellow]"
        )

    df_resp = _load_responses(responses_path)
    df_data = _load_dataset(dataset)
    dataset_lookup = {
        row["id"]: dict(row) for _, row in df_data.iterrows()
    }
    if models:
        wanted = {m.strip() for m in models.split(",") if m.strip()}
        df_resp = df_resp[df_resp["model_id"].isin(wanted)]
    if limit is not None:
        df_resp = df_resp.head(limit)

    columns = scored_csv_columns(df_resp.columns.tolist())
    existing = _load_existing_scored(scored_path)
    already: set[tuple[str, str, str]] = set()
    if existing is not None:
        for _, r in existing.iterrows():
            already.add((str(r.get("run_id", "")), str(r.get("model_id", "")), str(r.get("sample_id", ""))))
        console.print(
            f"[cyan]Resuming:[/cyan] {len(already)} rows already in scored.csv"
        )

    todo_records: list[dict[str, str]] = []
    for _, r in df_resp.iterrows():
        rec = {c: ("" if pd.isna(r.get(c)) else str(r.get(c))) for c in df_resp.columns}
        if (rec.get("run_id", ""), rec.get("model_id", ""), rec.get("sample_id", "")) in already:
            continue
        todo_records.append(rec)

    console.print(
        f"Scoring [bold]{len(todo_records)}[/bold] response rows "
        f"({len(df_resp)} total, {len(already)} already done) "
        f"with judge=[bold]{judge_model}[/bold] concurrency={concurrency}"
    )

    if not todo_records:
        console.print("[green]All rows already scored — emitting reports only.[/green]")
        _emit_reports(
            scored_path=scored_path,
            summary_path=summary_path,
            canonical_path=canonical_path,
            report_path=report_path,
            run_id=_run_id_from_dir(run_dir),
            judge_model=judge_model,
            judge_cost_usd=0.0,
            df_data=df_data,
            metadata_path=metadata_path,
        )
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY is not set.[/red]")
        raise typer.Exit(code=2)

    judge = JudgeClient(model=judge_model, concurrency=concurrency)
    writer = _ScoredWriter(scored_path, columns)
    asyncio.run(
        _run_all(
            judge=judge,
            todo=todo_records,
            dataset_lookup=dataset_lookup,
            writer=writer,
        )
    )

    cost_summary = judge.cost.summary()
    console.print(
        f"Judge calls: {cost_summary['calls']}  errors: {cost_summary['errors']}  "
        f"cost: [bold]${cost_summary['total_usd']:.4f}[/bold]"
    )
    console.print(
        f"Cache: writes={cost_summary['cache_creation_input_tokens']} "
        f"reads={cost_summary['cache_read_input_tokens']}"
    )

    _emit_reports(
        scored_path=scored_path,
        summary_path=summary_path,
        canonical_path=canonical_path,
        report_path=report_path,
        run_id=_run_id_from_dir(run_dir),
        judge_model=judge_model,
        judge_cost_usd=cost_summary["total_usd"],
        df_data=df_data,
        metadata_path=metadata_path,
    )


def _run_id_from_dir(run_dir: Path) -> str:
    return run_dir.name


async def _run_all(
    *,
    judge: JudgeClient,
    todo: list[dict[str, str]],
    dataset_lookup: dict[str, dict[str, str]],
    writer: _ScoredWriter,
) -> None:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
    )
    task_id = None
    sem_done = 0
    try:
        with progress:
            task_id = progress.add_task("[cyan]judging[/cyan]", total=len(todo))

            async def worker(rec: dict[str, str]) -> None:
                nonlocal sem_done
                row = _Row(base=rec, scored={})
                await _score_one(judge, row, dataset_lookup)
                await writer.write(row.base, row.scored)
                sem_done += 1
                progress.update(
                    task_id,
                    advance=1,
                    description=(
                        f"[cyan]judging[/cyan] "
                        f"calls={judge.cost.calls} err={judge.cost.errors} "
                        f"${judge.cost.total_usd:.3f}"
                    ),
                )

            await asyncio.gather(*(worker(r) for r in todo))
    finally:
        await judge.aclose()


# ----------------- Emit reports from scored.csv on disk -----------------


def _emit_reports(
    *,
    scored_path: Path,
    summary_path: Path,
    canonical_path: Path,
    report_path: Path,
    run_id: str,
    judge_model: str,
    judge_cost_usd: float,
    df_data: pd.DataFrame,
    metadata_path: Path | None = None,
) -> None:
    df_scored = pd.read_csv(scored_path, dtype=str, keep_default_na=False)
    # Cast numeric columns we use for percentiles.
    if "latency_total_ms" in df_scored.columns:
        df_scored["latency_total_ms"] = pd.to_numeric(
            df_scored["latency_total_ms"], errors="coerce"
        )
    if "latency_ttft_ms" in df_scored.columns:
        df_scored["latency_ttft_ms"] = pd.to_numeric(
            df_scored["latency_ttft_ms"], errors="coerce"
        )
    if "cost_usd" in df_scored.columns:
        df_scored["cost_usd"] = pd.to_numeric(df_scored["cost_usd"], errors="coerce")

    # Merge entity_class for per-class table & convenience.
    df_scored = df_scored.merge(
        df_data[["id", "entity_class"]],
        left_on="sample_id",
        right_on="id",
        how="left",
    )

    summary = aggregate_summary(df_scored)
    canonical = aggregate_canonical(df_scored)
    metadata_df = load_metadata(metadata_path)
    # Persist enriched summary so summary.csv carries vendor/params/license too.
    if not metadata_df.empty:
        from evaluator.aggregate import enrich_summary
        enriched = enrich_summary(summary, metadata_df)
        write_summary_csv(enriched, summary_path)
    else:
        write_summary_csv(summary, summary_path)
    write_canonical_csv(canonical, canonical_path)
    body = render_report(
        run_id=run_id,
        summary=summary,
        canonical=canonical,
        scored=df_scored,
        dataset_df=df_data,
        judge_model=judge_model,
        judge_cost_usd=judge_cost_usd,
        metadata=metadata_df if not metadata_df.empty else None,
    )
    write_report(report_path, body)
    console.print(f"[green]Wrote[/green] {summary_path}")
    console.print(f"[green]Wrote[/green] {canonical_path}")
    console.print(f"[green]Wrote[/green] {report_path}")


# ============================================================
# Determinism subcommand
# ============================================================


def _normalize_for_dedup(s: str) -> str:
    """Conservative normalization: strip leading/trailing whitespace only.

    Anything more (lowercasing, punctuation collapse, whitespace folding) would
    mask real determinism failures, since this benchmark cares about byte-for-byte
    stability of the output.
    """
    return (s or "").strip()


@app.command("determinism")
def determinism_cmd(
    responses: Path = typer.Option(
        ...,
        "--responses",
        help="Path to determinism_responses.csv (or its containing run dir).",
    ),
    out_dir: Optional[Path] = typer.Option(
        None,
        "--out-dir",
        help="Where to write determinism_summary.csv + determinism_per_sample.csv. "
             "Defaults to the directory containing the responses CSV.",
    ),
) -> None:
    """Score a determinism run.

    Groups by (model_id, sample_id) and computes:
      - all_identical:      True iff all trials produce byte-identical output
                            (after stripping leading/trailing whitespace).
      - p99_edit_distance:  p99 character-level edit distance across the
                            C(n_trials, 2) pairs of trials in this group.

    Writes determinism_per_sample.csv (one row per group) and
    determinism_summary.csv (one row per model_id with rolled-up metrics).
    No LLM judge.
    """
    from itertools import combinations

    import numpy as np
    from rapidfuzz.distance import Levenshtein  # type: ignore[import-untyped]

    # Resolve path: accept either the CSV or the run dir.
    if responses.is_dir():
        det_path = responses / "determinism_responses.csv"
    else:
        det_path = responses
    if not det_path.exists():
        console.print(f"[red]determinism_responses.csv not found:[/red] {det_path}")
        raise typer.Exit(code=2)

    out_root = out_dir if out_dir is not None else det_path.parent
    out_root.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(det_path, dtype=str, keep_default_na=False)
    required = {"model_id", "sample_id", "trial", "actual_output"}
    missing = required - set(df.columns)
    if missing:
        console.print(f"[red]missing columns:[/red] {missing}")
        raise typer.Exit(code=2)

    df["actual_output"] = df["actual_output"].fillna("")
    df["normalized_output"] = df["actual_output"].map(_normalize_for_dedup)
    df["error"] = df.get("error", "").fillna("")

    per_sample_rows: list[dict[str, Any]] = []
    by_model_distances: dict[str, list[int]] = {}

    grouped = df.groupby(["model_id", "sample_id"], sort=False)
    for (model_id, sample_id), grp in grouped:
        outputs = grp["normalized_output"].tolist()
        errors = (grp["error"] != "").sum()
        n_trials = len(outputs)
        unique = list(dict.fromkeys(outputs))  # preserve insertion order
        all_identical = len(unique) == 1 and errors == 0

        # Pairwise edit distances. With n_trials=100 → 4950 pairs per group.
        # Optimization: distance only depends on the unique strings + their
        # multiplicities, so use unique outputs and weight pairs accordingly.
        if all_identical:
            pair_distances: list[int] = []  # all zeros, no need to materialize
            p50 = p95 = p99 = mx = 0
            unique_count = 1
        else:
            counts = grp["normalized_output"].value_counts().to_dict()
            uniq = list(counts.keys())
            unique_count = len(uniq)
            # Compute distance once per unique-pair, weight by count_i*count_j.
            uniq_distances: dict[tuple[int, int], int] = {}
            for i, j in combinations(range(len(uniq)), 2):
                d = Levenshtein.distance(uniq[i], uniq[j])
                uniq_distances[(i, j)] = d
            # Expand to a flat list of pair distances (with appropriate weights),
            # also include zero-distances for same-unique pairs.
            flat: list[int] = []
            for i, j in combinations(range(len(uniq)), 2):
                w = counts[uniq[i]] * counts[uniq[j]]
                flat.extend([uniq_distances[(i, j)]] * w)
            for u in uniq:
                c = counts[u]
                if c >= 2:
                    flat.extend([0] * (c * (c - 1) // 2))
            pair_distances = flat
            arr = np.asarray(pair_distances, dtype=np.int64)
            p50 = int(np.percentile(arr, 50))
            p95 = int(np.percentile(arr, 95))
            p99 = int(np.percentile(arr, 99))
            mx = int(arr.max())

        by_model_distances.setdefault(model_id, []).extend(pair_distances)

        per_sample_rows.append(
            {
                "model_id": model_id,
                "sample_id": sample_id,
                "n_trials": n_trials,
                "errors": int(errors),
                "unique_outputs": unique_count,
                "all_identical": "True" if all_identical else "False",
                "edit_distance_p50": p50,
                "edit_distance_p95": p95,
                "edit_distance_p99": p99,
                "edit_distance_max": mx,
                # Helpful for spot-checks:
                "first_output": unique[0] if unique else "",
                "second_output": unique[1] if len(unique) > 1 else "",
            }
        )

    per_sample_df = pd.DataFrame(per_sample_rows).sort_values(["model_id", "sample_id"])
    per_sample_path = out_root / "determinism_per_sample.csv"
    per_sample_df.to_csv(per_sample_path, index=False)

    # Per-model summary.
    summary_rows: list[dict[str, Any]] = []
    for model_id, sub in per_sample_df.groupby("model_id", sort=False):
        n_groups = len(sub)
        all_id = (sub["all_identical"] == "True").sum()
        pct_identical = round(100.0 * all_id / n_groups, 2) if n_groups else 0.0
        flat_dists = by_model_distances.get(model_id, [])
        if flat_dists:
            arr = np.asarray(flat_dists, dtype=np.int64)
            p50 = int(np.percentile(arr, 50))
            p95 = int(np.percentile(arr, 95))
            p99 = int(np.percentile(arr, 99))
            mx = int(arr.max())
            mean = float(np.mean(arr))
        else:
            p50 = p95 = p99 = mx = 0
            mean = 0.0
        summary_rows.append(
            {
                "model_id": model_id,
                "n_samples": n_groups,
                "n_samples_all_identical": int(all_id),
                "pct_samples_all_identical": pct_identical,
                "edit_distance_p50": p50,
                "edit_distance_p95": p95,
                "edit_distance_p99": p99,
                "edit_distance_max": mx,
                "edit_distance_mean": round(mean, 2),
                "total_pair_count": len(flat_dists),
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values(
        "pct_samples_all_identical", ascending=False
    )
    summary_path = out_root / "determinism_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    # Console output.
    console.rule("[bold]Determinism summary[/bold]")
    table = Table(show_header=True, header_style="bold")
    for col in (
        "model_id", "n_samples", "all_identical", "%_identical",
        "p50", "p95", "p99", "max", "mean",
    ):
        table.add_column(col, justify="right" if col != "model_id" else "left")
    for _, r in summary_df.iterrows():
        table.add_row(
            str(r["model_id"]),
            str(r["n_samples"]),
            f"{r['n_samples_all_identical']}",
            f"{r['pct_samples_all_identical']}%",
            str(r["edit_distance_p50"]),
            str(r["edit_distance_p95"]),
            str(r["edit_distance_p99"]),
            str(r["edit_distance_max"]),
            f"{r['edit_distance_mean']:.2f}",
        )
    console.print(table)
    console.print(f"\n[green]Wrote[/green] {summary_path}")
    console.print(f"[green]Wrote[/green] {per_sample_path}")


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
