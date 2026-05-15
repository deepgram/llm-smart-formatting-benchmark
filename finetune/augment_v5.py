"""Round-5 augmentation — scale the v4 weak-class buckets up to ≥30 eval rows.

After v4 the eval-set counts for the weak classes are:

  CREDIT_CARD  = 11
  NUMERIC_ID   = 15
  TIME         = 10
  PHONE_NUMBER = 15
  NO_ENTITY    =  6

With the 80/20 stratified split, every additional corpus row contributes
~0.20 to eval and ~0.80 to train. To reliably reach **30 eval rows** per
class we need ~148 total corpus rows in each. v5 closes that gap with a
small safety buffer:

  CREDIT_CARD  +100  (53 -> ~153)
  NUMERIC_ID   + 85  (67 -> ~152)
  TIME         +100  (50 -> ~150)
  PHONE_NUMBER + 85  (68 -> ~153)
  NO_ENTITY    +120  (30 -> ~150)

The class guidance is re-used from v4 verbatim (same patterns; just need
more examples). Each class is generated in **batches of 30** with distinct
seeds so Claude doesn't repeat itself in one giant call, and so we stay
well under ``max_tokens=8192``.

Writes ``finetune/data/synthetic_augmented_v5.csv``. ``dataset.py::load_corpus``
loads v1+v2+v3+v4+v5 transparently.

Usage:
    uv run python -m finetune.augment_v5

Env required:
    ANTHROPIC_API_KEY
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from finetune.augment import (
    SYSTEM,
    Sample,
    _parse_json_array,
    few_shots,
    load_rows,
    write_csv,
)
from finetune.augment_v4 import GUIDANCE
from finetune.main import _load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTH_CSV = REPO_ROOT / "synthetic_data.csv"
AUG_V1_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented.csv"
AUG_V2_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented_v2.csv"
AUG_V3_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented_v3.csv"
AUG_V4_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented_v4.csv"
AUG_V5_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented_v5.csv"


# How many *additional* rows to generate per class.
TARGETS = {
    "CREDIT_CARD": 100,
    "NUMERIC_ID": 85,
    "TIME": 100,
    "PHONE_NUMBER": 85,
    "NO_ENTITY": 120,
}

# Per-call batch size. Keeps Claude responses well under 8192 max_tokens
# and gives us seed-level diversity across chunks.
BATCH_SIZE = 30
MAX_RETRIES_PER_CLASS = 8  # safety cap on the retry-while-short loop


# Same prompt skeleton as v4, with an extra "this is the Nth batch, vary
# from previous batches" nudge so the model gives us new examples per call.
USER_TEMPLATE = """\
Class: {cls}
Class guidance: {guidance}

Existing few-shot examples (do NOT copy verbatim — generate new variants):
{shots}

This is batch {batch_no} of {batch_total} for this class. Maximize diversity
versus the few-shots and versus any other batches you might have produced.
Vary the surrounding sentence, the speaker domain, the digit/word patterns,
and the embedded entity values. Avoid reusing the same area code / drug /
person name / order number / etc. across batches.

Generate {n} new training rows for the class above. Each row must be a JSON
object with these fields:

- "variant": short label for the sub-pattern (string)
- "prompt": OPTIONAL per-row formatting instruction. Default to "" unless the
  class guidance explicitly says some rows should carry an instruction.
- "input_text": the raw ASR transcript — all lowercase, no punctuation, words
  not digits, embedded in a natural surrounding sentence.
- "expected_output": the formatted transcript. EVERY word from input_text must
  appear in expected_output in the same order, with ONLY the relevant entity
  transformed. For NO_ENTITY rows, no entity is transformed; only
  capitalization + terminal punctuation are added.
- "difficulty": one of "basic", "edge", "adversarial".
- "domain": one of "generic", "contact_center", "finance", "voice_agent",
  "meeting", "medical".
- "notes": one-line note about what makes this row distinctive (or "").

