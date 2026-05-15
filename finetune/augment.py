"""Generate additional synthetic training rows for thin entity classes.

Strategy: for each target class, sample 6 existing rows as few-shot examples
and ask Claude Opus 4.7 to produce N new rows in the same shape. We then
sanity-check the output (input != expected for transforming classes, no
duplicate inputs vs. the existing corpus, sane lengths) before appending to
``finetune/data/synthetic_augmented.csv``.

The augmented file uses the same column schema as ``synthetic_data.csv`` so
``finetune/dataset.py::load_corpus`` can merge it transparently.

Usage:
    uv run python -m finetune.augment

Env required:
    ANTHROPIC_API_KEY
"""

from __future__ import annotations

import csv
import json
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from finetune.main import _load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTH_CSV = REPO_ROOT / "synthetic_data.csv"
AUG_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented.csv"


# class -> (existing-row source for few-shot, how many new rows to generate)
TARGETS = {
    "DATE_INTERVAL": 18,
    "DRUG_WITH_DOSE": 14,
    "SSN": 14,
    "CREDIT_CARD": 8,
    "URL": 5,
}


@dataclass
class Sample:
    id: str
    entity_class: str
    variant: str
    prompt: str
    input_text: str
    expected_output: str
    difficulty: str
    domain: str
    source: str
    notes: str


GUIDANCE = {
    "DATE_INTERVAL": (
        "DATE_INTERVAL means a span of dates spoken in natural language, e.g. "
        "'january through march' -> 'January – March', 'from the fifth to the "
        "tenth of march' -> 'March 5 – 10', or 'q one to q three twenty twenty "
        "five' -> 'Q1 – Q3 2025'. Cover month-to-month, weekday-to-weekday, "
        "quarter ranges, and explicit-year ranges. Avoid trivial duplicates of "
        "the few-shot examples."
    ),
    "DRUG_WITH_DOSE": (
        "DRUG_WITH_DOSE is a medication name + dose spoken in words. e.g. "
        "'metformin five hundred milligrams' -> 'metformin 500mg', 'lisinopril "
        "twenty mg' -> 'lisinopril 20mg'. Use realistic drug names (lisinopril, "
        "metformin, atorvastatin, amoxicillin, levothyroxine, hydrochlorothiazide, "
        "ozempic, sertraline, omeprazole, ibuprofen, acetaminophen, etc.) and "
        "realistic doses. Vary unit forms: mg, mcg, g, ml, units."
    ),
    "SSN": (
        "SSN is a 9-digit US Social Security Number spoken digit by digit, e.g. "
        "'one two three four five six seven eight nine' -> '123-45-6789'. Include "
        "rows with spoken 'oh' for zero, and include some with formatting prompts "
        "like 'Redact SSN as XXX-XX-####' (in which case expected is 'XXX-XX-####' "
        "filled with only the last 4 digits). Vary the surrounding sentence."
    ),
    "CREDIT_CARD": (
        "CREDIT_CARD is a 15- or 16-digit card number spoken in word groups, e.g. "
        "'four three two one nine eight seven six one two three four five six "
        "seven eight' -> '4321987612345678'. The MUST keep all digits in order. "
        "Half the rows should use a formatting prompt 'Redact all but the last "
        "four digits as XXXX XXXX XXXX ####' — in that case expected output is "
        "'XXXX XXXX XXXX ####' with the last four real digits."
    ),
    "URL": (
        "URL is a spoken web address with 'dot' for periods and 'slash' or "
        "'forward slash' for /, e.g. 'visit our company dot com forward slash "
        "careers' -> 'visit ourcompany.com/careers'. Lowercase, no spaces around "
        "dots or slashes. Cover .com, .io, .net, .org, .co, .dev TLDs and "
        "include subdomain and path variants."
    ),
}


SYSTEM = (
    "You generate synthetic training rows for a transcript-formatting "
    "benchmark. Each row simulates a spoken ASR transcript and the formatted "
    "post-processing output. Be diverse and realistic; do not duplicate the "
    "few-shot examples. Output strict JSON only."
)


