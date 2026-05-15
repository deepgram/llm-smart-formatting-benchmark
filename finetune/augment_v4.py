"""Round-4 synthetic-data augmentation targeting the classes still weak after
the v2 / v3 rounds.

Round 1 (``augment.py``):   DATE_INTERVAL / DRUG_WITH_DOSE / SSN / CREDIT_CARD / URL.
Round 2 (``augment_v2.py``):ADVERSARIAL / CARDINAL / EMAIL_ADDRESS / PERCENT / DATE_INTERVAL.
Round 3 (existing v3 CSV):  more ADVERSARIAL / CARDINAL / DATE_INTERVAL / EMAIL_ADDRESS / PERCENT.

Round 4 targets what's *still* weak in the v2-c1 FT runs (judge_pass %):

  - CREDIT_CARD     16.7% (Llama-3.2-3B), 16.7% (Gemma-3-1B), 33.3% (Qwen3.5-9B)
  - NUMERIC_ID      30 – 50% across the three FT models
  - TIME            50% across all FT models
  - PHONE_NUMBER    50 – 80%

…plus a brand-new ``NO_ENTITY`` bucket of "pass-through" rows: spoken
transcripts that contain *no* formattable entity. The FT models hallucinate
heavily (21–30% any-hallucination rate). Teaching the model that "if there's
nothing to format, preserve the words" should reduce that.

Writes ``finetune/data/synthetic_augmented_v4.csv``. ``dataset.py::load_corpus``
loads v1+v2+v3+v4 transparently.

Usage:
    uv run python -m finetune.augment_v4

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
from finetune.main import _load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTH_CSV = REPO_ROOT / "synthetic_data.csv"
AUG_V1_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented.csv"
AUG_V2_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented_v2.csv"
AUG_V3_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented_v3.csv"
AUG_V4_CSV = Path(__file__).resolve().parent / "data" / "synthetic_augmented_v4.csv"


TARGETS = {
    "CREDIT_CARD": 25,
    "NUMERIC_ID": 25,
    "TIME": 20,
    "PHONE_NUMBER": 25,
    "NO_ENTITY": 30,
}


GUIDANCE = {
    "CREDIT_CARD": (
        "Round-3 CREDIT_CARD — the FT models routinely drop or reorder digits "
        "on long spoken card numbers. Focus aggressively on digit-preservation. "
        "Cover ALL of these patterns:\n"
        "  - 16-digit Visa/MC ('four three two one nine eight seven six one two "
        "three four five six seven eight' -> '4321 9876 1234 5678')\n"
        "  - 15-digit Amex (groups of 4-6-5: '3782 822463 10005')\n"
        "  - spoken 'oh' for zero ('four oh oh oh ...' -> '4000 ...')\n"
        "  - 'double seven', 'triple two' chunked phrasing ('four three double "
        "seven' -> '4377')\n"
        "  - card spoken as four groups of four with 'space' between ('four "
        "three two one space nine eight seven six space ...')\n"
        "  - card embedded in natural sentence ('charge my card four three two "
        "one ... for two hundred dollars' — note MONEY entity also present, "
        "format BOTH)\n"
        "Output formatting: separate groups of 4 digits with a single space "
        "(default), unless a per-row prompt overrides.\n"
        "About 40% of rows should use a per-row 'prompt' instructing redaction: "
        "'Redact all but the last four digits as XXXX XXXX XXXX ####' — then the "
        "expected_output is 'XXXX XXXX XXXX ####' with ONLY the last four real "
        "digits filled in. Verify the digit count of every row before emitting: "
        "16 digits in must produce 16 digits out (or 4 visible digits if "
        "redacted)."
    ),
    "NUMERIC_ID": (
        "Round-3 NUMERIC_ID — the failure mode is the model dropping or "
        "transposing digits in long spoken IDs. Generate 25 rows spanning:\n"
        "  - order numbers ('order number one two three four five six seven' "
        "-> 'order number 1234567')\n"
        "  - account numbers (8 – 12 digits)\n"
        "  - confirmation codes (alphanumeric: 'confirmation code alpha bravo "
        "seven seven two' -> 'confirmation code AB772' — letters get uppercased)\n"
        "  - tracking numbers (UPS/FedEx-style, 12 – 20 digits)\n"
        "  - case/ticket IDs ('case number cee ar em dash one five seven seven' "
        "-> 'case number CRM-1577')\n"
        "  - patient/MRN IDs ('medical record number five five one two seven "
        "eight nine')\n"
        "Patterns to cover: spoken 'oh' for 0, repeated digits as 'double X' "
        "/ 'triple X', mixed letter/digit IDs where each letter is spoken "
        "(NATO or simply 'a' / 'b' / 'c'), and IDs with literal 'dash' between "
        "groups. The model MUST preserve digit count exactly — never round, "
        "never collapse repeats. Inputs are spoken-style (all lowercase, no "
        "punctuation, words for digits)."
    ),
    "TIME": (
        "Round-3 TIME — only 50% on every FT model. Generate 20 rows covering "
        "the patterns the models miss:\n"
        "  - 12-hour with am/pm ('three thirty pee em' -> '3:30 PM', 'nine "
        "fifteen ay em' -> '9:15 AM')\n"
        "  - 24-hour military ('fourteen hundred hours' -> '14:00', 'oh nine "
        "thirty' -> '09:30')\n"
        "  - quarter / half ('quarter past three' -> '3:15', 'half past nine' "
        "-> '9:30', 'quarter to five' -> '4:45')\n"
        "  - noon/midnight ('twelve noon' -> '12:00 PM', 'midnight' -> "
        "'12:00 AM')\n"
        "  - relative seconds ('thirty seconds past two' -> '2:00:30')\n"
        "  - time zones ('three pee em eastern' -> '3:00 PM ET', 'nine ay em "
        "pacific time' -> '9:00 AM PT')\n"
        "  - ranges (handled by DATE_INTERVAL — skip here)\n"
        "Use AM/PM uppercase with a space ('3:30 PM' not '3:30pm'). For 24-hour "
        "always use 'HH:MM'. Embed in natural sentences (meeting reminders, "
        "appointment confirmations, voicemail prompts)."
    ),
    "PHONE_NUMBER": (
        "Round-3 PHONE_NUMBER — generate 25 rows covering the patterns the FT "
        "models fumble:\n"
        "  - US 10-digit ('two oh two five five five oh one three four' -> "
        "'(202) 555-0134')\n"
        "  - US with country code ('one eight hundred five five five one two "
        "one two' -> '1-800-555-1212')\n"
        "  - extensions ('two oh two five five five oh one three four "
        "extension forty seven' -> '(202) 555-0134 ext. 47')\n"
        "  - international with country code ('plus four four two oh seven "
        "nine four six oh nine five eight' -> '+44 20 7946 0958')\n"
        "  - vanity numbers spoken as letters ('one eight hundred flowers' -> "
        "'1-800-FLOWERS' if all letters; preserve numeric form otherwise)\n"
        "  - spoken with 'dash' / 'hyphen' between groups\n"
        "  - per-row prompt asking for E.164 format ('Format phone numbers as "
        "E.164') — then expected is '+12025550134', no spaces/dashes\n"
        "Mix the default (US '(NNN) NNN-NNNN') with E.164-prompted rows roughly "
        "70/30. Always preserve digit count exactly. Avoid US area codes 555 "
        "+ 555 + XXXX duplicates — use 555-01XX range for fake examples and "
        "vary real-looking area codes (202, 415, 312, 617, 206, 305)."
    ),
    "NO_ENTITY": (
        "NO_ENTITY rows teach the model the most important pass-through "
        "behaviour: when a transcript contains NO formattable entity, the "
        "model must preserve every word and add ONLY sentence-level "
        "capitalization and punctuation. This combats hallucination — the FT "
        "models currently fabricate entities at 21 – 30% rates.\n\n"
        "Each row:\n"
        "  - input_text: a realistic spoken-style transcript (all lowercase, "
        "no punctuation, words not digits) that contains NO entity worth "
        "formatting — no money, no dates, no times, no phone numbers, no IDs, "
        "no addresses, no emails, no URLs, no percentages, no SSNs, no card "
        "numbers, no drug doses.\n"
        "  - expected_output: the SAME words, in the SAME order, with proper "
        "sentence capitalization (capitalize first word, capitalize proper "
        "nouns if naturally present) and terminal punctuation (period, "
        "question mark). Do NOT invent any entity. Do NOT reword. Do NOT "
        "remove filler words like 'um', 'uh', 'you know' — preserve them "
        "verbatim.\n\n"
        "Examples:\n"
        "  input:  'we should probably reschedule the meeting'\n"
        "  output: 'We should probably reschedule the meeting.'\n\n"
        "  input:  'can you transfer me to a real person please'\n"
        "  output: 'Can you transfer me to a real person please?'\n\n"
        "  input:  'um yeah i think that works for me'\n"
        "  output: 'Um, yeah, I think that works for me.'\n\n"
        "Vary the domain (contact_center, voice_agent, meeting, medical, "
        "generic). Vary sentence length from 5 words to 30 words. About 20% "
        "of rows should be multi-sentence (two short utterances). About 10% "
        "should contain proper nouns ('john', 'sarah', 'amazon', 'chase') "
        "that get capitalized but NOT classified as entities. Use difficulty "
        "'basic' for all rows."
    ),
}


# Same wrapper as v2; just calls Claude with the v3 guidance.
USER_TEMPLATE = """\
Class: {cls}
Class guidance: {guidance}

