"""Restart a STOPPED endpoint, run inference, stop+delete.

Faster than deploy-eval-stop because the model is already loaded — the
endpoint just needs to come back up from STOPPED.

Usage:
    uv run python -m finetune.restart_and_eval \\
        --endpoint-id endpoint-... \\
        --model-id ft-... \\
        --run-id ft-...-<ts>
"""

from __future__ import annotations

import csv
import datetime as dt
import sys
import time
from pathlib import Path

import typer

from finetune.dataset import Row
from finetune.infer import InferConfig, run_inference_sync
from finetune.main import RESULTS_ROOT, _load_dotenv, _read_rows_from_eval_csv

_load_dotenv()

app = typer.Typer(add_completion=False)


@app.command()
def main(
    endpoint_id: str = typer.Option(..., "--endpoint-id"),
    model_id: str = typer.Option(..., "--model-id"),
    run_id: str = typer.Option(..., "--run-id"),
    eval_csv: Path = typer.Option(Path("finetune/data/eval.csv"), "--eval-csv"),
    concurrency: int = typer.Option(8, "--concurrency"),
    delete_after: bool = typer.Option(True, "--delete-after/--keep"),
) -> None:
    from finetune.together_client import (
        _client,
        delete_endpoint,
        retrieve_endpoint,
        stop_endpoint,
    )

    c = _client()

    # Start it back up — but only if it's currently STOPPED. Together rejects
    # an update(state=STARTED) on an already-STARTING/STARTED endpoint with
    # 400 "Endpoint cannot be started. It is already starting/started".
    cur = retrieve_endpoint(endpoint_id)
    print(f"Endpoint {endpoint_id} current state: {cur.state}")
    if cur.state in ("STOPPED",):
        print(f"Restarting endpoint {endpoint_id}…")
        c.endpoints.update(endpoint_id, state="STARTED")

    started = time.time()
    last_state = ""
    timeout_s = 1800
    while time.time() - started < timeout_s:
        info = retrieve_endpoint(endpoint_id)
        if info.state != last_state:
            print(f"  state={info.state}")
            last_state = info.state
        if info.state == "STARTED":
            try:
                c.chat.completions.create(
                    model=info.name or info.model,
                    messages=[{"role": "user", "content": "ok"}],
                    max_tokens=1,
                    temperature=0.0,
                )
                print(f"Endpoint serving. Warm-resume took {time.time() - started:.1f}s")
                break
            except Exception as e:  # noqa: BLE001
                print(f"  not yet serving ({type(e).__name__}); retrying…")
        time.sleep(15)
    else:
        raise SystemExit(f"Endpoint {endpoint_id} did not become ready in {timeout_s}s")

    together_model = info.name or info.model
    run_dir = RESULTS_ROOT / run_id
    rows = _read_rows_from_eval_csv(eval_csv)

    cfg = InferConfig(
        model_id=model_id,
        together_model=together_model,
        run_dir=run_dir,
        run_id=run_id,
        concurrency=concurrency,
        max_tokens=1024,
        temperature=0.0,
    )

    try:
        run_inference_sync(cfg, rows)
        print(f"\nNext step: uv run evaluator score --responses {run_dir}")
    finally:
        total_min = (time.time() - started) / 60.0
        print(f"Total uptime ≈ {total_min:.2f} min")
        try:
            if delete_after:
                delete_endpoint(endpoint_id)
                print(f"Deleted {endpoint_id}")
            else:
                stop_endpoint(endpoint_id)
                print(f"Stopped {endpoint_id}")
        except Exception as e:  # noqa: BLE001
            print(f"WARNING: stop/delete failed: {e}")
            print(f"Manually clean up: uv run finetune stop --endpoint-id {endpoint_id}")


if __name__ == "__main__":
    app()
