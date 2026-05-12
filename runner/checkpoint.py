"""Resumability: track which (run_id, model_id, sample_id) tuples are done."""

from __future__ import annotations

import csv
import os
from pathlib import Path


RESPONSES_FIELDS: list[str] = [
    "run_id",
    "model_id",
    "provider",
    "sample_id",
    "base_prompt_hash",
    "formatting_prompt",
    "input_text",
    "expected_output",
    "actual_output",
    "latency_total_ms",
    "latency_ttft_ms",
    "tokens_in",
    "tokens_out",
    "cost_usd",
    "finish_reason",
    "error",
    "attempted_at",
    "completed_at",
]


def responses_csv_path(run_dir: Path) -> Path:
    return run_dir / "responses.csv"


def load_completed(run_dir: Path) -> set[tuple[str, str]]:
    """Return the set of (model_id, sample_id) already present in responses.csv.

    A row counts as "completed" if it is present at all — including rows with
    an ``error`` populated. We do not retry past failures on resume; the user
    can delete those rows manually if they want a retry.
    """
    path = responses_csv_path(run_dir)
    if not path.exists():
        return set()
    done: set[tuple[str, str]] = set()
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            done.add((row.get("model_id", ""), row.get("sample_id", "")))
    return done


def ensure_responses_header(run_dir: Path) -> None:
    """Create responses.csv with the header row if it doesn't exist yet."""
    path = responses_csv_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESPONSES_FIELDS)
        writer.writeheader()


def append_response(run_dir: Path, row: dict[str, object]) -> None:
    """Append a single result row to responses.csv. Caller serializes."""
    path = responses_csv_path(run_dir)
    # Coerce all values to CSV-friendly strings; pandas can re-type on read.
    out = {k: ("" if row.get(k) is None else row.get(k)) for k in RESPONSES_FIELDS}
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESPONSES_FIELDS)
        writer.writerow(out)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass


# ----------------- Determinism CSV (extra `trial` column) -----------------

DETERMINISM_FIELDS: list[str] = [
    "run_id",
    "model_id",
    "provider",
    "sample_id",
    "trial",
    "base_prompt_hash",
    "formatting_prompt",
    "input_text",
    "expected_output",
    "actual_output",
    "latency_total_ms",
    "latency_ttft_ms",
    "tokens_in",
    "tokens_out",
    "cost_usd",
    "finish_reason",
    "error",
    "attempted_at",
    "completed_at",
]


def determinism_csv_path(run_dir: Path) -> Path:
    return run_dir / "determinism_responses.csv"


def ensure_determinism_header(run_dir: Path) -> None:
    path = determinism_csv_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DETERMINISM_FIELDS)
        writer.writeheader()


def load_completed_determinism(run_dir: Path) -> set[tuple[str, str, int]]:
    """Return {(model_id, sample_id, trial)} already present, for resume."""
    path = determinism_csv_path(run_dir)
    if not path.exists():
        return set()
    done: set[tuple[str, str, int]] = set()
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                trial = int(row.get("trial", "") or 0)
            except ValueError:
                continue
            done.add((row.get("model_id", ""), row.get("sample_id", ""), trial))
    return done


def append_determinism_row(run_dir: Path, row: dict[str, object]) -> None:
    path = determinism_csv_path(run_dir)
    out = {k: ("" if row.get(k) is None else row.get(k)) for k in DETERMINISM_FIELDS}
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DETERMINISM_FIELDS)
        writer.writerow(out)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
