"""Programmatic scorers — exact-match and regex canonical-form checks.

Both methods are free, deterministic, and trivially testable. Run on every
row before the LLM-judge passes.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


# ----------------- Method 1: exact match -----------------


_WS_RE = re.compile(r"\s+")


def _normalize(s: str) -> str:
    """Normalize whitespace and unicode form for comparison.

    - NFC unicode normalization (so e.g. precomposed vs decomposed chars match)
    - Collapse internal whitespace to single spaces
    - Strip leading/trailing whitespace
    """
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", str(s))
    s = _WS_RE.sub(" ", s).strip()
    return s


def exact_match(actual: str, expected: str) -> bool:
    return _normalize(actual) == _normalize(expected)


# ----------------- Method 2: regex canonical-form checks -----------------
#
# A "regex check" only fires when the formatting prompt asks for a strict
# canonical form. For each row we identify which check (if any) applies based
# on (entity_class, formatting_prompt), then we apply the check to the
# candidate's actual_output. We do NOT validate the entire output — only that
# it contains the canonical-form entity in the right shape.
#
# When no check applies, callers should set both columns to None (NOT False) —
# distinguishing "not checked" from "checked and failed".


@dataclass(frozen=True)
class RegexCheck:
    name: str
    pattern: re.Pattern[str]
    description: str


_CHECKS: dict[str, RegexCheck] = {
    "iso8601_date": RegexCheck(
        name="iso8601_date",
        pattern=re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
        description="ISO 8601 YYYY-MM-DD date present.",
    ),
    "e164_phone": RegexCheck(
        name="e164_phone",
        pattern=re.compile(r"\+\d{6,15}"),
        description="E.164 phone (+ followed by 6-15 digits).",
    ),
    "us_dashed_phone": RegexCheck(
        name="us_dashed_phone",
        pattern=re.compile(r"(?:\d{3}-\d{3}-\d{4})|(?:\(\d{3}\) \d{3}-\d{4})"),
        description="US-dashed or parenthesized phone format.",
    ),
    "ssn_redaction": RegexCheck(
        name="ssn_redaction",
        pattern=re.compile(r"XXX-XX-\d{4}"),
        description="SSN redacted to XXX-XX-####.",
    ),
    "time_24h": RegexCheck(
        name="time_24h",
        pattern=re.compile(r"\b\d{2}:\d{2}\b(?!\s*[AaPp]\.?[Mm])"),
        description="24-hour HH:MM time, no AM/PM suffix.",
    ),
}


def pick_regex_check(entity_class: str, formatting_prompt: str) -> RegexCheck | None:
    """Return the regex check that applies to this row, or None.

    Heuristic match on entity_class + formatting_prompt text. Order matters
    only in that we pick the first specific match found.
    """
    cls = (entity_class or "").upper()
    p = (formatting_prompt or "").lower()
    if not p:
        return None

    if cls == "DATE" and ("iso 8601" in p or "iso8601" in p or "yyyy-mm-dd" in p):
        return _CHECKS["iso8601_date"]
    if cls == "PHONE_NUMBER" and ("e.164" in p or "e164" in p):
        return _CHECKS["e164_phone"]
    if cls == "PHONE_NUMBER" and (
        "us-dashed" in p or "dashed" in p or "###-###-####" in p or "(###) ###-####" in p
    ):
        return _CHECKS["us_dashed_phone"]
    if cls == "SSN" and ("redact" in p or "xxx-xx" in p):
        return _CHECKS["ssn_redaction"]
    if cls == "TIME" and ("24-hour" in p or "24 hour" in p or "hh:mm" in p):
        return _CHECKS["time_24h"]
    return None


def regex_pass(
    actual: str, entity_class: str, formatting_prompt: str
) -> tuple[bool | None, str | None]:
    """Return (pass, check_used). (None, None) if no check applies.

    For a check to pass, the regex must match somewhere in ``actual``. Note
    that for the 24h-time check we also require the absence of an AM/PM
    suffix — the regex enforces this via negative lookahead.
    """
    check = pick_regex_check(entity_class, formatting_prompt)
    if check is None:
        return None, None
    if not actual:
        return False, check.name
    found = bool(check.pattern.search(actual))
    return found, check.name


__all__ = [
    "RegexCheck",
    "exact_match",
    "pick_regex_check",
    "regex_pass",
]
