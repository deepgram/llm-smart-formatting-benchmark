"""Render the evaluator's markdown report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from evaluator.aggregate import (
    METADATA_COLUMNS,
    aggregate_grouped,
    enrich_summary,
    per_class_accuracy,
)


def _fmt_pct_with_ci(row: dict[str, Any], base: str) -> str:
    p = row.get(base)
    lo = row.get(f"{base}_lo")
    hi = row.get(f"{base}_hi")
    if p is None:
        return "—"
    if lo is None or hi is None:
        return f"{p:.1f}%"
    return f"{p:.1f}% [{lo:.1f}-{hi:.1f}]"


def _fmt_ms(v: float | None) -> str:
    return "—" if v is None or pd.isna(v) else f"{v:.0f} ms"


def _fmt_dollars(v: float | None) -> str:
    return "—" if v is None or pd.isna(v) else f"${v:.4f}"


def _meta(row: dict[str, Any], col: str) -> str:
    v = row.get(col)
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    s = str(v)
    return s if s else "—"


def headline_table(summary: pd.DataFrame) -> str:
    """Markdown table sorted by acc_judge_pass desc.

    If ``summary`` carries metadata columns (vendor, family, params_total,
    license, architecture), they are included in the table. Otherwise it falls
    back to the lean original layout.
    """
    if summary.empty:
        return "_No models scored._"
    has_meta = "vendor" in summary.columns and "params_total" in summary.columns
    if has_meta:
        cols = [
            "Model",
            "Vendor",
            "Params (active/total)",
            "Arch",
            "License",
            "Judge pass [95% CI]",
            "Exact match",
            "Canonical",
            "Catastrophic",
            "Halluc. any",
            "Latency p50",
            "Cost (USD)",
        ]
    else:
        cols = [
            "Model",
            "Judge pass [95% CI]",
            "Exact match",
            "Canonical",
            "Catastrophic",
            "Halluc. any",
            "Latency p50",
            "Cost (USD)",
        ]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in summary.iterrows():
        row = r.to_dict()
        em = (
            f"{row['acc_exact_match']:.1f}%"
            if row.get("acc_exact_match") is not None
            else "—"
        )
        canon = f"{int(row['canonical_pass_count'])}/{int(row['canonical_total'])}"
        cat = str(int(row["catastrophic_count"]))
        halluc = (
            f"{row['hallucination_rate_any']:.1f}%"
            if row.get("hallucination_rate_any") is not None
            else "—"
        )
        cells = [f"`{row['model_id']}`"]
        if has_meta:
            params = f"{_meta(row, 'params_active')} / {_meta(row, 'params_total')}"
            cells += [
                _meta(row, "vendor"),
                params,
                _meta(row, "architecture"),
                _meta(row, "license"),
            ]
        cells += [
            _fmt_pct_with_ci(row, "acc_judge_pass"),
            em,
            canon,
            cat,
            halluc,
            _fmt_ms(row.get("latency_p50_ms")),
            _fmt_dollars(row.get("cost_total_usd")),
        ]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def canonical_grid(canonical: pd.DataFrame) -> str:
    """Markdown table: rows = CANONICAL ids, cols = models, cells = pass/fail glyph."""
    if canonical.empty:
        return "_No canonical samples found._"
    model_cols = [c for c in canonical.columns if c != "sample_id"]
    header = ["Sample ID"] + model_cols
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for _, r in canonical.iterrows():
        cells = [f"`{r['sample_id']}`"]
        for m in model_cols:
            v = r.get(m, "")
            cells.append("PASS" if v == "pass" else "FAIL")
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def per_class_table(scored: pd.DataFrame, dataset_df: pd.DataFrame) -> str:
    pc = per_class_accuracy(scored, dataset_df)
    if pc.empty:
        return "_No per-class data._"
    pivot = pc.pivot_table(
        index="entity_class", columns="model_id", values="pct", aggfunc="first"
    ).fillna(0.0)
    pivot = pivot.round(1)
    cols = ["entity_class"] + list(pivot.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for cls, row in pivot.iterrows():
        cells = [str(cls)] + [f"{v:.1f}%" for v in row.tolist()]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def disagreement_table(scored: pd.DataFrame, *, top_n: int = 20) -> str:
    """Top-N rows where exact-match and judge disagree, ordered by class+id."""
    mask = scored["disagreement_kind"].fillna("").astype(str).str.len().gt(0)
    disagree = scored[mask].copy()
    if disagree.empty:
        return "_No disagreements between methods._"
    cols = [
        "model_id",
        "sample_id",
        "exact_match",
        "judge_accuracy",
        "disagreement_kind",
        "expected_output",
        "actual_output",
    ]
    available = [c for c in cols if c in disagree.columns]
    rows = disagree[available].head(top_n).to_dict(orient="records")
    header = ["model", "sample", "EM", "judge", "kind", "expected", "actual"]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for r in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{r.get('model_id', '')}`",
                    f"`{r.get('sample_id', '')}`",
                    str(r.get("exact_match", "")),
                    str(r.get("judge_accuracy", "")),
                    str(r.get("disagreement_kind", "")),
                    _truncate(str(r.get("expected_output", "")), 80),
                    _truncate(str(r.get("actual_output", "")), 80),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _truncate(s: str, n: int) -> str:
    s = s.replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def grouped_table(
    summary: pd.DataFrame, metadata: pd.DataFrame, *, group_field: str, label: str
) -> str:
    """Markdown table aggregating summary by a metadata field."""
    df = aggregate_grouped(summary, metadata, group_field=group_field)
    if df.empty:
        return f"_No {label} grouping available._"
    cols = [
        label,
        "models",
        "judge_pass_mean",
        "exact_match_mean",
        "canonical_pass_total",
        "catastrophic_total",
        "cost_total",
    ]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in df.iterrows():
        out.append(
            "| "
            + " | ".join(
                [
                    str(r[group_field]) or "—",
                    str(int(r["models"])),
                    f"{r['acc_judge_pass_mean']:.1f}%",
                    f"{r['acc_exact_match_mean']:.1f}%",
                    str(int(r["canonical_pass_total"])),
                    str(int(r["catastrophic_total"])),
                    _fmt_dollars(r["cost_total_usd"]),
                ]
            )
            + " |"
        )
    return "\n".join(out)


def open_weight_only_table(
    summary: pd.DataFrame, metadata: pd.DataFrame
) -> str:
    """Headline-style table restricted to open-weight models, sorted desc."""
    if summary.empty or metadata.empty:
        return "_No open-weight subset available._"
    enriched = enrich_summary(summary, metadata)
    if "open_weight" not in enriched.columns:
        return "_No open-weight metadata._"
    ow = enriched[enriched["open_weight"].astype(str).str.lower() == "true"]
    if ow.empty:
        return "_No open-weight models scored._"
    ow = ow.sort_values("acc_judge_pass", ascending=False)
    return headline_table(ow.reset_index(drop=True))


def render_report(
    *,
    run_id: str,
    summary: pd.DataFrame,
    canonical: pd.DataFrame,
    scored: pd.DataFrame,
    dataset_df: pd.DataFrame,
    judge_model: str,
    judge_cost_usd: float,
    metadata: pd.DataFrame | None = None,
) -> str:
    parts: list[str] = []
    parts.append(f"# Smart-formatting eval — run `{run_id}`")
    parts.append("")
    parts.append(f"Judge: `{judge_model}` — total judge cost: ${judge_cost_usd:.4f}")
    parts.append(
        f"Models: {summary['model_id'].nunique() if not summary.empty else 0} | "
        f"Rows scored: {len(scored)}"
    )
    parts.append("")

    enriched = summary
    has_meta = metadata is not None and not metadata.empty
    if has_meta:
        enriched = enrich_summary(summary, metadata)

    parts.append("## 1. Headline")
    parts.append("")
    parts.append(headline_table(enriched))
    parts.append("")

    if has_meta:
        parts.append("## 2. Open-weight only (sorted desc by judge_pass)")
        parts.append("")
        parts.append(open_weight_only_table(summary, metadata))
        parts.append("")

        for field, label in (
            ("family", "Family"),
            ("vendor", "Vendor"),
            ("architecture", "Architecture"),
            ("license", "License"),
        ):
            parts.append(f"## Grouped by {label}")
            parts.append("")
            parts.append(
                grouped_table(summary, metadata, group_field=field, label=label)
            )
            parts.append("")

    parts.append("## Canonical case grid")
    parts.append("")
    parts.append(canonical_grid(canonical))
    parts.append("")
    parts.append("## Per-class accuracy (% judge_pass)")
    parts.append("")
    parts.append(per_class_table(scored, dataset_df))
    parts.append("")
    parts.append("## Disagreements between methods (top 20)")
    parts.append("")
    parts.append(disagreement_table(scored))
    parts.append("")
    return "\n".join(parts)


def write_report(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


__all__ = [
    "canonical_grid",
    "disagreement_table",
    "grouped_table",
    "headline_table",
    "open_weight_only_table",
    "per_class_table",
    "render_report",
    "write_report",
]
