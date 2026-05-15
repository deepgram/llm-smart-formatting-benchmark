"""Dual-judge scorer for Mercury 2 responses.

Reads finetune/runs/mercury-2/<level>/responses.csv and grades every row
with Claude Opus 4.7 *and* GPT-5.5 in parallel, using the same
JUDGE_ACCURACY_SYSTEM prompt that scored the fine-tuned models — so the
comparison to together_ai.html numbers is apples-to-apples.

Writes finetune/runs/mercury-2/<level>/scored.csv with:
    id, entity_class, variant, expected_output, response,
    latency_ms, reasoning_tokens, completion_tokens,
    opus_accuracy, opus_catastrophic, opus_reason,
    gpt_accuracy,  gpt_catastrophic,  gpt_reason,
    opus_pass, gpt_pass, both_pass, disagree

Usage:
    ANTHROPIC_API_KEY=... OPENAI_API_KEY=... \\
        uv run python -m finetune.score_mercury --levels instant,low,medium,high
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

from evaluator.judge import JUDGE_MODEL_DEFAULT, JUDGE_MODEL_SECONDARY_DEFAULT, JudgeClient

HERE = Path(__file__).resolve().parent
RUNS_ROOT = HERE / "runs" / "mercury-2"
EVAL_CSV = HERE / "data" / "eval.csv"
LEVELS = ["instant", "low", "medium", "high"]


OUT_FIELDS = [
    "id", "entity_class", "variant", "expected_output", "response",
    "latency_ms", "reasoning_tokens", "completion_tokens",
    "opus_accuracy", "opus_catastrophic", "opus_reason",
    "gpt_accuracy", "gpt_catastrophic", "gpt_reason",
    "opus_pass", "gpt_pass", "both_pass", "disagree",
    "error",
]


def _load_eval_meta() -> dict[str, dict]:
    """id -> {variant, formatting_prompt} so we can recreate the judge's
    user-message context (matches what the fine-tunes were scored with)."""
    return {
        row["id"]: {
            "variant": row.get("variant", ""),
            "formatting_prompt": row.get("prompt", "") or "",
            "input_text": row.get("input_text", "") or "",
        }
        for row in csv.DictReader(EVAL_CSV.open())
    }


async def _score_level(level: str, eval_meta: dict[str, dict], concurrency: int) -> None:
    in_csv = RUNS_ROOT / level / "responses.csv"
    out_csv = RUNS_ROOT / level / "scored.csv"
    if not in_csv.exists():
        print(f"[{level}] SKIP — no responses.csv")
        return

    rows = list(csv.DictReader(in_csv.open()))
    print(f"[{level}] scoring {len(rows)} rows: opus={JUDGE_MODEL_DEFAULT} + gpt={JUDGE_MODEL_SECONDARY_DEFAULT}")

    opus = JudgeClient(model=JUDGE_MODEL_DEFAULT, concurrency=concurrency)
    gpt = JudgeClient(model=JUDGE_MODEL_SECONDARY_DEFAULT, concurrency=concurrency)

    async def score_row(row: dict) -> dict:
        meta = eval_meta.get(row["id"], {})
        kwargs = dict(
            formatting_prompt=meta.get("formatting_prompt", ""),
            input_text=meta.get("input_text", ""),
            expected_output=row.get("expected_output", ""),
            actual_output=row.get("response", ""),
            entity_class=row.get("entity_class", ""),
            variant=meta.get("variant", ""),
        )
        actual = row.get("response", "")
        if not actual.strip():
            # Skip judging empty responses — pre-mark as fail
            return _empty_result(row, meta, reason="empty_response")
        try:
            opus_j, gpt_j = await asyncio.gather(
                opus.judge_accuracy(**kwargs),
                gpt.judge_accuracy(**kwargs),
            )
        except Exception as e:  # noqa: BLE001
            return _empty_result(row, meta, reason=f"judge_error: {type(e).__name__}: {e}")
        opus_pass = opus_j.accuracy == "pass"
        gpt_pass = gpt_j.accuracy == "pass"
        return {
            "id": row["id"],
            "entity_class": row["entity_class"],
            "variant": meta.get("variant", ""),
            "expected_output": row["expected_output"],
            "response": actual,
            "latency_ms": row.get("latency_ms", ""),
            "reasoning_tokens": row.get("reasoning_tokens", ""),
            "completion_tokens": row.get("completion_tokens", ""),
            "opus_accuracy": opus_j.accuracy,
            "opus_catastrophic": opus_j.catastrophic,
            "opus_reason": opus_j.accuracy_reason[:200],
            "gpt_accuracy": gpt_j.accuracy,
            "gpt_catastrophic": gpt_j.catastrophic,
            "gpt_reason": gpt_j.accuracy_reason[:200],
            "opus_pass": opus_pass,
            "gpt_pass": gpt_pass,
            "both_pass": opus_pass and gpt_pass,
            "disagree": opus_pass != gpt_pass,
            "error": row.get("error", ""),
        }

    results = await asyncio.gather(*[score_row(r) for r in rows])
    await opus.aclose()
    await gpt.aclose()

    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        w.writerows(results)
    print(f"[{level}] wrote {out_csv}")
    _print_summary(level, results)


def _empty_result(row: dict, meta: dict, *, reason: str) -> dict:
    return {
        "id": row["id"],
        "entity_class": row["entity_class"],
        "variant": meta.get("variant", ""),
        "expected_output": row.get("expected_output", ""),
        "response": row.get("response", ""),
        "latency_ms": row.get("latency_ms", ""),
        "reasoning_tokens": row.get("reasoning_tokens", ""),
        "completion_tokens": row.get("completion_tokens", ""),
        "opus_accuracy": "other",
        "opus_catastrophic": True,
        "opus_reason": reason,
        "gpt_accuracy": "other",
        "gpt_catastrophic": True,
        "gpt_reason": reason,
        "opus_pass": False,
        "gpt_pass": False,
        "both_pass": False,
        "disagree": False,
        "error": row.get("error", "") or reason,
    }


def _print_summary(level: str, results: list[dict]) -> None:
    n = len(results)
    opus_p = sum(1 for r in results if r["opus_pass"])
    gpt_p = sum(1 for r in results if r["gpt_pass"])
    both = sum(1 for r in results if r["both_pass"])
    disagree = sum(1 for r in results if r["disagree"])
    opus_cat = sum(1 for r in results if str(r["opus_catastrophic"]) in ("True", "true", "1"))

    lats = sorted(int(r["latency_ms"]) for r in results if str(r["latency_ms"]).isdigit())
    rts = sorted(int(r["reasoning_tokens"]) for r in results if str(r["reasoning_tokens"]).isdigit())
    def pct(arr, p):
        if not arr: return 0
        return arr[min(len(arr)-1, int(round((len(arr)-1)*p)))]

    print(f"\n[{level}] n={n}")
    print(f"  opus pass     : {opus_p}/{n} ({100*opus_p/n:.0f}%)")
    print(f"  gpt  pass     : {gpt_p}/{n} ({100*gpt_p/n:.0f}%)")
    print(f"  both pass     : {both}/{n} ({100*both/n:.0f}%)")
    print(f"  disagree      : {disagree}/{n} ({100*disagree/n:.0f}%)")
    print(f"  catastrophic  : {opus_cat}/{n}")
    if lats:
        print(f"  latency_ms    : p50={pct(lats,0.5)}  p90={pct(lats,0.9)}  p99={pct(lats,0.99)}")
    if rts:
        print(f"  reasoning_tok : p50={pct(rts,0.5)}  p90={pct(rts,0.9)}  p99={pct(rts,0.99)}")


async def _amain(levels: list[str], concurrency: int) -> None:
    meta = _load_eval_meta()
    for lvl in levels:
        await _score_level(lvl, meta, concurrency)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--levels", default=",".join(LEVELS))
    p.add_argument("--concurrency", type=int, default=8)
    args = p.parse_args()

    for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        if not os.environ.get(var):
            print(f"ERROR: {var} not set", file=sys.stderr)
            return 1

    levels = [x.strip() for x in args.levels.split(",") if x.strip()]
    unknown = [x for x in levels if x not in LEVELS]
    if unknown:
        print(f"ERROR: unknown reasoning levels: {unknown}", file=sys.stderr)
        return 1

    asyncio.run(_amain(levels, args.concurrency))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
