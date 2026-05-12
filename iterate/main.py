"""Prompt-iteration loop for qwen3-32b-groq.

Workflow per invocation:

1. Read the system prompt from ``prompts/system_prompt.md`` (overrideable).
2. SHA-256 the prompt → 12-char hash. Skip if already in leaderboard
   (unless ``--force``).
3. Run qwen3-32b-groq via OpenRouter on a fixed stratified subset.
4. Score every row with the existing judge + EM + regex stack.
5. Append a one-line summary to ``leaderboard.csv``.
6. Print a diff against the previous best iteration.

To iterate: edit ``prompts/system_prompt.md`` → re-run this command.
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import hashlib
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from evaluator.aggregate import classify_disagreement
from evaluator.judge import JUDGE_MODEL_DEFAULT, JudgeClient
from evaluator.scorers import exact_match, regex_pass
from iterate.dataset import Sample, build_subset
from runner.models import MODEL_REGISTRY, ModelEntry
from runner.openrouter import OpenRouterClient

app = typer.Typer(
    name="iterate",
    help="Iterate on the smart-formatting system prompt against qwen3-32b-groq.",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()


DEFAULT_MODELS = "qwen3-32b-groq,gpt-oss-120b-groq"
DEFAULT_PROMPT_PATH = Path("prompts/system_prompt.md")
DEFAULT_DATASET = Path("synthetic_data.csv")
DEFAULT_OUT_ROOT = Path("iterate/results")

LEADERBOARD_FIELDS = [
    "iter_n",
    "timestamp",
    "prompt_hash",
    "model_id",
    "judge_model",
    "n_samples",
    "judge_pass",
    "judge_pass_pct",
    "exact_match_pct",
    "canonical_pass",
    "canonical_total",
    "catastrophic",
    "hallucination_any",
    "latency_p50_ms",
    "cost_runner_usd",
    "cost_judge_usd",
    "iter_dir",
]


# ----------------- prompt + hash -----------------


def read_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def hash_prompt(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


# ----------------- runner: one row at a time -----------------


def _build_messages(system_prompt: str, formatting_prompt: str, input_text: str) -> list[dict[str, str]]:
    """Compose chat messages with a custom system prompt (bypasses runner.prompts).

    Wraps the raw transcript in ``<transcript>...</transcript>`` tags so the
    system prompt can reference the spotlighting convention (per
    ``PROMPT_GUIDE.md`` recommendation #3 — Microsoft / PromptArmor pattern).
    """
    fp = (formatting_prompt or "").strip()
    if fp:
        system = f"{system_prompt}\n\nFormatting instructions:\n{fp}"
    else:
        system = system_prompt
    user = f"<transcript>\n{input_text}\n</transcript>"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


async def _run_samples(
    *,
    client: OpenRouterClient,
    entry: ModelEntry,
    samples: list[Sample],
    system_prompt: str,
    concurrency: int,
    progress: Progress,
    task_id: int,
) -> list[dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)
    results: list[dict[str, Any]] = [None] * len(samples)  # type: ignore[list-item]

    async def run_one(idx: int, s: Sample) -> None:
        async with sem:
            messages = _build_messages(system_prompt, s.formatting_prompt, s.input_text)
            attempted = dt.datetime.now(dt.timezone.utc).isoformat()
            try:
                res = await client.complete(entry, messages)
            except Exception as e:  # noqa: BLE001
                from runner.openrouter import CompletionResult
                res = CompletionResult(error=f"unhandled: {type(e).__name__}: {e}")
            completed = dt.datetime.now(dt.timezone.utc).isoformat()
            results[idx] = {
                "sample_id": s.sample_id,
                "entity_class": s.entity_class,
                "variant": s.variant,
                "source": s.source,
                "difficulty": s.difficulty,
                "formatting_prompt": s.formatting_prompt,
                "input_text": s.input_text,
                "expected_output": s.expected_output,
                "actual_output": res.actual_output or "",
                "latency_total_ms": res.latency_total_ms,
                "latency_ttft_ms": res.latency_ttft_ms,
                "tokens_in": res.tokens_in,
                "tokens_out": res.tokens_out,
                "cost_usd": res.cost_usd,
                "finish_reason": res.finish_reason or "",
                "error": res.error or "",
                "attempted_at": attempted,
                "completed_at": completed,
            }
            progress.update(task_id, advance=1)

    await asyncio.gather(*(run_one(i, s) for i, s in enumerate(samples)))
    return results


# ----------------- scoring: parallel judge -----------------


async def _score_rows(
    *,
    judge: JudgeClient,
    rows: list[dict[str, Any]],
    progress: Progress,
    task_id: int,
) -> list[dict[str, Any]]:
    sem = asyncio.Semaphore(judge.concurrency)
    out: list[dict[str, Any]] = [None] * len(rows)  # type: ignore[list-item]

    async def score_one(idx: int, row: dict[str, Any]) -> None:
        async with sem:
            actual = row["actual_output"]
            expected = row["expected_output"]
            entity_class = row["entity_class"]
            variant = row["variant"]
            fp = row["formatting_prompt"]
            input_text = row["input_text"]

            em = exact_match(actual, expected)
            rp, rc = regex_pass(actual, entity_class, fp)

            judge_accuracy = ""
            judge_accuracy_reason = ""
            judge_promptability = ""
            judge_promptability_reason = ""
            judge_catastrophic = ""
            judge_hallucination = ""
            judge_hallucination_reason = ""
            judge_error = ""

            if row["error"]:
                judge_accuracy = "other"
                judge_accuracy_reason = f"runner error: {row['error'][:120]}"
                judge_promptability = "n_a" if not fp else "ignored"
                judge_promptability_reason = "no candidate output"
                judge_catastrophic = "False"
                judge_hallucination = "none"
                judge_hallucination_reason = "no candidate output"
            else:
                try:
                    acc_task = judge.judge_accuracy(
                        formatting_prompt=fp,
                        input_text=input_text,
                        expected_output=expected,
                        actual_output=actual,
                        entity_class=entity_class,
                        variant=variant,
                    )
                    hal_task = judge.judge_hallucination(
                        input_text=input_text, actual_output=actual
                    )
                    acc, hal = await asyncio.gather(acc_task, hal_task)
                    judge_accuracy = acc.accuracy
                    judge_accuracy_reason = acc.accuracy_reason
                    judge_promptability = acc.promptability
                    judge_promptability_reason = acc.promptability_reason
                    judge_catastrophic = "True" if acc.catastrophic else "False"
                    judge_hallucination = hal.hallucination
                    judge_hallucination_reason = hal.hallucination_reason
                except Exception as e:  # noqa: BLE001
                    judge_error = f"{type(e).__name__}: {e}"

            methods_agree, dis_kind = classify_disagreement(em, rp, judge_accuracy)
            scored = dict(row)
            scored.update(
                {
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
                    "disagreement_kind": dis_kind,
                    "judge_error": judge_error,
                }
            )
            out[idx] = scored
            progress.update(task_id, advance=1)

    await asyncio.gather(*(score_one(i, r) for i, r in enumerate(rows)))
    return out


# ----------------- aggregation -----------------


def _percentile(values: list[float], pct: float) -> float | None:
    vs = [v for v in values if v is not None and not pd.isna(v)]
    if not vs:
        return None
    vs.sort()
    if len(vs) == 1:
        return vs[0]
    pos = (len(vs) - 1) * pct / 100.0
    import math

    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return vs[lo]
    frac = pos - lo
    return vs[lo] + (vs[hi] - vs[lo]) * frac


def _summarize(scored: list[dict[str, Any]], judge_cost: float) -> dict[str, Any]:
    n = len(scored)
    judge_pass = sum(1 for r in scored if r["judge_accuracy"] == "pass")
    em = sum(1 for r in scored if r["exact_match"] == "True")
    catastrophic = sum(1 for r in scored if r["judge_catastrophic"] == "True")
    halluc_any = sum(1 for r in scored if r["judge_hallucination"] not in ("none", ""))
    canonical = [r for r in scored if r["source"] == "customer_canonical"]
    canonical_pass = sum(1 for r in canonical if r["judge_accuracy"] == "pass")
    latencies = [
        float(r["latency_total_ms"]) for r in scored if r.get("latency_total_ms") not in (None, "")
    ]
    runner_cost = sum(
        float(r["cost_usd"]) for r in scored if r.get("cost_usd") not in (None, "")
    )
    return {
        "n_samples": n,
        "judge_pass": judge_pass,
        "judge_pass_pct": round(100.0 * judge_pass / n, 2) if n else 0.0,
        "exact_match_pct": round(100.0 * em / n, 2) if n else 0.0,
        "canonical_pass": canonical_pass,
        "canonical_total": len(canonical),
        "catastrophic": catastrophic,
        "hallucination_any": halluc_any,
        "latency_p50_ms": round(_percentile(latencies, 50) or 0.0, 1),
        "cost_runner_usd": round(runner_cost, 6),
        "cost_judge_usd": round(judge_cost, 6),
    }


# ----------------- leaderboard -----------------


def _read_leaderboard(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_leaderboard(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEADERBOARD_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LEADERBOARD_FIELDS})


def _append_leaderboard(path: Path, row: dict[str, Any]) -> None:
    existing = _read_leaderboard(path)
    existing.append(row)
    _write_leaderboard(path, existing)


# ----------------- per-iter output -----------------


def _next_iter_n(out_root: Path) -> int:
    if not out_root.exists():
        return 1
    nums = []
    for p in out_root.iterdir():
        if p.is_dir() and p.name.startswith("iter-"):
            try:
                nums.append(int(p.name.split("-")[1]))
            except (IndexError, ValueError):
                continue
    return (max(nums) + 1) if nums else 1


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})


# ----------------- diff vs prior best -----------------


def _print_multi_diff(
    *,
    summaries: dict[str, dict[str, Any]],
    results: list[tuple[str, list[dict[str, Any]], float]],
    leaderboard: list[dict[str, str]],
    judge_model: str,
) -> None:
    """Per-model diff vs prior best (matching judge_model + n_samples + model_id)."""
    table = Table(title="Iteration result", show_header=True, header_style="bold")
    table.add_column("metric")
    for model_id in summaries:
        table.add_column(f"{model_id}\nthis iter", justify="right")
        table.add_column(f"{model_id}\nbest", justify="right")
        table.add_column("Δ", justify="right")

    metric_keys = [
        ("judge_pass_pct", "%"),
        ("exact_match_pct", "%"),
        ("canonical_pass", ""),
        ("catastrophic", ""),
        ("hallucination_any", ""),
        ("latency_p50_ms", "ms"),
    ]

    bests: dict[str, dict[str, str]] = {}
    for model_id, summary in summaries.items():
        n_samples = summary["n_samples"]
        comparable = [
            r for r in leaderboard
            if r.get("judge_model") == judge_model
            and str(r.get("n_samples")) == str(n_samples)
            and r.get("model_id") == model_id
        ]
        if comparable:
            best = max(
                comparable,
                key=lambda r: (
                    float(r.get("judge_pass_pct") or 0.0),
                    int(r.get("canonical_pass") or 0),
                    -int(r.get("iter_n") or 0),
                ),
            )
            bests[model_id] = best
        else:
            bests[model_id] = {}

    def _delta(cur: float, prev: Any, suffix: str) -> str:
        if prev in (None, ""):
            return "—"
        try:
            d = cur - float(prev)
        except (TypeError, ValueError):
            return "—"
        sign = "+" if d > 0 else ""
        return f"{sign}{d:.2f}{suffix}"

    for key, suffix in metric_keys:
        row_cells: list[str] = [key]
        for model_id, summary in summaries.items():
            cur = summary[key] if key != "canonical_pass" else f"{summary['canonical_pass']}/{summary['canonical_total']}"
            best_val = bests[model_id].get(key, "")
            row_cells.append(f"{cur}{suffix}" if isinstance(cur, (int, float)) else str(cur))
            row_cells.append(
                f"{best_val}{suffix}" if best_val not in ("", None) and key != "canonical_pass"
                else (str(best_val) if best_val else "—")
            )
            if isinstance(summary[key] if key != "canonical_pass" else summary["canonical_pass"], (int, float)):
                cmp_cur = float(summary[key]) if key != "canonical_pass" else float(summary["canonical_pass"])
                row_cells.append(_delta(cmp_cur, best_val, suffix if key != "canonical_pass" else ""))
            else:
                row_cells.append("—")
        table.add_row(*row_cells)

    console.print(table)

    # Row-level diffs per model.
    scored_by_model = {mid: scored for mid, scored, _ in results}
    for model_id, scored in scored_by_model.items():
        prev_iter_dir = bests[model_id].get("iter_dir")
        if not prev_iter_dir:
            continue
        prev_scored = Path(prev_iter_dir) / model_id / "scored.csv"
        if not prev_scored.exists():
            # Backwards-compat: pre-multi-model iters had scored.csv at top level.
            prev_scored = Path(prev_iter_dir) / "scored.csv"
        if not prev_scored.exists():
            continue
        try:
            prev_df = pd.read_csv(prev_scored, dtype=str, keep_default_na=False)
        except Exception:  # noqa: BLE001
            continue
        cur_pass = {r["sample_id"]: r["judge_accuracy"] == "pass" for r in scored}
        prev_pass = {
            r["sample_id"]: r.get("judge_accuracy") == "pass" for _, r in prev_df.iterrows()
        }
        common = set(cur_pass) & set(prev_pass)
        newly_pass = sorted(s for s in common if cur_pass[s] and not prev_pass[s])
        newly_fail = sorted(s for s in common if not cur_pass[s] and prev_pass[s])
        if newly_pass:
            console.print(f"[green]{model_id}: +{len(newly_pass)} newly passing:[/green] {', '.join(newly_pass)}")
        if newly_fail:
            console.print(f"[red]{model_id}: -{len(newly_fail)} newly failing:[/red] {', '.join(newly_fail)}")
        if not newly_pass and not newly_fail:
            console.print(f"[dim]{model_id}: no row-level pass/fail changes vs best.[/dim]")


def _print_diff(
    *,
    summary: dict[str, Any],
    leaderboard: list[dict[str, str]],
    scored: list[dict[str, Any]],
    out_root: Path,
    judge_model: str,
) -> None:
    table = Table(title="Iteration result", show_header=True, header_style="bold")
    table.add_column("metric")
    table.add_column("this iter", justify="right")
    table.add_column("best so far", justify="right")
    table.add_column("Δ vs best", justify="right")

    # Only compare against prior iters with the same judge_model and subset size.
    # Switching judges or subset size invalidates score deltas.
    n_samples = summary["n_samples"]
    comparable = [
        r for r in leaderboard
        if r.get("judge_model") == judge_model
        and str(r.get("n_samples")) == str(n_samples)
    ]
    if comparable:
        def _key(r: dict[str, str]) -> tuple[float, int, int]:
            return (
                float(r.get("judge_pass_pct") or 0.0),
                int(r.get("canonical_pass") or 0),
                -int(r.get("iter_n") or 0),
            )

        best = max(comparable, key=_key)
    else:
        best = {}
        if leaderboard:
            console.print(
                f"[yellow]No comparable prior iters "
                f"(same judge_model={judge_model} and n_samples={n_samples}). "
                f"Showing standalone result.[/yellow]"
            )

    def fmt(v: Any, suffix: str = "") -> str:
        if v in (None, ""):
            return "—"
        return f"{v}{suffix}"

    def delta(cur: float, prev: Any, suffix: str = "") -> str:
        if prev in (None, ""):
            return "—"
        try:
            d = cur - float(prev)
        except (TypeError, ValueError):
            return "—"
        sign = "+" if d > 0 else ""
        return f"{sign}{d:.2f}{suffix}"

    rows = [
        ("judge_pass_pct", summary["judge_pass_pct"], best.get("judge_pass_pct"), "%"),
        ("exact_match_pct", summary["exact_match_pct"], best.get("exact_match_pct"), "%"),
        ("canonical_pass", f"{summary['canonical_pass']}/{summary['canonical_total']}", best.get("canonical_pass"), ""),
        ("catastrophic", summary["catastrophic"], best.get("catastrophic"), ""),
        ("hallucination_any", summary["hallucination_any"], best.get("hallucination_any"), ""),
        ("latency_p50_ms", summary["latency_p50_ms"], best.get("latency_p50_ms"), "ms"),
        ("cost_judge_usd", summary["cost_judge_usd"], best.get("cost_judge_usd"), ""),
    ]

    for name, cur, prev, suffix in rows:
        if isinstance(cur, (int, float)) and prev not in (None, ""):
            d = delta(float(cur), prev, suffix)
        else:
            d = "—"
        table.add_row(name, fmt(cur, suffix), fmt(prev, suffix), d)
    console.print(table)

    if not best.get("iter_dir"):
        return

    prev_dir = Path(best["iter_dir"])
    prev_scored_path = prev_dir / "scored.csv"
    if not prev_scored_path.exists():
        return
    try:
        prev_df = pd.read_csv(prev_scored_path, dtype=str, keep_default_na=False)
    except Exception:  # noqa: BLE001
        return

    cur_pass = {r["sample_id"]: r["judge_accuracy"] == "pass" for r in scored}
    prev_pass = {
        r["sample_id"]: r.get("judge_accuracy") == "pass"
        for _, r in prev_df.iterrows()
    }
    common = set(cur_pass) & set(prev_pass)
    newly_pass = sorted(s for s in common if cur_pass[s] and not prev_pass[s])
    newly_fail = sorted(s for s in common if not cur_pass[s] and prev_pass[s])

    if newly_pass:
        console.print(f"[green]+{len(newly_pass)} newly passing:[/green] {', '.join(newly_pass)}")
    if newly_fail:
        console.print(f"[red]-{len(newly_fail)} newly failing:[/red] {', '.join(newly_fail)}")
    if not newly_pass and not newly_fail:
        console.print("[dim]No row-level pass/fail changes vs best.[/dim]")


# ----------------- CLI -----------------


@app.command("run")
def run_cmd(
    prompt: Path = typer.Option(
        DEFAULT_PROMPT_PATH, "--prompt", help="System prompt file to evaluate."
    ),
    dataset: Path = typer.Option(
        DEFAULT_DATASET, "--dataset", help="Source dataset CSV."
    ),
    out_root: Path = typer.Option(
        DEFAULT_OUT_ROOT,
        "--out-root",
        help="Where iter-NNN-* dirs and leaderboard.csv land.",
    ),
    models: str = typer.Option(
        DEFAULT_MODELS,
        "--models",
        help="Comma-separated model registry keys; all run in parallel each iter.",
    ),
    judge_model: str = typer.Option(
        JUDGE_MODEL_DEFAULT, "--judge-model", help="Anthropic model id for the judge."
    ),
    n_per_class: int = typer.Option(
        3, "--n-per-class", help="Synthetic samples per non-canonical entity_class."
    ),
    n_adversarial: int = typer.Option(
        6, "--n-adversarial", help="Adversarial samples to draw."
    ),
    seed: int = typer.Option(
        42, "--seed", help="Seed for stratified sampling. Keep stable across iters."
    ),
    include_messy: bool = typer.Option(
        True,
        "--messy/--no-messy",
        help="Include the multi-entity rows parsed from messy_prompts.txt.",
    ),
    runner_concurrency: int = typer.Option(
        8, "--runner-concurrency", help="In-flight model calls per model."
    ),
    judge_concurrency: int = typer.Option(
        16, "--judge-concurrency", help="In-flight judge calls (shared across models)."
    ),
    force: bool = typer.Option(
        False, "--force", help="Re-evaluate even if this prompt hash already has an entry."
    ),
    note: Optional[str] = typer.Option(
        None, "--note", help="Free-form note saved to the iter dir as note.txt."
    ),
) -> None:
    """Run one iteration: load prompt, score every model in parallel, append per-model rows to leaderboard."""
    if not prompt.exists():
        console.print(f"[red]prompt file not found:[/red] {prompt}")
        raise typer.Exit(code=2)
    if not dataset.exists():
        console.print(f"[red]dataset not found:[/red] {dataset}")
        raise typer.Exit(code=2)
    model_ids = [m.strip() for m in models.split(",") if m.strip()]
    if not model_ids:
        console.print("[red]--models is empty.[/red]")
        raise typer.Exit(code=2)
    for mid in model_ids:
        if mid not in MODEL_REGISTRY:
            console.print(f"[red]model_id not in registry:[/red] {mid}")
            raise typer.Exit(code=2)
    if not os.environ.get("OPENROUTER_API_KEY"):
        console.print("[red]OPENROUTER_API_KEY is not set.[/red]")
        raise typer.Exit(code=2)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY is not set (needed for judge).[/red]")
        raise typer.Exit(code=2)

    prompt_text = read_prompt(prompt)
    p_hash = hash_prompt(prompt_text)

    leaderboard_path = out_root / "leaderboard.csv"
    leaderboard = _read_leaderboard(leaderboard_path)
    if not force:
        # Hash dedupe is per (prompt_hash, model_id). Skip iter only if EVERY
        # requested model already has a row for this hash.
        already_done: set[str] = {
            r.get("model_id", "") for r in leaderboard if r.get("prompt_hash") == p_hash
        }
        if all(mid in already_done for mid in model_ids):
            iters = sorted({int(r["iter_n"]) for r in leaderboard if r.get("prompt_hash") == p_hash})
            console.print(
                f"[yellow]prompt hash {p_hash} already evaluated for all requested "
                f"models (iters {iters}). Use --force to re-run.[/yellow]"
            )
            raise typer.Exit(code=0)
        # If only some models are missing, restrict to the missing ones.
        missing = [mid for mid in model_ids if mid not in already_done]
        if missing != model_ids:
            console.print(
                f"[cyan]prompt hash {p_hash} already evaluated for "
                f"{[m for m in model_ids if m in already_done]}; only running "
                f"{missing} this iter.[/cyan]"
            )
            model_ids = missing

    samples = build_subset(
        dataset,
        n_per_class=n_per_class,
        n_adversarial=n_adversarial,
        seed=seed,
        include_messy=include_messy,
    )
    iter_n = _next_iter_n(out_root)
    iter_dir = out_root / f"iter-{iter_n:03d}-{p_hash}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "prompt.txt").write_text(prompt_text, encoding="utf-8")
    if note:
        (iter_dir / "note.txt").write_text(note, encoding="utf-8")

    console.rule(f"[bold cyan]iter {iter_n} • {p_hash} • {', '.join(model_ids)}[/bold cyan]")
    console.print(
        f"prompt: {prompt}  ({len(prompt_text)} chars)\n"
        f"dataset: {dataset}  subset={len(samples)} rows  seed={seed}\n"
        f"out: {iter_dir}"
    )

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
    )

    async def _pipeline_for_model(
        client: OpenRouterClient,
        judge: JudgeClient,
        model_id: str,
    ) -> tuple[str, list[dict[str, Any]], float]:
        """Run + score one model end-to-end. Returns (model_id, scored, runner_cost)."""
        entry = MODEL_REGISTRY[model_id]
        run_task = progress.add_task(
            f"[cyan]{model_id}[/cyan] running", total=len(samples)
        )
        per_model_conc = int(entry.get("concurrency") or runner_concurrency)
        rows = await _run_samples(
            client=client,
            entry=entry,
            samples=samples,
            system_prompt=prompt_text,
            concurrency=per_model_conc,
            progress=progress,
            task_id=run_task,
        )
        model_dir = iter_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(model_dir / "responses.csv", rows)
        judge_task = progress.add_task(
            f"[magenta]{model_id}[/magenta] judging", total=len(rows)
        )
        scored = await _score_rows(
            judge=judge, rows=rows, progress=progress, task_id=judge_task
        )
        _write_csv(model_dir / "scored.csv", scored)
        runner_cost = sum(
            float(r["cost_usd"]) for r in scored if r.get("cost_usd") not in (None, "")
        )
        return model_id, scored, runner_cost

    async def _go() -> tuple[list[tuple[str, list[dict[str, Any]], float]], float]:
        client = OpenRouterClient.from_env()
        judge = JudgeClient(model=judge_model, concurrency=judge_concurrency)
        try:
            with progress:
                results = await asyncio.gather(
                    *(_pipeline_for_model(client, judge, mid) for mid in model_ids)
                )
            return results, judge.cost.total_usd
        finally:
            await client.aclose()
            await judge.aclose()

    t0 = time.time()
    results, total_judge_cost = asyncio.run(_go())
    wall = time.time() - t0

    # Distribute judge cost equally across models (each model used the same n_samples).
    per_model_judge_cost = total_judge_cost / max(1, len(results))

    summaries: dict[str, dict[str, Any]] = {}
    for model_id, scored, runner_cost in results:
        summary = _summarize(scored, per_model_judge_cost)
        summary["cost_runner_usd"] = round(runner_cost, 6)
        summaries[model_id] = summary
        lb_row = {
            "iter_n": iter_n,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "prompt_hash": p_hash,
            "model_id": model_id,
            "judge_model": judge_model,
            "iter_dir": str(iter_dir),
            **summary,
        }
        _append_leaderboard(leaderboard_path, lb_row)

    console.print(f"\n[bold]Done in {wall:.1f}s.[/bold]  total judge_cost=${total_judge_cost:.4f}")
    _print_multi_diff(
        summaries=summaries,
        results=results,
        leaderboard=leaderboard,
        judge_model=judge_model,
    )
    console.print(f"\n[green]Leaderboard:[/green] {leaderboard_path}")


@app.command("show")
def show_cmd(
    out_root: Path = typer.Option(DEFAULT_OUT_ROOT, "--out-root"),
    top: int = typer.Option(10, "--top", help="Show top N iterations by judge_pass_pct."),
    model: Optional[str] = typer.Option(
        None, "--model", help="Filter to a single model_id (default: show all)."
    ),
) -> None:
    """Print the current leaderboard sorted by judge_pass_pct desc."""
    lb = _read_leaderboard(out_root / "leaderboard.csv")
    if not lb:
        console.print("[yellow]no leaderboard yet.[/yellow]")
        return
    if model:
        lb = [r for r in lb if r.get("model_id") == model]
    lb.sort(
        key=lambda r: (
            float(r.get("judge_pass_pct") or 0.0),
            int(r.get("canonical_pass") or 0),
        ),
        reverse=True,
    )
    table = Table(show_header=True, header_style="bold")
    for col in ("iter_n", "model_id", "prompt_hash", "judge_pass_pct", "exact_match_pct",
                "canonical_pass", "catastrophic", "latency_p50_ms",
                "cost_runner_usd", "cost_judge_usd"):
        table.add_column(col)
    for r in lb[:top]:
        table.add_row(
            r.get("iter_n", ""),
            r.get("model_id", ""),
            r.get("prompt_hash", ""),
            r.get("judge_pass_pct", ""),
            r.get("exact_match_pct", ""),
            f"{r.get('canonical_pass','')}/{r.get('canonical_total','')}",
            r.get("catastrophic", ""),
            r.get("latency_p50_ms", ""),
            r.get("cost_runner_usd", ""),
            r.get("cost_judge_usd", ""),
        )
    console.print(table)


@app.command("failures")
def failures_cmd(
    iter_dir: Path = typer.Argument(..., help="Path to an iter-NNN-* dir."),
    model: Optional[str] = typer.Option(
        None, "--model",
        help="Model_id subdir (multi-model iters). Default: auto-detect single subdir, "
             "or fall back to top-level scored.csv (legacy single-model iters).",
    ),
    only_judge_fail: bool = typer.Option(
        True, "--only-judge-fail/--all", help="Only rows where judge_accuracy != 'pass'."
    ),
    limit: int = typer.Option(40, "--limit"),
) -> None:
    """Inspect per-row failures from a given iteration to guide the next prompt edit."""
    if model:
        scored_path = iter_dir / model / "scored.csv"
    else:
        # Auto-detect: prefer a single model-named subdir, else legacy top-level.
        subdirs = [p for p in iter_dir.iterdir() if p.is_dir() and (p / "scored.csv").exists()]
        if len(subdirs) == 1:
            scored_path = subdirs[0] / "scored.csv"
            console.print(f"[dim]auto-selected model: {subdirs[0].name}[/dim]")
        elif subdirs:
            console.print(
                f"[red]multiple model subdirs found:[/red] {[p.name for p in subdirs]}. "
                f"Pass --model <model_id> to disambiguate."
            )
            raise typer.Exit(code=2)
        else:
            scored_path = iter_dir / "scored.csv"
    if not scored_path.exists():
        console.print(f"[red]not found:[/red] {scored_path}")
        raise typer.Exit(code=2)
    df = pd.read_csv(scored_path, dtype=str, keep_default_na=False)
    if only_judge_fail:
        df = df[df["judge_accuracy"] != "pass"]
    df = df.head(limit)
    table = Table(show_header=True, header_style="bold", show_lines=True)
    for col in ("sample_id", "entity_class", "expected_output",
                "actual_output", "judge_accuracy", "judge_accuracy_reason"):
        table.add_column(col, overflow="fold", max_width=50)
    for _, r in df.iterrows():
        table.add_row(
            r["sample_id"],
            r.get("entity_class", ""),
            r["expected_output"],
            r["actual_output"],
            r["judge_accuracy"],
            r.get("judge_accuracy_reason", ""),
        )
    console.print(table)


# ----------------- Matrix (prompts × models) -----------------


MATRIX_LEADERBOARD_FIELDS = [
    "cell_id",
    "timestamp",
    "prompt_label",
    "prompt_hash",
    "model_id",
    "judge_model",
    "n_samples",
    "judge_pass",
    "judge_pass_pct",
    "exact_match_pct",
    "canonical_pass",
    "canonical_total",
    "catastrophic",
    "hallucination_any",
    "latency_total_p50_ms",
    "latency_total_p95_ms",
    "latency_ttft_p50_ms",
    "tokens_in_mean",
    "tokens_out_mean",
    "wall_seconds",
    "cost_runner_usd",
    "cost_judge_usd",
    "cell_dir",
]


@app.command("matrix")
def matrix_cmd(
    prompts: str = typer.Option(
        ...,
        "--prompts",
        help="Comma-separated prompt files (e.g. prompts/seed.md,iterate/results/iter-009-*/prompt.txt).",
    ),
    models: str = typer.Option(
        ...,
        "--models",
        help="Comma-separated model_ids from MODEL_REGISTRY.",
    ),
    out_root: Path = typer.Option(
        Path("iterate/results/matrix"),
        "--out-root",
        help="Where matrix-leaderboard.csv and per-cell dirs land.",
    ),
    judge_model: str = typer.Option(
        JUDGE_MODEL_DEFAULT, "--judge-model", help="Anthropic model id for the judge."
    ),
    dataset: Path = typer.Option(Path("synthetic_data.csv"), "--dataset"),
    n_per_class: int = typer.Option(3, "--n-per-class"),
    n_adversarial: int = typer.Option(6, "--n-adversarial"),
    seed: int = typer.Option(42, "--seed"),
    include_messy: bool = typer.Option(True, "--messy/--no-messy"),
    runner_concurrency: int = typer.Option(8, "--runner-concurrency"),
    judge_concurrency: int = typer.Option(16, "--judge-concurrency"),
    label_map: Optional[str] = typer.Option(
        None,
        "--labels",
        help="Optional comma-separated friendly labels for each prompt path "
             "(same order as --prompts). Default: filename stems.",
    ),
) -> None:
    """Run a prompts × models matrix. Each cell scored end-to-end; results to one CSV."""
    prompt_paths = [Path(p.strip()) for p in prompts.split(",") if p.strip()]
    model_ids = [m.strip() for m in models.split(",") if m.strip()]
    if not prompt_paths or not model_ids:
        console.print("[red]--prompts and --models are required.[/red]")
        raise typer.Exit(code=2)
    for pp in prompt_paths:
        if not pp.exists():
            console.print(f"[red]prompt file not found:[/red] {pp}")
            raise typer.Exit(code=2)
    for mid in model_ids:
        if mid not in MODEL_REGISTRY:
            console.print(f"[red]model not in registry:[/red] {mid}")
            raise typer.Exit(code=2)
    if not os.environ.get("OPENROUTER_API_KEY"):
        console.print("[red]OPENROUTER_API_KEY not set.[/red]")
        raise typer.Exit(code=2)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY not set.[/red]")
        raise typer.Exit(code=2)

    if label_map:
        labels = [s.strip() for s in label_map.split(",")]
        if len(labels) != len(prompt_paths):
            console.print("[red]--labels count must match --prompts count.[/red]")
            raise typer.Exit(code=2)
    else:
        labels = [pp.parent.name if pp.name == "prompt.txt" else pp.stem for pp in prompt_paths]

    samples = build_subset(
        dataset, n_per_class=n_per_class, n_adversarial=n_adversarial,
        seed=seed, include_messy=include_messy,
    )
    out_root.mkdir(parents=True, exist_ok=True)
    leaderboard_path = out_root / "matrix-leaderboard.csv"
    if not leaderboard_path.exists():
        with leaderboard_path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=MATRIX_LEADERBOARD_FIELDS).writeheader()

    n_cells = len(prompt_paths) * len(model_ids)
    console.rule(f"[bold cyan]matrix • {len(prompt_paths)} prompts × {len(model_ids)} models = {n_cells} cells[/bold cyan]")
    console.print(f"subset={len(samples)} rows  judge={judge_model}  out={out_root}\n")
    console.print(f"prompts: {[f'{lab}={pp}' for lab, pp in zip(labels, prompt_paths)]}")
    console.print(f"models:  {model_ids}\n")

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
    )

    async def _cell_pipeline(
        client: OpenRouterClient,
        judge: JudgeClient,
        prompt_text: str,
        prompt_label: str,
        prompt_hash: str,
        model_id: str,
    ) -> dict[str, Any]:
        cell_dir = out_root / prompt_label / model_id
        cell_dir.mkdir(parents=True, exist_ok=True)
        entry = MODEL_REGISTRY[model_id]
        run_task = progress.add_task(
            f"[cyan]{prompt_label}/{model_id}[/cyan] running", total=len(samples)
        )
        t0 = time.time()
        rows = await _run_samples(
            client=client, entry=entry, samples=samples,
            system_prompt=prompt_text, concurrency=runner_concurrency,
            progress=progress, task_id=run_task,
        )
        _write_csv(cell_dir / "responses.csv", rows)
        judge_task = progress.add_task(
            f"[magenta]{prompt_label}/{model_id}[/magenta] judging", total=len(rows)
        )
        scored = await _score_rows(
            judge=judge, rows=rows, progress=progress, task_id=judge_task
        )
        wall = time.time() - t0
        _write_csv(cell_dir / "scored.csv", scored)

        # Aggregate per-cell metrics, including latency + token + cost.
        n = len(scored)
        judge_pass = sum(1 for r in scored if r["judge_accuracy"] == "pass")
        em = sum(1 for r in scored if r["exact_match"] == "True")
        catastrophic = sum(1 for r in scored if r["judge_catastrophic"] == "True")
        halluc_any = sum(1 for r in scored if r["judge_hallucination"] not in ("none", ""))
        canonical = [r for r in scored if r["source"] == "customer_canonical"]
        canonical_pass = sum(1 for r in canonical if r["judge_accuracy"] == "pass")
        latencies = [
            float(r["latency_total_ms"]) for r in scored
            if r.get("latency_total_ms") not in (None, "")
        ]
        ttfts = [
            float(r["latency_ttft_ms"]) for r in scored
            if r.get("latency_ttft_ms") not in (None, "")
        ]
        toks_in = [int(r["tokens_in"]) for r in scored if r.get("tokens_in") not in (None, "")]
        toks_out = [int(r["tokens_out"]) for r in scored if r.get("tokens_out") not in (None, "")]
        runner_cost = sum(
            float(r["cost_usd"]) for r in scored if r.get("cost_usd") not in (None, "")
        )
        return {
            "cell_id": f"{prompt_label}/{model_id}",
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "prompt_label": prompt_label,
            "prompt_hash": prompt_hash,
            "model_id": model_id,
            "judge_model": judge_model,
            "n_samples": n,
            "judge_pass": judge_pass,
            "judge_pass_pct": round(100.0 * judge_pass / n, 2) if n else 0.0,
            "exact_match_pct": round(100.0 * em / n, 2) if n else 0.0,
            "canonical_pass": canonical_pass,
            "canonical_total": len(canonical),
            "catastrophic": catastrophic,
            "hallucination_any": halluc_any,
            "latency_total_p50_ms": round(_percentile(latencies, 50) or 0.0, 1),
            "latency_total_p95_ms": round(_percentile(latencies, 95) or 0.0, 1),
            "latency_ttft_p50_ms": round(_percentile(ttfts, 50) or 0.0, 1),
            "tokens_in_mean": round(sum(toks_in) / len(toks_in), 1) if toks_in else 0.0,
            "tokens_out_mean": round(sum(toks_out) / len(toks_out), 1) if toks_out else 0.0,
            "wall_seconds": round(wall, 1),
            "cost_runner_usd": round(runner_cost, 6),
            "cost_judge_usd": "",  # filled per-prompt batch (judge cost is shared)
            "cell_dir": str(cell_dir),
        }

    async def _go() -> list[dict[str, Any]]:
        client = OpenRouterClient.from_env()
        judge = JudgeClient(model=judge_model, concurrency=judge_concurrency)
        all_cells: list[dict[str, Any]] = []
        try:
            with progress:
                # One prompt at a time → all models in parallel for that prompt.
                # Lets us attribute judge cost per-prompt-batch.
                for label, ppath in zip(labels, prompt_paths):
                    prompt_text = read_prompt(ppath)
                    p_hash = hash_prompt(prompt_text)
                    # Snapshot the prompt next to its results.
                    (out_root / label).mkdir(parents=True, exist_ok=True)
                    (out_root / label / "prompt.txt").write_text(prompt_text, encoding="utf-8")

                    judge_cost_before = judge.cost.total_usd
                    cells = await asyncio.gather(*[
                        _cell_pipeline(client, judge, prompt_text, label, p_hash, mid)
                        for mid in model_ids
                    ])
                    judge_cost_for_prompt = judge.cost.total_usd - judge_cost_before
                    per_cell_judge = judge_cost_for_prompt / max(1, len(cells))
                    for cell in cells:
                        cell["cost_judge_usd"] = round(per_cell_judge, 6)
                    all_cells.extend(cells)

                    # Append rows for this prompt-batch immediately.
                    with leaderboard_path.open("a", newline="", encoding="utf-8") as f:
                        w = csv.DictWriter(f, fieldnames=MATRIX_LEADERBOARD_FIELDS)
                        for cell in cells:
                            w.writerow({k: cell.get(k, "") for k in MATRIX_LEADERBOARD_FIELDS})
        finally:
            await client.aclose()
            await judge.aclose()
        return all_cells

    t_start = time.time()
    cells = asyncio.run(_go())
    wall = time.time() - t_start
    total_cost = sum(float(c.get("cost_runner_usd") or 0) for c in cells) + sum(float(c.get("cost_judge_usd") or 0) for c in cells)
    console.print(f"\n[bold]Matrix done in {wall:.1f}s.[/bold]  total cost ≈ ${total_cost:.2f}")
    _print_matrix_heatmap(cells, labels, model_ids)
    console.print(f"\n[green]Leaderboard:[/green] {leaderboard_path}")


def _print_matrix_heatmap(
    cells: list[dict[str, Any]], labels: list[str], model_ids: list[str]
) -> None:
    """Render a prompts × models heatmap of judge_pass_pct."""
    by_cell = {(c["prompt_label"], c["model_id"]): c for c in cells}
    table = Table(title="judge_pass_pct (% of 80 rows)", show_header=True, header_style="bold")
    table.add_column("prompt")
    for mid in model_ids:
        table.add_column(mid, justify="right")
    table.add_column("row mean", justify="right")
    for lab in labels:
        row = [lab]
        vals: list[float] = []
        for mid in model_ids:
            c = by_cell.get((lab, mid))
            if c:
                v = float(c["judge_pass_pct"])
                vals.append(v)
                row.append(f"{v:.1f}")
            else:
                row.append("—")
        if vals:
            row.append(f"{sum(vals)/len(vals):.1f}")
        else:
            row.append("—")
        table.add_row(*row)
    # Column means
    col_means = ["[dim]col mean[/dim]"]
    overall: list[float] = []
    for mid in model_ids:
        col_vals = [float(by_cell[(lab, mid)]["judge_pass_pct"]) for lab in labels if (lab, mid) in by_cell]
        if col_vals:
            col_means.append(f"{sum(col_vals)/len(col_vals):.1f}")
            overall.extend(col_vals)
        else:
            col_means.append("—")
    col_means.append(f"{sum(overall)/len(overall):.1f}" if overall else "—")
    table.add_row(*col_means)
    console.print(table)

    # Latency p50 heatmap
    table2 = Table(title="latency_total p50 (ms)", show_header=True, header_style="bold")
    table2.add_column("prompt")
    for mid in model_ids:
        table2.add_column(mid, justify="right")
    for lab in labels:
        row = [lab]
        for mid in model_ids:
            c = by_cell.get((lab, mid))
            row.append(f"{c['latency_total_p50_ms']:.0f}" if c else "—")
        table2.add_row(*row)
    console.print(table2)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
