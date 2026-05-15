"""Build the fine-tune corpus and 80/20 train/eval split.

Sources combined:
  - ``synthetic_data.csv``  (501 rows: synthetic + adversarial + canonical)
  - ``messy_prompts.txt``   (~20 multi-entity rows)

Split policy:
  - All ``source=customer_canonical`` rows go to the **eval** side. They are
    the highest-trust ground truth — the fine-tuned model must never see
    them during training.
  - Everything else is split 80/20, stratified by ``entity_class`` so the
    eval slice has the same class mix as train. Seeded for reproducibility.

Outputs (under ``finetune/data/``):
  - ``train.jsonl`` — Together "conversational" format, one JSON per line
    with ``{"messages": [system, user, assistant]}``
  - ``eval.jsonl``  — same shape (for completeness / sanity-checking)
  - ``eval.csv``    — `sample_id, entity_class, variant, prompt, input_text,
                       expected_output, difficulty, domain, source` — exactly
    the columns the parent runner/evaluator expect, so we can re-use that
    pipeline to score the fine-tuned model.
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd

from finetune.prompts import build_messages
from iterate.dataset import parse_messy_prompts


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = REPO_ROOT / "synthetic_data.csv"
DEFAULT_MESSY = REPO_ROOT / "messy_prompts.txt"
DEFAULT_OUT = Path(__file__).resolve().parent / "data"
DEFAULT_AUGMENTED = DEFAULT_OUT / "synthetic_augmented.csv"
DEFAULT_AUGMENTED_V2 = DEFAULT_OUT / "synthetic_augmented_v2.csv"
DEFAULT_AUGMENTED_V3 = DEFAULT_OUT / "synthetic_augmented_v3.csv"
DEFAULT_AUGMENTED_V4 = DEFAULT_OUT / "synthetic_augmented_v4.csv"
DEFAULT_AUGMENTED_V5 = DEFAULT_OUT / "synthetic_augmented_v5.csv"


@dataclass(frozen=True)
class Row:
    sample_id: str
    entity_class: str
    variant: str
    formatting_prompt: str
    input_text: str
    expected_output: str
    source: str
    difficulty: str
    domain: str


# ----------------- loading -----------------


def _load_synthetic(path: Path) -> list[Row]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    out: list[Row] = []
    for _, r in df.iterrows():
        out.append(
            Row(
                sample_id=str(r["id"]),
                entity_class=str(r.get("entity_class", "")),
                variant=str(r.get("variant", "")),
                formatting_prompt=str(r.get("prompt", "") or ""),
                input_text=str(r.get("input_text", "") or ""),
                expected_output=str(r.get("expected_output", "") or ""),
                source=str(r.get("source", "")),
                difficulty=str(r.get("difficulty", "")),
                domain=str(r.get("domain", "")),
            )
        )
    return out


def _load_messy(path: Path) -> list[Row]:
    samples = parse_messy_prompts(path)
    out: list[Row] = []
    for s in samples:
        out.append(
            Row(
                sample_id=s.sample_id,
                entity_class=s.entity_class,
                variant=s.variant,
                formatting_prompt=s.formatting_prompt,
                input_text=s.input_text,
                expected_output=s.expected_output,
                source=s.source,
                difficulty=s.difficulty,
                domain=s.variant,
            )
        )
    return out


def load_corpus(
    dataset: Path = DEFAULT_DATASET,
    messy: Path = DEFAULT_MESSY,
    augmented: Path = DEFAULT_AUGMENTED,
    augmented_v2: Path = DEFAULT_AUGMENTED_V2,
    augmented_v3: Path = DEFAULT_AUGMENTED_V3,
    augmented_v4: Path = DEFAULT_AUGMENTED_V4,
    augmented_v5: Path = DEFAULT_AUGMENTED_V5,
) -> list[Row]:
    rows = _load_synthetic(dataset)
    if messy.exists():
        rows.extend(_load_messy(messy))
    if augmented.exists():
        # Augmented CSV has the same schema as synthetic_data.csv.
        rows.extend(_load_synthetic(augmented))
    if augmented_v2.exists():
        rows.extend(_load_synthetic(augmented_v2))
    if augmented_v3.exists():
        rows.extend(_load_synthetic(augmented_v3))
    if augmented_v4.exists():
        rows.extend(_load_synthetic(augmented_v4))
    if augmented_v5.exists():
        rows.extend(_load_synthetic(augmented_v5))
    # Drop rows missing inputs/outputs — they would only confuse training.
    return [r for r in rows if r.input_text and r.expected_output]


# ----------------- 80/20 stratified split -----------------


def split_train_eval(
    rows: list[Row],
    *,
    eval_frac: float = 0.20,
    seed: int = 42,
) -> tuple[list[Row], list[Row]]:
    """Hold-out all customer_canonical; 80/20 stratify the rest by entity_class.

    Adversarial rows are split alongside everything else — we *want* the model
    to learn the prompt-injection defense pattern, so adversarial transcripts
    should appear in train as well as eval.
    """
    rng = random.Random(seed)
    canonical: list[Row] = [r for r in rows if r.source == "customer_canonical"]
    rest: list[Row] = [r for r in rows if r.source != "customer_canonical"]

    # Stratification key: messy rows have unique compound entity_class
    # values ("MONEY|DATE|PHONE_NUMBER", etc.), which would put every messy
    # sample in its own size-1 bucket → all into eval. They're conceptually
    # the same as MIXED rows (multi-entity transcripts), so merge them into
    # the MIXED bucket for stratification.
    def strat_key(r: Row) -> str:
        if r.source == "messy" or "|" in (r.entity_class or ""):
            return "MIXED"
        return r.entity_class or "_blank_"

    by_class: dict[str, list[Row]] = {}
    for r in rest:
        by_class.setdefault(strat_key(r), []).append(r)

    train: list[Row] = []
    eval_: list[Row] = list(canonical)
    for cls, bucket in sorted(by_class.items()):
        bucket_sorted = sorted(bucket, key=lambda x: x.sample_id)
        rng.shuffle(bucket_sorted)
        # Round so very small buckets still place at least 1 in eval.
        n_eval = max(1, round(len(bucket_sorted) * eval_frac)) if bucket_sorted else 0
        n_eval = min(n_eval, len(bucket_sorted) - 1) if len(bucket_sorted) > 1 else n_eval
        eval_.extend(bucket_sorted[:n_eval])
        train.extend(bucket_sorted[n_eval:])

    train.sort(key=lambda r: r.sample_id)
    eval_.sort(key=lambda r: r.sample_id)
    return train, eval_


# ----------------- writers -----------------


def write_jsonl(rows: list[Row], path: Path, *, with_assistant: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            messages = build_messages(
                input_text=r.input_text,
                formatting_prompt=r.formatting_prompt,
                expected_output=r.expected_output if with_assistant else None,
            )
            f.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")


EVAL_CSV_FIELDS = [
    "id",
    "entity_class",
    "variant",
    "prompt",
    "input_text",
    "expected_output",
    "difficulty",
    "domain",
    "source",
    "notes",
]


def write_eval_csv(rows: list[Row], path: Path) -> None:
    """Write the eval slice in the same shape as ``synthetic_data.csv`` so
    the parent runner + evaluator can consume it unchanged."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EVAL_CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "id": r.sample_id,
                    "entity_class": r.entity_class,
                    "variant": r.variant,
                    "prompt": r.formatting_prompt,
                    "input_text": r.input_text,
                    "expected_output": r.expected_output,
                    "difficulty": r.difficulty,
                    "domain": r.domain,
                    "source": r.source,
                    "notes": "",
                }
            )


# ----------------- summary helpers -----------------


def class_counts(rows: Iterable[Row]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        out[r.entity_class or "_blank_"] = out.get(r.entity_class or "_blank_", 0) + 1
    return dict(sorted(out.items()))


__all__ = [
    "Row",
    "load_corpus",
    "split_train_eval",
    "write_jsonl",
    "write_eval_csv",
    "class_counts",
    "DEFAULT_DATASET",
    "DEFAULT_MESSY",
    "DEFAULT_OUT",
]
