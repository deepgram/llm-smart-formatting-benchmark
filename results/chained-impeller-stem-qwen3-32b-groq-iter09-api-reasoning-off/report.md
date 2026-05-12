# Smart-formatting eval — run `chained-impeller-stem-qwen3-32b-groq-iter09-api-reasoning-off`

Judge: `claude-opus-4-7` — total judge cost: $5.4832
Models: 1 | Rows scored: 80

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-32b-groq` | Alibaba/Qwen | 32B / 32B | dense | Apache-2.0 | 77.5% [67.2-85.3] | 70.0% | 4/9 | 10 | 25.0% | 396 ms | $0.0294 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-32b-groq` | Alibaba/Qwen | 32B / 32B | dense | Apache-2.0 | 77.5% [67.2-85.3] | 70.0% | 4/9 | 10 | 25.0% | 396 ms | $0.0294 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| qwen | 1 | 77.5% | 70.0% | 4 | 10 | $0.0294 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Alibaba/Qwen | 1 | 77.5% | 70.0% | 4 | 10 | $0.0294 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| dense | 1 | 77.5% | 70.0% | 4 | 10 | $0.0294 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Apache-2.0 | 1 | 77.5% | 70.0% | 4 | 10 | $0.0294 |

## Canonical case grid

| Sample ID | qwen3-32b-groq |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | FAIL |
| `CANONICAL-NIAGARA-PHONE` | PASS |
| `CANONICAL-RINGCENTRAL-PHONE` | FAIL |
| `CANONICAL-TALKATOO-CENTURY` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | qwen3-32b-groq |
| --- | --- |
| CARDINAL | 50.0% |
| DATE | 81.1% |
| MONEY | 80.6% |
| NUMERIC_ID | 0.0% |
| PERCENT | 100.0% |
| PHONE_NUMBER | 50.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen3-32b-groq` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `qwen3-32b-groq` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2,500,000 |
| `qwen3-32b-groq` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50 |
| `qwen3-32b-groq` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8¢ |
| `qwen3-32b-groq` | `MONEY-E011` | False | pass | judge_pass_em_fail | $0.99 | 99¢ |
| `qwen3-32b-groq` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million dollars |
| `qwen3-32b-groq` | `DATE-ISO-008` | False | wrong_value | regex_judge_disagree | expires 2028-07-03 | expires 2028-03-07 |
