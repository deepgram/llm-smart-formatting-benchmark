"""Roll up scored rows into per-model summary tables.

Reads ``scored.csv`` + the original ``responses.csv`` (for latency/cost)
and produces:

- ``summary.csv``    — one row per model with proportion metrics + Wilson 95% CIs.
- ``canonical.csv``  — pass/fail per model on the 9 CANONICAL-* rows.

Optional model metadata CSV (``models_metadata.csv``) is joined on ``model_id``
when provided, surfacing vendor / family / params / license / release_date /
architecture in the summary and enabling grouped tables in the report.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


# ----------------- Model metadata loading -----------------


METADATA_COLUMNS = (
    "model_id",
    "vendor",
    "family",
    "model_full_name",
    "params_total",
    "params_active",
    "architecture",
    "context_window",
    "license",
    "open_weight",
    "release_date",
)


def load_metadata(path: Path | None) -> pd.DataFrame:
    """Read models_metadata.csv. Returns empty DataFrame if path is missing.

    Only the columns we care about are kept; missing columns are filled with
    empty strings so downstream merges always succeed.
    """
    if path is None or not path.exists():
        return pd.DataFrame(columns=list(METADATA_COLUMNS))
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in METADATA_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[list(METADATA_COLUMNS)]


# ----------------- Wilson 95% CI -----------------


def wilson_ci(k: int, n: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Returns (lo, hi) at 95% confidence by default. ``n=0`` returns (0, 0).
    """
    if n <= 0:
        return 0.0, 0.0
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    lo = max(0.0, centre - half)
    hi = min(1.0, centre + half)
    return lo, hi


# ----------------- Schema for scored.csv extra columns -----------------


SCORE_COLUMNS: list[str] = [
    "exact_match",
    "regex_pass",
    "regex_check_used",
    "judge_accuracy",
    "judge_accuracy_reason",
    "judge_promptability",
    "judge_promptability_reason",
    "judge_catastrophic",
    "judge_hallucination",
    "judge_hallucination_reason",
    "methods_agree",
    "disagreement_kind",
    "judge_error",
    # Optional second-judge columns (e.g. gpt-5.5 cross-check of Opus).
    # Populated by `evaluator second-judge` or by `evaluator score
    # --judge2-model …`. Blank in legacy files; readers should treat blank
    # as "not yet judged by the secondary".
    "judge2_model",
    "judge2_accuracy",
    "judge2_accuracy_reason",
    "judge2_promptability",
    "judge2_promptability_reason",
    "judge2_catastrophic",
    "judge2_hallucination",
    "judge2_hallucination_reason",
    "judge2_error",
    "judges_agree",
]


def scored_csv_columns(input_columns: list[str]) -> list[str]:
    """Return the column order for scored.csv (responses cols + score cols)."""
    return list(input_columns) + [c for c in SCORE_COLUMNS if c not in input_columns]


# ----------------- Disagreement classification -----------------


def classify_disagreement(
    em: bool, regex_p: bool | None, judge_acc: str | None
) -> tuple[bool, str]:
    """Return (methods_agree, disagreement_kind).

    ``methods_agree`` is True when ``exact_match`` agrees with ``judge_accuracy == 'pass'``.
    ``disagreement_kind`` is None on agreement, otherwise a short label.
    """
    judge_pass = judge_acc == "pass"
    if em == judge_pass:
        # Exact-match agrees with judge; check regex if it ran.
        if regex_p is not None and regex_p != judge_pass:
            return False, "regex_judge_disagree"
        return True, ""
    if judge_pass and not em:
        return False, "judge_pass_em_fail"
    if em and not judge_pass:
        return False, "em_pass_judge_fail"
    return True, ""


# ----------------- Latency percentile helper -----------------


