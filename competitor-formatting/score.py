"""Score competitor STT formatting against expected_output with TWO judges.

Reads responses/<provider>.csv. For each row, runs Claude Opus 4.7 and
OpenAI GPT-5.5 in parallel as independent judges. Writes
responses/<provider>.scored.csv and prints a per-class summary plus
inter-judge agreement.

Output columns:
    id, entity_class, expected_output, transcript,
    stt_latency_ms, stt_error,
    exact_match,
    opus_label, opus_notes, opus_pass,
    gpt_label,  gpt_notes,  gpt_pass,
    both_pass, disagree

Usage:
    ANTHROPIC_API_KEY=... OPENAI_API_KEY=... \\
      uv run python competitor-formatting/score.py --provider deepgram
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESP_ROOT = HERE / "responses"

OPUS_MODEL = "claude-opus-4-7"  # same as evaluator/judge.py
GPT_MODEL = "gpt-5.5"           # same as runner/models.py gpt-5-5 entry

JUDGE_SYSTEM = """You grade speech-to-text output for entity formatting quality.

Given:
- a reference (the formatted text we expect)
- a transcript (what the STT system returned)

Score whether the entities in the transcript are formatted correctly. The
transcript may have minor word-level differences from the reference because
of acoustic similarity; that's OK as long as the *entity formatting* is right
(money has $ + decimals, dates are like "March 5, 2026", phone numbers are
grouped, emails are "user@host", URLs are real-looking, etc.).

Output strict JSON only:
{
  "label": "pass" | "style_violation" | "numeric_drift" | "wrong_value" | "other",
  "notes": "one short sentence"
}