Return a JSON array of {n} objects, nothing else — no prose, no code fences."""


def generate_batch(
    client,
    *,
    cls: str,
    n: int,
    existing: list[Sample],
    seed: int,
    batch_no: int,
    batch_total: int,
    id_offset: int,
) -> list[Sample]:
    shots = few_shots(existing, cls, n=6, seed=seed)
    user_msg = USER_TEMPLATE.format(
        cls=cls,
        guidance=GUIDANCE[cls],
        shots=shots if shots else "(no existing rows for this class — invent from guidance)",
        batch_no=batch_no,
        batch_total=batch_total,
        n=n,
    )
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    items = _parse_json_array(raw)

    existing_inputs = {r.input_text.strip().lower() for r in existing}
    out: list[Sample] = []
    for i, it in enumerate(items):
        inp = (it.get("input_text") or "").strip()
        exp = (it.get("expected_output") or "").strip()
        prompt = (it.get("prompt") or "").strip()
        if not inp or not exp:
            continue
        if inp.lower() in existing_inputs:
            continue
        if cls != "NO_ENTITY":
            if inp == exp:
                continue
        else:
            # Pass-through sanity: punctuation+case-stripped tokens must match,
            # so the model can't reword us into hallucinations.
            norm_in = "".join(c.lower() for c in inp if c.isalnum() or c.isspace()).split()
            norm_out = "".join(c.lower() for c in exp if c.isalnum() or c.isspace()).split()
            if norm_in != norm_out:
                continue
        sid = f"AUG5-{cls.replace('_', '-')}-{id_offset + i + 1:03d}-{seed}"
        out.append(
            Sample(
                id=sid,
                entity_class=cls,
                variant=str(it.get("variant", ""))[:60],
                prompt=prompt,
                input_text=inp,
                expected_output=exp,
                difficulty=str(it.get("difficulty", "basic"))[:32],
                domain=str(it.get("domain", "generic"))[:32],
                source="synthetic_augmented_v5",
                notes=str(it.get("notes", ""))[:200],
            )
        )
        existing_inputs.add(inp.lower())
    return out


def generate_for_class(
    client, *, cls: str, n_target: int, existing: list[Sample], base_seed: int
) -> list[Sample]:
    """Keep firing batches until we've kept ``n_target`` rows or we hit
    ``MAX_RETRIES_PER_CLASS`` without making forward progress."""
    kept: list[Sample] = []
    seed = base_seed
    batch_total_est = max(1, (n_target + BATCH_SIZE - 1) // BATCH_SIZE)
    batch_no = 1
    stalls = 0
    while len(kept) < n_target and stalls < MAX_RETRIES_PER_CLASS:
        remaining = n_target - len(kept)
        n_this = min(BATCH_SIZE, remaining)
        before = len(kept)
        new = generate_batch(
            client,
            cls=cls,
            n=n_this,
            existing=existing + kept,
            seed=seed,
            batch_no=batch_no,
            batch_total=batch_total_est,
            id_offset=len(kept),
        )
        kept.extend(new)
        print(
            f"    batch {batch_no} seed={seed}: requested {n_this}, kept {len(new)}; "
            f"cumulative {len(kept)} / {n_target}",
            flush=True,
        )
        if len(kept) == before:
            stalls += 1
        else:
            stalls = 0
        seed += 1
        batch_no += 1
    return kept


def main() -> int:
    _load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set.", file=sys.stderr)
        return 2
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    existing = load_rows(SYNTH_CSV)
    for p in (AUG_V1_CSV, AUG_V2_CSV, AUG_V3_CSV, AUG_V4_CSV):
        if p.exists():
            existing.extend(load_rows(p))
    print(f"Loaded {len(existing)} existing rows (synthetic + v1..v4)")

    new_rows: list[Sample] = []
    for cls, n in TARGETS.items():
        print(f"  generating {n} new rows for {cls} …", flush=True)
        out = generate_for_class(client, cls=cls, n_target=n, existing=existing, base_seed=50)
        print(f"    -> kept {len(out)} / {n} for {cls}")
        new_rows.extend(out)
        existing.extend(out)  # later classes dedup against earlier v5 output

    write_csv(new_rows, AUG_V5_CSV)
    print(f"Wrote {len(new_rows)} v5 augmented rows -> {AUG_V5_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