def _percentile(values: list[float], pct: float) -> float | None:
    """Inclusive linear-interpolation percentile (compatible with numpy default)."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * pct / 100.0
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    frac = pos - lo
    return s[lo] + (s[hi] - s[lo]) * frac


# ----------------- Per-model summary -----------------


@dataclass(frozen=True)
class ModelSummary:
    model_id: str
    total_rows: int
    em_pass: int
    judge_pass: int
    consensus_pass: int
    uncertain: int
    catastrophic: int
    canonical_pass: int
    canonical_total: int
    halluc_any: int
    halluc_fabricated: int
    refusals: int
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    latency_ttft_p50_ms: float | None
    cost_total_usd: float

    def to_row(self) -> dict[str, Any]:
        n = self.total_rows
        em_lo, em_hi = wilson_ci(self.em_pass, n)
        jp_lo, jp_hi = wilson_ci(self.judge_pass, n)
        cs_lo, cs_hi = wilson_ci(self.consensus_pass, n)
        un_lo, un_hi = wilson_ci(self.uncertain, n)
        ha_lo, ha_hi = wilson_ci(self.halluc_any, n)
        hf_lo, hf_hi = wilson_ci(self.halluc_fabricated, n)
        cost_per_correct = (
            self.cost_total_usd / self.judge_pass if self.judge_pass else None
        )
        return {
            "model_id": self.model_id,
            "total_rows": n,
            "acc_exact_match": _pct(self.em_pass, n),
            "acc_exact_match_lo": _pct_f(em_lo),
            "acc_exact_match_hi": _pct_f(em_hi),
            "acc_judge_pass": _pct(self.judge_pass, n),
            "acc_judge_pass_lo": _pct_f(jp_lo),
            "acc_judge_pass_hi": _pct_f(jp_hi),
            "acc_consensus": _pct(self.consensus_pass, n),
            "acc_consensus_lo": _pct_f(cs_lo),
            "acc_consensus_hi": _pct_f(cs_hi),
            "uncertain_bucket_pct": _pct(self.uncertain, n),
            "uncertain_bucket_pct_lo": _pct_f(un_lo),
            "uncertain_bucket_pct_hi": _pct_f(un_hi),
            "catastrophic_count": self.catastrophic,
            "canonical_pass_count": self.canonical_pass,
            "canonical_total": self.canonical_total,
            "hallucination_rate_any": _pct(self.halluc_any, n),
            "hallucination_rate_any_lo": _pct_f(ha_lo),
            "hallucination_rate_any_hi": _pct_f(ha_hi),
            "hallucination_rate_fabricated": _pct(self.halluc_fabricated, n),
            "hallucination_rate_fabricated_lo": _pct_f(hf_lo),
            "hallucination_rate_fabricated_hi": _pct_f(hf_hi),
            "refusal_count": self.refusals,
            "latency_p50_ms": _round(self.latency_p50_ms),
            "latency_p95_ms": _round(self.latency_p95_ms),
            "latency_ttft_p50_ms": _round(self.latency_ttft_p50_ms),
            "cost_total_usd": round(self.cost_total_usd, 6),
            "cost_per_correct_usd": (
                round(cost_per_correct, 6) if cost_per_correct is not None else None
            ),
        }


def _pct(k: int, n: int) -> float:
    return round(100.0 * k / n, 2) if n else 0.0


def _pct_f(p: float) -> float:
    return round(100.0 * p, 2)


def _round(x: float | None) -> float | None:
    return None if x is None else round(x, 1)


# ----------------- Aggregation entrypoints -----------------


def enrich_summary(
    summary: pd.DataFrame, metadata: pd.DataFrame
) -> pd.DataFrame:
    """Left-join model metadata onto a summary DataFrame on ``model_id``.

    Missing matches yield empty strings for metadata columns.
    """
    if summary.empty or metadata.empty:
        return summary
    cols_to_add = [c for c in METADATA_COLUMNS if c != "model_id"]
    merged = summary.merge(
        metadata[list(METADATA_COLUMNS)],
        on="model_id",
        how="left",
    )
    for c in cols_to_add:
        merged[c] = merged[c].fillna("")
    return merged


def aggregate_grouped(
    summary: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    group_field: str,
) -> pd.DataFrame:
    """Aggregate summary metrics by a metadata field (family, size_tier-derived,
    architecture, license, etc.). Returns one row per group with average
    judge-pass rate, total catastrophic count, total canonical pass count, and
    member count.
    """
    if summary.empty or metadata.empty or group_field not in metadata.columns:
        return pd.DataFrame()
    enriched = enrich_summary(summary, metadata)
    if group_field not in enriched.columns or enriched[group_field].eq("").all():
        return pd.DataFrame()
    grouped = enriched.groupby(group_field, dropna=False).agg(
        models=("model_id", "count"),
        acc_judge_pass_mean=("acc_judge_pass", "mean"),
        acc_exact_match_mean=("acc_exact_match", "mean"),
        canonical_pass_total=("canonical_pass_count", "sum"),
        catastrophic_total=("catastrophic_count", "sum"),
        cost_total_usd=("cost_total_usd", "sum"),
    ).reset_index()
    grouped["acc_judge_pass_mean"] = grouped["acc_judge_pass_mean"].round(2)
    grouped["acc_exact_match_mean"] = grouped["acc_exact_match_mean"].round(2)
    grouped["cost_total_usd"] = grouped["cost_total_usd"].round(4)
    grouped = grouped.sort_values("acc_judge_pass_mean", ascending=False)
    return grouped.reset_index(drop=True)


def aggregate_summary(scored: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame: one row per model_id with all summary metrics."""
    rows: list[dict[str, Any]] = []
    canonical_mask = scored["sample_id"].str.startswith("CANONICAL-")
    canonical_total = int(canonical_mask.sum() / max(scored["model_id"].nunique(), 1))
    for model_id, grp in scored.groupby("model_id"):
        n = len(grp)
        em_series = grp["exact_match"].astype(str).eq("True")
        judge_pass_series = grp["judge_accuracy"].eq("pass")
        em_pass = int(em_series.sum())
        judge_pass = int(judge_pass_series.sum())
        consensus = int((em_series & judge_pass_series).sum())
        uncertain = int(
            grp["disagreement_kind"].fillna("").astype(str).str.len().gt(0).sum()
        )
        catastrophic = int(grp["judge_catastrophic"].astype(str).eq("True").sum())
        halluc_any = int(
            grp["judge_hallucination"]
            .fillna("")
            .astype(str)
            .isin(["minor_addition", "dropped_content", "fabricated"])
            .sum()
        )
        halluc_fab = int(grp["judge_hallucination"].eq("fabricated").sum())
        refusal_mask = (
            grp["judge_accuracy"].eq("other")
            & grp["judge_accuracy_reason"]
            .fillna("")
            .str.contains(
                r"refus|cannot|won't|will not|decline",
                case=False,
                regex=True,
            )
        )
        refusals = int(refusal_mask.sum())
        canonical_pass = int(
            (
                grp["sample_id"].str.startswith("CANONICAL-")
                & judge_pass_series
            ).sum()
        )
        # Latency stats from responses fields (already merged into scored).
        lat_total = _floats(grp.get("latency_total_ms", pd.Series(dtype=str)))
        lat_ttft = _floats(grp.get("latency_ttft_ms", pd.Series(dtype=str)))
        cost_total = _floats(grp.get("cost_usd", pd.Series(dtype=str)))
        ms = ModelSummary(
            model_id=str(model_id),
            total_rows=n,
            em_pass=em_pass,
            judge_pass=judge_pass,
            consensus_pass=consensus,
            uncertain=uncertain,
            catastrophic=catastrophic,
            canonical_pass=canonical_pass,
            canonical_total=canonical_total,
            halluc_any=halluc_any,
            halluc_fabricated=halluc_fab,
            refusals=refusals,
            latency_p50_ms=_percentile(lat_total, 50),
            latency_p95_ms=_percentile(lat_total, 95),
            latency_ttft_p50_ms=_percentile(lat_ttft, 50),
            cost_total_usd=sum(cost_total),
        )
        rows.append(ms.to_row())
    out = pd.DataFrame(rows).sort_values("acc_judge_pass", ascending=False)
    return out.reset_index(drop=True)


