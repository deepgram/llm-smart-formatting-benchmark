"""CLI entrypoint for the benchmark runner."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from runner.baseline import run_baseline_sync
from runner.chained import run_chained_sync
from runner.models import MODEL_REGISTRY, resolve_models
from runner.prompts import BASE_PROMPT, base_prompt_hash
from runner.runner import (
    DetSample,
    dry_run_preview,
    load_samples,
    make_run_id,
    run_benchmark,
    run_determinism,
    summarize_determinism_run,
    summarize_run,
    write_determinism_manifest,
    write_manifest,
)


app = typer.Typer(
    name="runner",
    help="OpenRouter benchmark runner for ASR transcript formatting.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _require_api_key() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        console.print(
            "[bold red]OPENROUTER_API_KEY env var is not set.[/bold red] "
            "Export it before running a real benchmark."
        )
        raise typer.Exit(code=2)


def _resolve_run_dir(run_id: str, results_root: Path) -> Path:
    return results_root / run_id


@app.command("run")
def run_cmd(
    models: str = typer.Option(
        "all",
        "--models",
        help="'all' or comma-separated model_ids from MODEL_REGISTRY.",
    ),
    dataset: Path = typer.Option(
        Path("synthetic_data.csv"),
        "--dataset",
        help="Path to the synthetic-data CSV.",
    ),
    run_id: str = typer.Option(
        "auto", "--run-id", help="Run id, or 'auto' for an ISO8601 timestamp."
    ),
    results_root: Path = typer.Option(
        Path("results"), "--results-root", help="Root directory for run outputs."
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Cap the number of samples (useful for smoke tests)."
    ),
    concurrency: int = typer.Option(
        8, "--concurrency", help="Concurrent in-flight requests per model."
    ),
    parallel_models: int = typer.Option(
        1,
        "--parallel-models",
        help="How many models to run concurrently (default 1: sequential).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the first ~3 fully-rendered request payloads and exit. No API calls.",
    ),
) -> None:
    """Run the benchmark, or preview it with --dry-run."""
    if not dataset.exists():
        console.print(f"[red]Dataset not found:[/red] {dataset}")
        raise typer.Exit(code=2)
    try:
        model_entries = resolve_models(models)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2) from e

    samples = load_samples(dataset, limit=limit)
    console.print(
        f"Loaded [bold]{len(samples)}[/bold] samples from {dataset}; "
        f"[bold]{len(model_entries)}[/bold] models selected."
    )

    if dry_run:
        dry_run_preview(model_entries, samples, n=3)
        return

    _require_api_key()

    rid = make_run_id(run_id)
    run_dir = _resolve_run_dir(rid, results_root)
    run_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"Run id: [bold]{rid}[/bold]")
    console.print(f"Run dir: [bold]{run_dir}[/bold]")

    sampling_defaults = {"temperature": 0.0, "top_p": 1.0, "max_tokens": 1024}
    write_manifest(
        run_dir,
        run_id=rid,
        models=model_entries,
        sampling_defaults=sampling_defaults,
        dataset_path=dataset,
        base_prompt=BASE_PROMPT,
        parallel_models=parallel_models,
        concurrency=concurrency,
        limit=limit,
    )

    try:
        stats = asyncio.run(
            run_benchmark(
                run_id=rid,
                run_dir=run_dir,
                models=model_entries,
                samples=samples,
                concurrency=concurrency,
                parallel_models=parallel_models,
            )
        )
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted — partial results saved.[/yellow]")
        raise typer.Exit(code=130) from None
    summarize_run(run_dir, stats)


@app.command("baseline")
def baseline_cmd(
    dataset: Path = typer.Option(
        Path("synthetic_data.csv"),
        "--dataset",
        help="Path to the synthetic-data CSV.",
    ),
    run_id: str = typer.Option(
        "auto", "--run-id", help="Run id, or 'auto' for an ISO8601 timestamp."
    ),
    results_root: Path = typer.Option(
        Path("results"), "--results-root", help="Root directory for run outputs."
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Cap the number of samples (useful for smoke tests)."
    ),
    concurrency: int = typer.Option(
        8, "--concurrency", help="Concurrent in-flight pipeline requests."
    ),
    impeller_url: str = typer.Option(
        "http://localhost:8080/v2",
        "--impeller-url",
        help="Base URL for Impeller's v2 API.",
    ),
    stem_url: str = typer.Option(
        "http://localhost:8888/v1",
        "--stem-url",
        help="Base URL for Stem's v1 API.",
    ),
    timeout: float = typer.Option(
        60.0,
        "--timeout",
        help="Per-request timeout in seconds.",
    ),
) -> None:
    """Run the existing Impeller -> Stem formatting pipeline as a baseline."""
    if not dataset.exists():
        console.print(f"[red]Dataset not found:[/red] {dataset}")
        raise typer.Exit(code=2)
    try:
        run_baseline_sync(
            dataset=dataset,
            run_id_spec=run_id,
            results_root=results_root,
            limit=limit,
            concurrency=concurrency,
            impeller_url=impeller_url,
            stem_url=stem_url,
            timeout=timeout,
        )
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted — partial results saved.[/yellow]")
        raise typer.Exit(code=130) from None


@app.command("chained")
def chained_cmd(
    models: str = typer.Option(
        ...,
        "--models",
        help="Comma-separated model_ids to run after Impeller -> Stem.",
    ),
    prompt: Path = typer.Option(
        ...,
        "--prompt",
        help="System prompt file for the LLM stage.",
    ),
    dataset: Path = typer.Option(
        Path("synthetic_data.csv"),
        "--dataset",
        help="Path to the synthetic-data CSV.",
    ),
    run_id: str = typer.Option(
        "auto", "--run-id", help="Run id, or 'auto' for an ISO8601 timestamp."
    ),
    results_root: Path = typer.Option(
        Path("results"), "--results-root", help="Root directory for run outputs."
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Cap the number of samples (useful for smoke tests)."
    ),
    baseline_concurrency: int = typer.Option(
        8, "--baseline-concurrency", help="Concurrent Impeller -> Stem requests."
    ),
    llm_concurrency: int = typer.Option(
        8, "--llm-concurrency", help="Concurrent LLM requests."
    ),
    impeller_url: str = typer.Option(
        "http://localhost:8080/v2",
        "--impeller-url",
        help="Base URL for Impeller's v2 API.",
    ),
    stem_url: str = typer.Option(
        "http://localhost:8888/v1",
        "--stem-url",
        help="Base URL for Stem's v1 API.",
    ),
    timeout: float = typer.Option(
        60.0,
        "--timeout",
        help="Per-request timeout for the Impeller -> Stem stage.",
    ),
) -> None:
    """Run Impeller -> Stem first, then feed that output into selected LLMs."""
    if not dataset.exists():
        console.print(f"[red]Dataset not found:[/red] {dataset}")
        raise typer.Exit(code=2)
    if not prompt.exists():
        console.print(f"[red]Prompt not found:[/red] {prompt}")
        raise typer.Exit(code=2)
    try:
        model_entries = resolve_models(models)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2) from e
    unsupported = [
        m["model_id"] for m in model_entries if m.get("route", "openrouter") != "openrouter"
    ]
    if unsupported:
        console.print(
            "[red]Chained runner currently supports OpenRouter-routed models only:[/red] "
            + ", ".join(unsupported)
        )
        raise typer.Exit(code=2)
    _require_api_key()
    try:
        run_chained_sync(
            dataset=dataset,
            prompt=prompt,
            models=model_entries,
            run_id_spec=run_id,
            results_root=results_root,
            limit=limit,
            baseline_concurrency=baseline_concurrency,
            llm_concurrency=llm_concurrency,
            impeller_url=impeller_url,
            stem_url=stem_url,
            timeout=timeout,
        )
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted — partial results saved.[/yellow]")
        raise typer.Exit(code=130) from None


@app.command("resume")
def resume_cmd(
    run_id: str = typer.Argument(..., help="Existing run id under results/."),
    results_root: Path = typer.Option(Path("results"), "--results-root"),
    dataset: Optional[Path] = typer.Option(
        None,
        "--dataset",
        help="Override the dataset path; defaults to manifest's path.",
    ),
    concurrency: Optional[int] = typer.Option(None, "--concurrency"),
    parallel_models: Optional[int] = typer.Option(None, "--parallel-models"),
) -> None:
    """Resume a previously-started run by reading its manifest."""
    run_dir = _resolve_run_dir(run_id, results_root)
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        console.print(f"[red]No manifest at {manifest_path}[/red]")
        raise typer.Exit(code=2)
    manifest = json.loads(manifest_path.read_text())
    ds = dataset or Path(manifest["dataset_path"])
    if not ds.exists():
        console.print(f"[red]Dataset from manifest missing:[/red] {ds}")
        raise typer.Exit(code=2)

    # Re-hydrate model entries from MODEL_REGISTRY by model_id; fall back to
    # the manifest's recorded fields if a model has been removed locally.
    model_entries = []
    for m in manifest["models"]:
        if m["model_id"] in MODEL_REGISTRY:
            model_entries.append(MODEL_REGISTRY[m["model_id"]])
        else:
            console.print(
                f"[yellow]model_id {m['model_id']} not in MODEL_REGISTRY; "
                f"using manifest copy.[/yellow]"
            )
            model_entries.append(m)  # type: ignore[arg-type]

    samples = load_samples(ds, limit=manifest.get("dataset_limit"))
    _require_api_key()
    cc = concurrency if concurrency is not None else manifest.get("concurrency", 8)
    pm = (
        parallel_models
        if parallel_models is not None
        else manifest.get("parallel_models", 1)
    )
    try:
        stats = asyncio.run(
            run_benchmark(
                run_id=run_id,
                run_dir=run_dir,
                models=model_entries,
                samples=samples,
                concurrency=cc,
                parallel_models=pm,
            )
        )
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted — partial results saved.[/yellow]")
        raise typer.Exit(code=130) from None
    summarize_run(run_dir, stats)


@app.command("list-models")
def list_models_cmd() -> None:
    """Print the MODEL_REGISTRY keys + slugs."""
    console.print(f"[bold]{len(MODEL_REGISTRY)} models registered:[/bold]")
    for k, v in MODEL_REGISTRY.items():
        thinking = bool(v.get("extra_body"))
        routed = v.get("provider_routing") or {}
        routing = routed.get("order", "default") if routed else "default"
        console.print(
            f"  - [cyan]{k}[/cyan]  ->  {v['openrouter_slug']}  "
            f"(thinking={thinking}, routing={routing})"
        )


@app.command("show-prompt")
def show_prompt_cmd() -> None:
    """Print the base system prompt and its hash."""
    console.print(f"[bold]base_prompt_hash:[/bold] {base_prompt_hash()}")
    console.rule("[bold]BASE_PROMPT[/bold]")
    console.print(BASE_PROMPT)


@app.command("determinism")
def determinism_cmd(
    models: str = typer.Option(
        ...,
        "--models",
        help="Comma-separated model_ids from MODEL_REGISTRY.",
    ),
    prompt: Path = typer.Option(
        ...,
        "--prompt",
        help="System prompt file (e.g. iterate/results/iter-009-*/prompt.txt).",
    ),
    dataset: Path = typer.Option(
        Path("synthetic_data.csv"), "--dataset",
    ),
    subset: Optional[Path] = typer.Option(
        None,
        "--subset",
        help="CSV with `id` column listing the 50 sample_ids; if omitted, "
             "auto-derived (all canonical + spread across entity_class).",
    ),
    target_n: int = typer.Option(
        50, "--target-n", help="Subset size when auto-deriving (default 50)."
    ),
    trials: int = typer.Option(100, "--trials"),
    run_id: str = typer.Option(
        "auto", "--run-id", help="Run id, or 'auto' for an ISO8601 timestamp."
    ),
    results_root: Path = typer.Option(
        Path("results"), "--results-root",
    ),
    concurrency: int = typer.Option(
        16, "--concurrency", help="Concurrent in-flight requests per model."
    ),
    parallel_models: int = typer.Option(
        1, "--parallel-models",
    ),
    seed: int = typer.Option(42, "--seed", help="Subset selection seed."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print first 1 request payload and exit."
    ),
) -> None:
    """Run a determinism eval: same input × same prompt × N trials per model.

    Writes ``determinism_responses.csv`` with an extra ``trial`` column.
    Score with ``evaluator determinism --responses <run_dir>``.
    """
    if not prompt.exists():
        console.print(f"[red]prompt file not found:[/red] {prompt}")
        raise typer.Exit(code=2)
    if not dataset.exists():
        console.print(f"[red]dataset not found:[/red] {dataset}")
        raise typer.Exit(code=2)
    try:
        model_entries = resolve_models(models)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2) from e

    # Build subset.
    if subset is not None:
        if not subset.exists():
            console.print(f"[red]subset CSV not found:[/red] {subset}")
            raise typer.Exit(code=2)
        # Honor the --subset CSV: it must list at least an `id` column.
        import pandas as pd

        sub_df = pd.read_csv(subset, dtype=str, keep_default_na=False)
        if "id" not in sub_df.columns:
            console.print("[red]--subset CSV must have an `id` column.[/red]")
            raise typer.Exit(code=2)
        ds_df = pd.read_csv(dataset, dtype=str, keep_default_na=False)
        keep = set(sub_df["id"].tolist())
        ds_df = ds_df[ds_df["id"].isin(keep)]
        if ds_df.empty:
            console.print("[red]No matching rows for --subset ids.[/red]")
            raise typer.Exit(code=2)
        det_samples = [
            DetSample(
                sample_id=str(r["id"]),
                formatting_prompt=str(r.get("prompt", "") or ""),
                input_text=str(r.get("input_text", "") or ""),
                expected_output=str(r.get("expected_output", "") or ""),
            )
            for _, r in ds_df.iterrows()
        ]
    else:
        from iterate.dataset import build_determinism_subset

        full_subset = build_determinism_subset(dataset, target_n=target_n, seed=seed)
        det_samples = [
            DetSample(
                sample_id=s.sample_id,
                formatting_prompt=s.formatting_prompt,
                input_text=s.input_text,
                expected_output=s.expected_output,
            )
            for s in full_subset
        ]

    system_prompt = prompt.read_text(encoding="utf-8").strip()
    console.print(
        f"Determinism eval: [bold]{len(det_samples)}[/bold] samples × "
        f"[bold]{trials}[/bold] trials × [bold]{len(model_entries)}[/bold] models = "
        f"[bold]{len(det_samples) * trials * len(model_entries)}[/bold] calls."
    )

    if dry_run:
        # Print one rendered payload using the first model + first sample.
        from runner.openrouter import build_request_body

        head = model_entries[0]
        s = det_samples[0]
        fp = (s.formatting_prompt or "").strip()
        sys_msg = system_prompt if not fp else f"{system_prompt}\n\nFormatting instructions:\n{fp}"
        body = build_request_body(
            head,
            [{"role": "system", "content": sys_msg}, {"role": "user", "content": s.input_text}],
            stream=True,
        )
        console.print_json(data=body)
        return

    _require_api_key()

    rid = make_run_id(run_id)
    run_dir = _resolve_run_dir(rid, results_root)
    run_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"Run id: [bold]{rid}[/bold]")
    console.print(f"Run dir: [bold]{run_dir}[/bold]")

    sampling_defaults = {"temperature": 0.0, "top_p": 1.0, "max_tokens": 1024}
    write_determinism_manifest(
        run_dir,
        run_id=rid,
        models=model_entries,
        sampling_defaults=sampling_defaults,
        dataset_path=dataset,
        system_prompt=system_prompt,
        system_prompt_path=str(prompt),
        trials=trials,
        concurrency=concurrency,
        parallel_models=parallel_models,
        n_samples=len(det_samples),
    )

    try:
        stats = asyncio.run(
            run_determinism(
                run_id=rid,
                run_dir=run_dir,
                models=model_entries,
                samples=det_samples,
                trials=trials,
                system_prompt=system_prompt,
                concurrency=concurrency,
                parallel_models=parallel_models,
            )
        )
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted — partial results saved.[/yellow]")
        raise typer.Exit(code=130) from None
    summarize_determinism_run(run_dir, stats)


# Allow `python -m runner` and `runner` (via [project.scripts]) to both work,
# and default to the `run` command for the typer app when invoked bare with
# args.
def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