Existing few-shot examples (do NOT copy verbatim — generate new variants):
{shots}

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


def generate_for_class(
    client, *, cls: str, n: int, existing: list[Sample], seed: int
) -> list[Sample]:
    # For NO_ENTITY there are no existing rows to seed few-shots — fall back to
    # an empty list, which `few_shots` handles via `min(n, len(pool))`.
    shots = few_shots(existing, cls, n=6, seed=seed)
    user_msg = USER_TEMPLATE.format(
        cls=cls,
        guidance=GUIDANCE[cls],
        shots=shots if shots else "(no existing rows for this class — invent from guidance)",
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
        # NO_ENTITY rows commonly differ only in capitalization + punctuation,
        # so `inp == exp` (case-insensitive, punctuation-stripped) is fine.
        # For every other v3 class the entity must transform, so reject
        # identical-after-normalization rows.
        if cls != "NO_ENTITY":
            if inp == exp:
                continue
        else:
            # Sanity: the punctuation/case-stripped texts should match
            # token-by-token (we don't want the model rewording the
            # pass-through example).
            norm_in = "".join(c.lower() for c in inp if c.isalnum() or c.isspace()).split()
            norm_out = "".join(c.lower() for c in exp if c.isalnum() or c.isspace()).split()
            if norm_in != norm_out:
                continue
        sid = f"AUG4-{cls.replace('_', '-')}-{i + 1:03d}-{seed}"
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
                source="synthetic_augmented_v4",
                notes=str(it.get("notes", ""))[:200],
            )
        )
        existing_inputs.add(inp.lower())
    return out


def main() -> int:
    _load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set.", file=sys.stderr)
        return 2
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Combine canonical synthetic + v1 + v2 + v3 so v4 dedups against everything.
    existing = load_rows(SYNTH_CSV)
    if AUG_V1_CSV.exists():
        existing.extend(load_rows(AUG_V1_CSV))
    if AUG_V2_CSV.exists():
        existing.extend(load_rows(AUG_V2_CSV))
    if AUG_V3_CSV.exists():
        existing.extend(load_rows(AUG_V3_CSV))
    print(f"Loaded {len(existing)} existing rows (synthetic + v1 + v2 + v3)")

    new_rows: list[Sample] = []
    for cls, n in TARGETS.items():
        print(f"  generating {n} new rows for {cls} …", flush=True)
        out = generate_for_class(client, cls=cls, n=n, existing=existing, seed=44)
        print(f"    kept {len(out)} / {n}")
        new_rows.extend(out)
        existing.extend(out)  # later classes dedup against earlier v4 output

    write_csv(new_rows, AUG_V4_CSV)
    print(f"Wrote {len(new_rows)} v4 augmented rows -> {AUG_V4_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