def _floats(s: pd.Series) -> list[float]:
    out: list[float] = []
    for v in s.tolist():
        if v in (None, "", "nan"):
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def aggregate_canonical(scored: pd.DataFrame) -> pd.DataFrame:
    """One row per CANONICAL-* sample, columns are pass/fail per model.

    Returned columns: ``sample_id`` + one column per model with values
    "pass" or "fail" (under judge_accuracy).
    """
    canon = scored[scored["sample_id"].str.startswith("CANONICAL-")].copy()
    if canon.empty:
        return pd.DataFrame(columns=["sample_id"])
    canon["judge_pass"] = canon["judge_accuracy"].eq("pass")
    pivot = canon.pivot_table(
        index="sample_id",
        columns="model_id",
        values="judge_pass",
        aggfunc="first",
    )
    pivot = pivot.reset_index()
    for col in pivot.columns:
        if col == "sample_id":
            continue
        pivot[col] = pivot[col].map(lambda v: "pass" if bool(v) else "fail")
    # Stable sort by sample_id.
    pivot = pivot.sort_values("sample_id").reset_index(drop=True)
    return pivot


def per_class_accuracy(
    scored: pd.DataFrame, dataset_df: pd.DataFrame
) -> pd.DataFrame:
    """Per-entity-class judge_pass rate, indexed by model_id × entity_class."""
    if "entity_class" not in scored.columns:
        merged = scored.merge(
            dataset_df[["id", "entity_class"]],
            left_on="sample_id",
            right_on="id",
            how="left",
        )
    else:
        merged = scored
    merged["judge_pass"] = merged["judge_accuracy"].eq("pass")
    grouped = (
        merged.groupby(["model_id", "entity_class"])["judge_pass"]
        .agg(["sum", "count"])
        .reset_index()
    )
    grouped["pct"] = (grouped["sum"] / grouped["count"] * 100).round(1)
    return grouped


# ----------------- Output writers -----------------


def write_summary_csv(summary: pd.DataFrame, path: Path) -> None:
    summary.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def write_canonical_csv(canonical: pd.DataFrame, path: Path) -> None:
    canonical.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


__all__ = [
    "METADATA_COLUMNS",
    "ModelSummary",
    "SCORE_COLUMNS",
    "aggregate_canonical",
    "aggregate_grouped",
    "aggregate_summary",
    "classify_disagreement",
    "enrich_summary",
    "load_metadata",
    "per_class_accuracy",
    "scored_csv_columns",
    "wilson_ci",
    "write_canonical_csv",
    "write_summary_csv",
]
