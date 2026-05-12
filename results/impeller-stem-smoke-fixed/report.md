# Smart-formatting eval — run `impeller-stem-smoke-fixed`

Judge: `claude-opus-4-7` — total judge cost: $0.2110
Models: 1 | Rows scored: 3

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `impeller-stem-baseline` | Deepgram | undisclosed / undisclosed | distilbert-plus-rules | Proprietary | 33.3% [6.2-79.2] | 33.3% | 1/3 | 2 | 33.3% | 87 ms | $0.0000 |

## 2. Open-weight only (sorted desc by judge_pass)

_No open-weight models scored._

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| smart-formatting | 1 | 33.3% | 33.3% | 1 | 2 | $0.0000 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Deepgram | 1 | 33.3% | 33.3% | 1 | 2 | $0.0000 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| distilbert-plus-rules | 1 | 33.3% | 33.3% | 1 | 2 | $0.0000 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Proprietary | 1 | 33.3% | 33.3% | 1 | 2 | $0.0000 |

## Canonical case grid

| Sample ID | impeller-stem-baseline |
| --- | --- |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | impeller-stem-baseline |
| --- | --- |
| MONEY | 0.0% |
| NUMERIC_ID | 0.0% |
| PERCENT | 100.0% |

## Disagreements between methods (top 20)

_No disagreements between methods._