- pass: entities are correctly formatted, even if surrounding words differ slightly
- style_violation: entity content is right but formatted unusually (e.g. "March 5 2026" vs "March 5, 2026")
- numeric_drift: a digit is wrong or shifted (e.g. "$171.41" vs "$71.41")
- wrong_value: the entity is entirely wrong (e.g. wrong date, wrong phone)
- other: anything else (empty transcript, hallucinated content, etc.)"""

USER_TMPL = "reference:\n{ref}\n\ntranscript:\n{hyp}\n\nReturn JSON only."


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[.,;:!?]+$", "", s)
    return s


def _parse_json(text: str) -> tuple[str, str]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    # If there's text around the JSON, try to extract the first {...}
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        text = m.group(0)
    try:
        j = json.loads(text)
        return str(j.get("label", "other")), str(j.get("notes", ""))[:200]
    except Exception as e:  # noqa: BLE001
        return "other", f"parse_error: {type(e).__name__}: {text[:100]}"


async def judge_opus(client, ref: str, hyp: str) -> tuple[str, str]:
    if not hyp.strip():
        return "other", "empty transcript"
    try:
        msg = await client.messages.create(
            model=OPUS_MODEL,
            max_tokens=200,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": USER_TMPL.format(ref=ref, hyp=hyp)}],
        )
        text = msg.content[0].text if msg.content else ""
        return _parse_json(text)
    except Exception as e:  # noqa: BLE001
        return "other", f"judge_error: {type(e).__name__}: {e}"


async def judge_gpt(client, ref: str, hyp: str) -> tuple[str, str]:
    if not hyp.strip():
        return "other", "empty transcript"
    try:
        resp = await client.chat.completions.create(
            model=GPT_MODEL,
            max_completion_tokens=200,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": USER_TMPL.format(ref=ref, hyp=hyp)},
            ],
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content or ""
        return _parse_json(text)
    except Exception as e:  # noqa: BLE001
        return "other", f"judge_error: {type(e).__name__}: {e}"


async def _score(provider: str, concurrency: int) -> None:
    in_csv = RESP_ROOT / f"{provider}.csv"
    out_csv = RESP_ROOT / f"{provider}.scored.csv"
    if not in_csv.exists():
        print(f"ERROR: {in_csv} not found", file=sys.stderr)
        return

    rows = list(csv.DictReader(in_csv.open()))
    print(f"[{provider}] scoring {len(rows)} rows: opus={OPUS_MODEL} + gpt={GPT_MODEL}")

    from anthropic import AsyncAnthropic
    from openai import AsyncOpenAI
    a_client = AsyncAnthropic()
    o_client = AsyncOpenAI()
    sem = asyncio.Semaphore(concurrency)

    async def worker(row: dict) -> dict:
        ref = row["expected_output"]
        hyp = row["transcript"]
        exact = _normalize(ref) == _normalize(hyp)
        async with sem:
            (opus_label, opus_notes), (gpt_label, gpt_notes) = await asyncio.gather(
                judge_opus(a_client, ref, hyp),
                judge_gpt(o_client, ref, hyp),
            )
        opus_pass = opus_label == "pass"
        gpt_pass = gpt_label == "pass"
        return {
            "id": row["id"],
            "entity_class": row["entity_class"],
            "expected_output": ref,
            "transcript": hyp,
            "stt_latency_ms": row.get("latency_ms", ""),
            "stt_error": row.get("error", ""),
            "exact_match": exact,
            "opus_label": opus_label,
            "opus_notes": opus_notes,
            "opus_pass": opus_pass,
            "gpt_label": gpt_label,
            "gpt_notes": gpt_notes,
            "gpt_pass": gpt_pass,
            "both_pass": opus_pass and gpt_pass,
            "disagree": opus_pass != gpt_pass,
        }

    results = await asyncio.gather(*[worker(r) for r in rows])

    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"[{provider}] wrote {out_csv}")
    _print_summary(provider, results)


def _print_summary(provider: str, results: list[dict]) -> None:
    n = len(results)
    opus_p = sum(1 for r in results if r["opus_pass"])
    gpt_p = sum(1 for r in results if r["gpt_pass"])
    both = sum(1 for r in results if r["both_pass"])
    disagree = sum(1 for r in results if r["disagree"])
    exact = sum(1 for r in results if r["exact_match"])

    # STT latency stats
    lats = sorted(int(r["stt_latency_ms"]) for r in results if str(r["stt_latency_ms"]).isdigit())
    def pct(p: float) -> int:
        if not lats:
            return 0
        i = min(len(lats) - 1, int(round((len(lats) - 1) * p)))
        return lats[i]

    print(f"\n[{provider}] overall (n={n}):")
    print(f"  exact match :     {exact}/{n}  ({100*exact/n:.0f}%)")
    print(f"  opus pass   :     {opus_p}/{n}  ({100*opus_p/n:.0f}%)")
    print(f"  gpt  pass   :     {gpt_p}/{n}  ({100*gpt_p/n:.0f}%)")
    print(f"  both pass   :     {both}/{n}  ({100*both/n:.0f}%)")
    print(f"  disagree    :     {disagree}/{n}  ({100*disagree/n:.0f}%)")
    if lats:
        print(f"  stt latency :     p50={pct(0.50)}ms  p90={pct(0.90)}ms  p99={pct(0.99)}ms")

    by_class: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_class[r["entity_class"]].append(r)
    print(f"\n  {'class':16}  {'n':>3}  {'opus':>5}  {'gpt':>5}  {'both':>5}  {'disag':>5}")
    for cls in sorted(by_class):
        rs = by_class[cls]
        o = sum(1 for r in rs if r["opus_pass"])
        g = sum(1 for r in rs if r["gpt_pass"])
        b = sum(1 for r in rs if r["both_pass"])
        d = sum(1 for r in rs if r["disagree"])
        print(f"  {cls:16}  {len(rs):>3}  {o:>5}  {g:>5}  {b:>5}  {d:>5}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True)
    p.add_argument("--concurrency", type=int, default=8)
    args = p.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 1
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        return 1
    asyncio.run(_score(args.provider, args.concurrency))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