USER_TEMPLATE = """\
Class: {cls}
Class guidance: {guidance}

Existing few-shot examples (do NOT copy verbatim — generate new variants):
{shots}

Generate {n} new training rows for the class above. Each row must be a JSON
object with these fields:

- "variant": short label for the sub-pattern (string)
- "prompt": OPTIONAL per-row formatting instruction. Use "" for ~70% of rows;
  use a realistic customer instruction for ~30% (e.g. redaction, render-as-digits,
  E.164 for phones, etc.).
- "input_text": the raw ASR transcript — all lowercase, no punctuation, words
  not digits, in a natural surrounding sentence (not just the bare entity).
- "expected_output": the formatted transcript. EVERY word from input_text must
  appear in expected_output in the same order, with ONLY the entity transformed.
- "difficulty": one of "basic", "edge", "adversarial" (mostly "basic" or "edge").
- "domain": one of "generic", "contact_center", "finance", "voice_agent",
  "meeting", "medical".
- "notes": optional one-line note about what makes this row distinctive (or "").

Return a JSON array of {n} objects, nothing else — no prose, no code fences."""


def load_rows(path: Path) -> list[Sample]:
    out: list[Sample] = []
    with path.open() as f:
        for r in csv.DictReader(f):
            out.append(
                Sample(
                    id=r.get("id", ""),
                    entity_class=r.get("entity_class", ""),
                    variant=r.get("variant", ""),
                    prompt=r.get("prompt", ""),
                    input_text=r.get("input_text", ""),
                    expected_output=r.get("expected_output", ""),
                    difficulty=r.get("difficulty", ""),
                    domain=r.get("domain", ""),
                    source=r.get("source", ""),
                    notes=r.get("notes", ""),
                )
            )
    return out


def few_shots(rows: list[Sample], cls: str, n: int, seed: int) -> str:
    pool = [r for r in rows if r.entity_class == cls]
    rng = random.Random(seed)
    picks = rng.sample(pool, min(n, len(pool)))
    out = []
    for r in picks:
        out.append(
            json.dumps(
                {
                    "variant": r.variant,
                    "prompt": r.prompt,
                    "input_text": r.input_text,
                    "expected_output": r.expected_output,
                    "difficulty": r.difficulty,
                    "domain": r.domain,
                    "notes": r.notes,
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(out)


def _parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    # Strip code fences if the model added them despite instructions.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def generate_for_class(client, *, cls: str, n: int, existing: list[Sample], seed: int) -> list[Sample]:
    shots = few_shots(existing, cls, n=6, seed=seed)
    user_msg = USER_TEMPLATE.format(
        cls=cls,
        guidance=GUIDANCE[cls],
        shots=shots,
        n=n,
    )
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
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
        # Tolerate redacted CC/SSN where input!=expected but expected mostly !=input.
        if inp == exp and cls not in {"ADVERSARIAL"}:
            # Suspicious — entity should have transformed.
            continue
        sid = f"AUG-{cls.replace('_','-')}-{i+1:03d}-{seed}"
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
                source="synthetic_augmented",
                notes=str(it.get("notes", ""))[:200],
            )
        )
        existing_inputs.add(inp.lower())
    return out


def write_csv(rows: list[Sample], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id", "entity_class", "variant", "prompt", "input_text",
        "expected_output", "difficulty", "domain", "source", "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({
                "id": r.id, "entity_class": r.entity_class, "variant": r.variant,
                "prompt": r.prompt, "input_text": r.input_text,
                "expected_output": r.expected_output, "difficulty": r.difficulty,
                "domain": r.domain, "source": r.source, "notes": r.notes,
            })


def main() -> int:
    _load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set.", file=sys.stderr)
        return 2
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    existing = load_rows(SYNTH_CSV)
    print(f"Loaded {len(existing)} existing rows from {SYNTH_CSV.name}")

    new_rows: list[Sample] = []
    for cls, n in TARGETS.items():
        print(f"  generating {n} new rows for {cls} …", flush=True)
        out = generate_for_class(client, cls=cls, n=n, existing=existing, seed=42)
        print(f"    kept {len(out)} / {n}")
        new_rows.extend(out)

    write_csv(new_rows, AUG_CSV)
    print(f"Wrote {len(new_rows)} augmented rows -> {AUG_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
