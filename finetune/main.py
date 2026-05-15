"""CLI for the Together.ai fine-tune + eval pipeline.

Subcommands:
  split     Build train.jsonl / eval.jsonl / eval.csv from synthetic_data.csv.
  upload    Upload train.jsonl to Together and print the file id.
  train     Kick off a LoRA fine-tune (writes job_info.json).
  status    Poll a fine-tune job by job_id (or read from job_info.json).
  infer     Run the fine-tuned model over eval.csv → results/<run_id>/responses.csv.
  score     Shell out to the parent ``evaluator score`` on the run dir.
  all       split → upload → train → wait → infer → score (one shot).

Defaults are tuned for the smallest practical base model:
  --base-model meta-llama/Llama-3.2-3B-Instruct  (LoRA)

Env required:
  TOGETHER_API_KEY  for upload/train/status/infer/all
  ANTHROPIC_API_KEY for score (the judge model in the parent evaluator)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from finetune.dataset import (
    DEFAULT_DATASET,
    DEFAULT_MESSY,
    DEFAULT_OUT,
    Row,
    class_counts,
    load_corpus,
    split_train_eval,
    write_eval_csv,
    write_jsonl,
)
from finetune.infer import InferConfig, run_inference_sync
from finetune.prompts import prompt_hash


app = typer.Typer(
    name="finetune",
    help="Fine-tune small models on Together.ai for transcript formatting.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results"
DEFAULT_BASE_MODEL = "meta-llama/Llama-3.2-3B-Instruct"


def _load_dotenv() -> None:
    """Best-effort load of TOGETHER_API_KEY from .env files. No dependency.
    Order: repo .env, then finetune/.env (more specific wins). Existing env
    vars are preserved (never overwritten)."""
    candidates = [REPO_ROOT / ".env", Path(__file__).resolve().parent / ".env"]
    for p in candidates:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("\"'")
            if k and k not in os.environ:
                os.environ[k] = v


_load_dotenv()


# ----------------- helpers -----------------


def _read_rows_from_eval_csv(eval_csv: Path) -> list[Row]:
    """Load the eval.csv we wrote, returning Row objects for the inference loop."""
    import csv

    out: list[Row] = []
    with eval_csv.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(
                Row(
                    sample_id=r["id"],
                    entity_class=r.get("entity_class", ""),
                    variant=r.get("variant", ""),
                    formatting_prompt=r.get("prompt", ""),
                    input_text=r.get("input_text", ""),
                    expected_output=r.get("expected_output", ""),
                    source=r.get("source", ""),
                    difficulty=r.get("difficulty", ""),
                    domain=r.get("domain", ""),
                )
            )
    return out


def _job_info_path(out_dir: Path) -> Path:
    return out_dir / "job_info.json"


def _load_job_info(out_dir: Path) -> dict:
    p = _job_info_path(out_dir)
    if not p.exists():
        raise typer.BadParameter(
            f"No job_info.json at {p}. Run `finetune train` first or pass --job-id."
        )
    return json.loads(p.read_text())


def _save_job_info(out_dir: Path, info: dict) -> None:
    p = _job_info_path(out_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(info, indent=2, sort_keys=True))


# ----------------- split -----------------


@app.command("split")
def split_cmd(
    dataset: Path = typer.Option(DEFAULT_DATASET, "--dataset"),
    messy: Path = typer.Option(DEFAULT_MESSY, "--messy"),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    eval_frac: float = typer.Option(0.20, "--eval-frac"),
    seed: int = typer.Option(42, "--seed"),
) -> None:
    """Build train.jsonl + eval.jsonl + eval.csv. Idempotent."""
    rows = load_corpus(dataset=dataset, messy=messy)
    train, eval_ = split_train_eval(rows, eval_frac=eval_frac, seed=seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "train.jsonl"
    eval_jsonl = out_dir / "eval.jsonl"
    eval_csv = out_dir / "eval.csv"

    write_jsonl(train, train_path, with_assistant=True)
    write_jsonl(eval_, eval_jsonl, with_assistant=True)
    write_eval_csv(eval_, eval_csv)

    # Summary
    t = Table(title="Split summary")
    t.add_column("split"); t.add_column("rows", justify="right"); t.add_column("canonical", justify="right")
    t.add_row("train", str(len(train)), str(sum(1 for r in train if r.source == "customer_canonical")))
    t.add_row("eval",  str(len(eval_)), str(sum(1 for r in eval_  if r.source == "customer_canonical")))
    console.print(t)

    console.print(f"[green]Wrote[/green] {train_path}  ({len(train)} rows)")
    console.print(f"[green]Wrote[/green] {eval_jsonl}  ({len(eval_)} rows)")
    console.print(f"[green]Wrote[/green] {eval_csv}    ({len(eval_)} rows, parent-runner schema)")

    # Per-class counts for sanity.
    ct = Table(title="entity_class distribution")
    ct.add_column("class"); ct.add_column("train", justify="right"); ct.add_column("eval", justify="right")
    tc, ec = class_counts(train), class_counts(eval_)
    for cls in sorted(set(tc) | set(ec)):
        ct.add_row(cls, str(tc.get(cls, 0)), str(ec.get(cls, 0)))
    console.print(ct)


# ----------------- upload -----------------


@app.command("upload")
def upload_cmd(
    file: Path = typer.Option(DEFAULT_OUT / "train.jsonl", "--file"),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
) -> None:
    """Upload train.jsonl to Together; cache the file_id in upload.json."""
    from finetune.together_client import upload_training_file

    if not file.exists():
        raise typer.BadParameter(f"{file} does not exist — run `finetune split` first.")

    console.print(f"Uploading {file} to Together…")
    res = upload_training_file(str(file))
    info = {"file_id": res.file_id, "filename": res.filename, "bytes": res.bytes}
    (out_dir / "upload.json").write_text(json.dumps(info, indent=2))
    console.print(f"[green]file_id:[/green] {res.file_id}")


# ----------------- train -----------------


@app.command("train")
def train_cmd(
    base_model: str = typer.Option(DEFAULT_BASE_MODEL, "--base-model"),
    suffix: str = typer.Option("smart-fmt", "--suffix"),
    file_id: Optional[str] = typer.Option(None, "--file-id", help="Skip upload, use this file id."),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    n_epochs: int = typer.Option(3, "--n-epochs"),
    learning_rate: float = typer.Option(1e-4, "--learning-rate"),
    n_checkpoints: int = typer.Option(1, "--n-checkpoints"),
    warmup_ratio: float = typer.Option(0.03, "--warmup-ratio"),
) -> None:
    """Create a LoRA fine-tune. Writes job_info.json with the job_id."""
    from finetune.together_client import create_lora_finetune

    if file_id is None:
        up = out_dir / "upload.json"
        if not up.exists():
            raise typer.BadParameter("No --file-id and no upload.json; run `finetune upload` first.")
        file_id = json.loads(up.read_text())["file_id"]

    console.print(f"Creating LoRA fine-tune: base={base_model}, suffix={suffix}, file_id={file_id}")
    res = create_lora_finetune(
        training_file_id=file_id,
        base_model=base_model,
        suffix=suffix,
        n_epochs=n_epochs,
        learning_rate=learning_rate,
        n_checkpoints=n_checkpoints,
        warmup_ratio=warmup_ratio,
    )
    info = {
        "job_id": res.job_id,
        "status": res.status,
        "output_name": res.output_name,
        "base_model": base_model,
        "suffix": suffix,
        "file_id": file_id,
        "n_epochs": n_epochs,
        "learning_rate": learning_rate,
    }
    _save_job_info(out_dir, info)
    console.print(f"[green]job_id:[/green] {res.job_id}  status={res.status}")
    console.print(f"Saved to {_job_info_path(out_dir)}")


# ----------------- status -----------------


@app.command("status")
def status_cmd(
    job_id: Optional[str] = typer.Option(None, "--job-id"),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    wait: bool = typer.Option(False, "--wait", help="Poll until terminal state."),
    poll_seconds: int = typer.Option(30, "--poll-seconds"),
    events: bool = typer.Option(False, "--events", help="Print recent training events."),
) -> None:
    """Show fine-tune job status; optionally block until done."""
    from finetune.together_client import list_finetune_events, retrieve_finetune

    if job_id is None:
        job_id = _load_job_info(out_dir)["job_id"]

    terminal = {"completed", "error", "cancelled", "failed"}
    while True:
        res = retrieve_finetune(job_id)
        console.print(f"job_id={job_id}  status={res.status}  output_name={res.output_name}")
        if events:
            for msg in list_finetune_events(job_id)[-10:]:
                console.print(f"  • {msg}")
        if res.output_name:
            # Persist as soon as we know the final model name.
            info = _load_job_info(out_dir) if _job_info_path(out_dir).exists() else {"job_id": job_id}
            info["status"] = res.status
            info["output_name"] = res.output_name
            _save_job_info(out_dir, info)
        if not wait or res.status in terminal:
            break
        time.sleep(poll_seconds)


# ----------------- infer -----------------


@app.command("infer")
def infer_cmd(
    model_id: str = typer.Option(..., "--model-id", help="Logical id written to responses.csv (e.g. ft-llama-3.2-3b-iter1)."),
    together_model: Optional[str] = typer.Option(None, "--together-model", help="Together model name. Defaults to output_name from job_info.json."),
    eval_csv: Path = typer.Option(DEFAULT_OUT / "eval.csv", "--eval-csv"),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Defaults to <model_id>-<UTC timestamp>."),
    results_root: Path = typer.Option(RESULTS_ROOT, "--results-root"),
    concurrency: int = typer.Option(8, "--concurrency"),
    max_tokens: int = typer.Option(1024, "--max-tokens"),
    temperature: float = typer.Option(0.0, "--temperature"),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
) -> None:
    """Run inference over eval.csv → results/<run_id>/responses.csv."""
    if together_model is None:
        info = _load_job_info(out_dir)
        together_model = info.get("output_name") or info.get("base_model")
        if not together_model:
            raise typer.BadParameter(
                "Could not infer --together-model from job_info.json. Pass it explicitly."
            )

    if run_id is None:
        import datetime as dt
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{model_id}-{ts}"

    run_dir = results_root / run_id
    rows = _read_rows_from_eval_csv(eval_csv)
    console.print(
        f"Inferring [bold]{together_model}[/bold] over {len(rows)} eval rows → "
        f"{run_dir / 'responses.csv'}"
    )

    cfg = InferConfig(
        model_id=model_id,
        together_model=together_model,
        run_dir=run_dir,
        run_id=run_id,
        concurrency=concurrency,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    run_inference_sync(cfg, rows)
    console.print(f"\nNext step:  uv run evaluator score --responses {run_dir}")


# ----------------- score -----------------


@app.command("score")
def score_cmd(
    run_id: str = typer.Argument(..., help="The run id under results/."),
    results_root: Path = typer.Option(RESULTS_ROOT, "--results-root"),
    dataset: Path = typer.Option(DEFAULT_OUT / "eval.csv", "--dataset", help="Pass the held-out eval.csv so the evaluator's dataset lookup matches."),
) -> None:
    """Shell out to the parent evaluator on the run dir."""
    run_dir = results_root / run_id
    if not (run_dir / "responses.csv").exists():
        raise typer.BadParameter(f"No responses.csv at {run_dir}.")
    cmd = [
        sys.executable, "-m", "evaluator.main", "score",
        "--responses", str(run_dir),
        "--dataset", str(dataset),
    ]
    console.print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))


# ----------------- all-in-one -----------------


@app.command("all")
def all_cmd(
    base_model: str = typer.Option(DEFAULT_BASE_MODEL, "--base-model"),
    suffix: str = typer.Option("smart-fmt", "--suffix"),
    model_id: str = typer.Option("ft-smart-fmt-v1", "--model-id"),
    n_epochs: int = typer.Option(3, "--n-epochs"),
    learning_rate: float = typer.Option(1e-4, "--learning-rate"),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    poll_seconds: int = typer.Option(30, "--poll-seconds"),
    concurrency: int = typer.Option(8, "--concurrency"),
) -> None:
    """split → upload → train → wait → infer → score. Blocks until done."""
    ctx_split = {
        "dataset": DEFAULT_DATASET, "messy": DEFAULT_MESSY, "out_dir": out_dir,
        "eval_frac": 0.20, "seed": 42,
    }
    split_cmd(**ctx_split)
    upload_cmd(file=out_dir / "train.jsonl", out_dir=out_dir)
    train_cmd(
        base_model=base_model, suffix=suffix, file_id=None, out_dir=out_dir,
        n_epochs=n_epochs, learning_rate=learning_rate, n_checkpoints=1, warmup_ratio=0.03,
    )
    status_cmd(job_id=None, out_dir=out_dir, wait=True, poll_seconds=poll_seconds, events=True)
    infer_cmd(
        model_id=model_id, together_model=None,
        eval_csv=out_dir / "eval.csv", run_id=None, results_root=RESULTS_ROOT,
        concurrency=concurrency, max_tokens=1024, temperature=0.0, out_dir=out_dir,
    )


# ----------------- endpoint lifecycle -----------------


def _endpoint_info_path(out_dir: Path) -> Path:
    return out_dir / "endpoint_info.json"


def _wait_until_ready(endpoint_id: str, *, timeout_s: int = 1800, poll_s: int = 15) -> None:
    """Poll until the endpoint is STARTED and responding to a trivial chat call."""
    from finetune.together_client import _client, retrieve_endpoint

    deadline = time.time() + timeout_s
    last_state = ""
    while time.time() < deadline:
        info = retrieve_endpoint(endpoint_id)
        if info.state != last_state:
            console.print(f"  endpoint {endpoint_id}: state={info.state}")
            last_state = info.state
        if info.state == "STARTED":
            # Try a tiny ping to confirm the model is actually serving.
            # IMPORTANT: route by endpoint.name (unique routing handle with -hash suffix),
            # not endpoint.model — the bare model id is treated as a non-serverless lookup
            # and rejected even when the dedicated endpoint is up.
            try:
                client = _client()
                client.chat.completions.create(
                    model=info.name or info.model,
                    messages=[{"role": "user", "content": "ok"}],
                    max_tokens=1,
                    temperature=0.0,
                )
                console.print(f"[green]Endpoint {endpoint_id} is serving.[/green]")
                return
            except Exception as e:  # noqa: BLE001
                console.print(f"  not yet ready ({type(e).__name__}: {e}); retrying…")
        time.sleep(poll_s)
    raise RuntimeError(f"Endpoint {endpoint_id} did not become ready within {timeout_s}s.")


@app.command("deploy")
def deploy_cmd(
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    hardware: Optional[str] = typer.Option(None, "--hardware", help="Hardware SKU; if unset, picks the cheapest available."),
    display_name: Optional[str] = typer.Option(None, "--display-name"),
    inactive_timeout: int = typer.Option(10, "--inactive-timeout", help="Auto-stop after N minutes of no traffic."),
    wait: bool = typer.Option(True, "--wait/--no-wait"),
) -> None:
    """Create a dedicated endpoint for the FT model in out_dir/job_info.json."""
    from finetune.together_client import (
        create_endpoint,
        list_endpoint_hardware,
    )

    info = _load_job_info(out_dir)
    model = info.get("output_name")
    if not model:
        raise typer.BadParameter("job_info.json has no output_name; the FT job isn't complete.")

    if hardware is None:
        opts = list_endpoint_hardware(model)
        if not opts:
            raise typer.BadParameter(f"No hardware options returned for {model}.")
        opts.sort(key=lambda h: h.get("pricing", {}).get("cents_per_minute", 1e9))
        hardware = opts[0]["id"]
        console.print(f"Auto-selected hardware: [bold]{hardware}[/bold] ({opts[0].get('pricing', {}).get('cents_per_minute')}¢/min)")

    if display_name is None:
        display_name = f"ft-eval-{out_dir.name}"

    console.print(f"Creating endpoint for {model} on {hardware}…")
    ep = create_endpoint(
        model=model,
        hardware=hardware,
        display_name=display_name,
        inactive_timeout=inactive_timeout,
    )
    ep_info = {
        "id": ep.id, "name": ep.name, "model": ep.model, "hardware": ep.hardware,
        "state": ep.state, "display_name": ep.display_name,
        "inactive_timeout": inactive_timeout,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _endpoint_info_path(out_dir).write_text(json.dumps(ep_info, indent=2))
    console.print(f"[green]endpoint id:[/green] {ep.id}  state={ep.state}")

    if wait:
        _wait_until_ready(ep.id)


@app.command("stop")
def stop_cmd(
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    endpoint_id: Optional[str] = typer.Option(None, "--endpoint-id"),
) -> None:
    """Stop a dedicated endpoint (pauses billing; keeps the definition)."""
    from finetune.together_client import stop_endpoint

    if endpoint_id is None:
        p = _endpoint_info_path(out_dir)
        if not p.exists():
            raise typer.BadParameter(f"No endpoint_info.json at {p} and no --endpoint-id.")
        endpoint_id = json.loads(p.read_text())["id"]

    ep = stop_endpoint(endpoint_id)
    console.print(f"[yellow]Stopped[/yellow] {endpoint_id}  state={ep.state}")


@app.command("delete-endpoint")
def delete_endpoint_cmd(
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    endpoint_id: Optional[str] = typer.Option(None, "--endpoint-id"),
) -> None:
    """Delete a dedicated endpoint (final teardown)."""
    from finetune.together_client import delete_endpoint

    if endpoint_id is None:
        p = _endpoint_info_path(out_dir)
        if not p.exists():
            raise typer.BadParameter(f"No endpoint_info.json at {p} and no --endpoint-id.")
        endpoint_id = json.loads(p.read_text())["id"]

    delete_endpoint(endpoint_id)
    console.print(f"[red]Deleted[/red] {endpoint_id}")


@app.command("deploy-eval-stop")
def deploy_eval_stop_cmd(
    model_id: str = typer.Option(..., "--model-id"),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out-dir"),
    hardware: Optional[str] = typer.Option(None, "--hardware"),
    availability_zone: Optional[str] = typer.Option(None, "--availability-zone"),
    eval_csv: Path = typer.Option(DEFAULT_OUT / "eval.csv", "--eval-csv"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
    results_root: Path = typer.Option(RESULTS_ROOT, "--results-root"),
    concurrency: int = typer.Option(8, "--concurrency"),
    max_tokens: int = typer.Option(1024, "--max-tokens"),
    inactive_timeout: int = typer.Option(10, "--inactive-timeout"),
    delete_after: bool = typer.Option(False, "--delete-after/--keep"),
) -> None:
    """One-shot: deploy → wait → infer → stop. Always stops in try/finally."""
    from finetune.together_client import (
        create_endpoint,
        delete_endpoint,
        list_endpoint_hardware,
        stop_endpoint,
    )

    info = _load_job_info(out_dir)
    base_model_id = info.get("output_name")
    if not base_model_id:
        raise typer.BadParameter("job_info.json has no output_name.")

    if hardware is None:
        opts = list_endpoint_hardware(base_model_id)
        if not opts:
            raise typer.BadParameter(f"No hardware options returned for {together_model}.")
        opts.sort(key=lambda h: h.get("pricing", {}).get("cents_per_minute", 1e9))
        hardware = opts[0]["id"]
        cpm = opts[0].get("pricing", {}).get("cents_per_minute")
        console.print(f"Auto-selected hardware: [bold]{hardware}[/bold] ({cpm}¢/min)")

    if run_id is None:
        import datetime as dt
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{model_id}-{ts}"
    run_dir = results_root / run_id

    rows = _read_rows_from_eval_csv(eval_csv)
    console.print(f"Deploying [bold]{base_model_id}[/bold] → inferring {len(rows)} rows → {run_dir}")

    ep = create_endpoint(
        model=base_model_id,
        hardware=hardware,
        display_name=f"ft-eval-{out_dir.name}",
        inactive_timeout=inactive_timeout,
        availability_zone=availability_zone,
    )
    # Together routes chat.completions by endpoint.name (model + -hash suffix), not by the
    # bare model id — passing the bare id returns "non-serverless model" 400 even with a
    # live dedicated endpoint.
    together_model = ep.name or base_model_id
    ep_info = {
        "id": ep.id, "name": ep.name, "model": ep.model, "hardware": ep.hardware,
        "display_name": ep.display_name, "inactive_timeout": inactive_timeout,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": run_id,
    }
    _endpoint_info_path(out_dir).write_text(json.dumps(ep_info, indent=2))
    console.print(f"[green]endpoint id:[/green] {ep.id}")

    started = time.time()
    try:
        _wait_until_ready(ep.id)
        warm_s = time.time() - started
        console.print(f"Cold start: {warm_s:.1f}s")

        cfg = InferConfig(
            model_id=model_id,
            together_model=together_model,
            run_dir=run_dir,
            run_id=run_id,
            concurrency=concurrency,
            max_tokens=max_tokens,
            temperature=0.0,
        )
        run_inference_sync(cfg, rows)
        console.print(f"\nNext step:  uv run evaluator score --responses {run_dir}")
    finally:
        total_min = (time.time() - started) / 60.0
        console.print(f"[yellow]Total endpoint uptime ≈ {total_min:.2f} min[/yellow]")
        try:
            if delete_after:
                delete_endpoint(ep.id)
                console.print(f"[red]Deleted[/red] {ep.id}")
            else:
                stop_endpoint(ep.id)
                console.print(f"[yellow]Stopped[/yellow] {ep.id}")
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]WARNING:[/red] failed to stop endpoint {ep.id}: {e}")
            console.print(f"[red]Manually stop it:[/red] uv run finetune stop --endpoint-id {ep.id}")


@app.command("show-prompt")
def show_prompt_cmd() -> None:
    """Print the fine-tune system prompt + its hash."""
    from finetune.prompts import FT_SYSTEM_PROMPT
    console.print(f"[bold]Hash:[/bold] {prompt_hash()}\n")
    console.print(FT_SYSTEM_PROMPT)


if __name__ == "__main__":
    app()
