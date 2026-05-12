"""Stratified subset selector for the prompt-iteration loop.

Returns a deterministic subset of synthetic_data.csv covering all 9
``customer_canonical`` rows + a fixed number of ``adversarial`` rows + a
small per-class sample of the remaining synthetic rows + all ``messy``
multi-entity rows parsed from ``messy_prompts.txt``. The subset is seeded
so it is stable across iterations — that is essential, otherwise score
deltas across iterations would conflate prompt change with sample change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class Sample:
    sample_id: str
    entity_class: str
    variant: str
    formatting_prompt: str
    input_text: str
    expected_output: str
    source: str
    difficulty: str


# ----------------- messy_prompts.txt parser -----------------


_HEADER_RE = re.compile(r"^\s*\[(\d+)\]\s*([^|]+?)\s*\|\s*(.+?)\s*$")


def parse_messy_prompts(path: Path) -> list[Sample]:
    """Parse the freeform ``messy_prompts.txt`` file into Sample rows.

    File format (per block, separated by ``---``):

        [N] domain | ENTITY_A ENTITY_B ...
        INPUT: <one-line ASR transcript>
        PROMPT: <optional formatting instruction>
        EXPECTED: <one-line expected output>
    """
    if not path.exists():
        return []
    blocks = path.read_text(encoding="utf-8").split("\n---\n")
    out: list[Sample] = []
    for raw in blocks:
        header = None
        domain = ""
        classes = ""
        input_text = ""
        prompt_text = ""
        expected = ""
        for line in raw.splitlines():
            line = line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            m = _HEADER_RE.match(line)
            if m and header is None:
                header = m.group(1)
                domain = m.group(2).strip()
                classes = m.group(3).strip().replace(" ", "|")
                continue
            if line.startswith("INPUT:"):
                input_text = line[len("INPUT:"):].strip()
            elif line.startswith("PROMPT:"):
                prompt_text = line[len("PROMPT:"):].strip()
            elif line.startswith("EXPECTED:"):
                expected = line[len("EXPECTED:"):].strip()
        if header is None or not input_text or not expected:
            continue
        out.append(
            Sample(
                sample_id=f"MESSY-{int(header):03d}",
                entity_class=classes or "MIXED",
                variant=domain,
                formatting_prompt=prompt_text,
                input_text=input_text,
                expected_output=expected,
                source="messy",
                difficulty="messy",
            )
        )
    return out


def build_subset(
    dataset_path: Path,
    *,
    n_per_class: int = 3,
    n_adversarial: int = 6,
    seed: int = 42,
    include_messy: bool = True,
    messy_path: Path | None = None,
) -> list[Sample]:
    df = pd.read_csv(dataset_path, dtype=str, keep_default_na=False)

    canonical = df[df["source"] == "customer_canonical"]

    adv_pool = df[df["source"] == "adversarial"]
    n_adv = min(n_adversarial, len(adv_pool))
    adversarial = adv_pool.sample(n=n_adv, random_state=seed) if n_adv else adv_pool.iloc[0:0]

    rest = df[~df["source"].isin(["customer_canonical", "adversarial"])]
    pieces: list[pd.DataFrame] = [canonical, adversarial]
    for cls in sorted(rest["entity_class"].unique()):
        sub = rest[rest["entity_class"] == cls]
        if len(sub) <= n_per_class:
            pieces.append(sub)
        else:
            pieces.append(sub.sample(n=n_per_class, random_state=seed))

    out = pd.concat(pieces).drop_duplicates(subset=["id"]).sort_values("id")
    samples: list[Sample] = []
    for _, r in out.iterrows():
        samples.append(
            Sample(
                sample_id=str(r["id"]),
                entity_class=str(r.get("entity_class", "")),
                variant=str(r.get("variant", "")),
                formatting_prompt=str(r.get("prompt", "") or ""),
                input_text=str(r.get("input_text", "") or ""),
                expected_output=str(r.get("expected_output", "") or ""),
                source=str(r.get("source", "")),
                difficulty=str(r.get("difficulty", "")),
            )
        )

    if include_messy:
        if messy_path is None:
            messy_path = dataset_path.parent / "messy_prompts.txt"
        samples.extend(parse_messy_prompts(messy_path))
    return samples


def build_determinism_subset(
    dataset_path: Path,
    *,
    target_n: int = 50,
    seed: int = 42,
) -> list[Sample]:
    """Pick a fixed 50-row subset for determinism eval.

    All ``customer_canonical`` rows + a deterministic spread across the
    remaining ``entity_class`` values. Stable across calls (``seed``).
    """
    df = pd.read_csv(dataset_path, dtype=str, keep_default_na=False)

    canonical = df[df["source"] == "customer_canonical"]
    rest = df[df["source"] != "customer_canonical"]
    classes = sorted(rest["entity_class"].unique())

    remaining = max(0, target_n - len(canonical))
    if classes and remaining > 0:
        per_class = max(1, remaining // len(classes))
    else:
        per_class = 0

    pieces: list[pd.DataFrame] = [canonical]
    used_ids: set[str] = set(canonical["id"].tolist())
    for cls in classes:
        sub = rest[(rest["entity_class"] == cls) & (~rest["id"].isin(used_ids))]
        if sub.empty:
            continue
        n = min(per_class, len(sub))
        pick = sub.sample(n=n, random_state=seed)
        used_ids.update(pick["id"].tolist())
        pieces.append(pick)

    out = pd.concat(pieces).drop_duplicates(subset=["id"]).sort_values("id")

    # Top up to target_n if we under-shot, draw from any unused rest rows.
    if len(out) < target_n:
        leftover = rest[~rest["id"].isin(out["id"])]
        if not leftover.empty:
            top_up = leftover.sample(
                n=min(target_n - len(out), len(leftover)),
                random_state=seed,
            )
            out = pd.concat([out, top_up]).drop_duplicates(subset=["id"]).sort_values("id")

    # Trim to target_n if we over-shot — keep all canonical first.
    if len(out) > target_n:
        keep_canonical = out[out["source"] == "customer_canonical"]
        non_canonical = out[out["source"] != "customer_canonical"]
        keep_other = non_canonical.head(target_n - len(keep_canonical))
        out = pd.concat([keep_canonical, keep_other]).sort_values("id")

    samples: list[Sample] = []
    for _, r in out.iterrows():
        samples.append(
            Sample(
                sample_id=str(r["id"]),
                entity_class=str(r.get("entity_class", "")),
                variant=str(r.get("variant", "")),
                formatting_prompt=str(r.get("prompt", "") or ""),
                input_text=str(r.get("input_text", "") or ""),
                expected_output=str(r.get("expected_output", "") or ""),
                source=str(r.get("source", "")),
                difficulty=str(r.get("difficulty", "")),
            )
        )
    return samples


__all__ = ["Sample", "build_subset", "build_determinism_subset", "parse_messy_prompts"]
