# Smart-formatting eval — run `chained-full-impeller-stem-qwen3-32b-groq-iter09-api-reasoning-off`

Judge: `claude-opus-4-7` — total judge cost: $34.4491
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-32b-groq` | Alibaba/Qwen | 32B / 32B | dense | Apache-2.0 | 76.5% [72.5-80.0] | 63.7% | 4/9 | 46 | 22.8% | 402 ms | $0.1766 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-32b-groq` | Alibaba/Qwen | 32B / 32B | dense | Apache-2.0 | 76.5% [72.5-80.0] | 63.7% | 4/9 | 46 | 22.8% | 402 ms | $0.1766 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| qwen | 1 | 76.5% | 63.7% | 4 | 46 | $0.1766 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Alibaba/Qwen | 1 | 76.5% | 63.7% | 4 | 46 | $0.1766 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| dense | 1 | 76.5% | 63.7% | 4 | 46 | $0.1766 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Apache-2.0 | 1 | 76.5% | 63.7% | 4 | 46 | $0.1766 |

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
| ADDRESS | 82.1% |
| ADVERSARIAL | 67.3% |
| CARDINAL | 87.8% |
| CREDIT_CARD | 45.0% |
| DATE | 75.5% |
| DATE_INTERVAL | 80.0% |
| DRUG_WITH_DOSE | 100.0% |
| EMAIL_ADDRESS | 96.4% |
| MIXED | 66.7% |
| MONEY | 82.9% |
| NUMERIC_ID | 64.3% |
| PERCENT | 100.0% |
| PHONE_NUMBER | 60.5% |
| SSN | 86.7% |
| TIME | 66.7% |
| URL | 91.3% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen3-32b-groq` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `qwen3-32b-groq` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2,500,000 |
| `qwen3-32b-groq` | `MONEY-E004` | False | pass | judge_pass_em_fail | a loss of -$12,000 | a loss of negative $12,000 |
| `qwen3-32b-groq` | `MONEY-E011` | False | pass | judge_pass_em_fail | $0.99 | 99¢ |
| `qwen3-32b-groq` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8¢ |
| `qwen3-32b-groq` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50 |
| `qwen3-32b-groq` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | 2.5 million dollars |
| `qwen3-32b-groq` | `DATE-ISO-003` | False | wrong_value | regex_judge_disagree | delivery date 2025-06-09 | delivery date 2025-09-06 |
| `qwen3-32b-groq` | `DATE-ISO-008` | False | wrong_value | regex_judge_disagree | expires 2028-07-03 | expires 2028-03-07 |
| `qwen3-32b-groq` | `TIME-24-002` | False | numeric_drift | regex_judge_disagree | system reboots at 02:30 | system reboots at 00:30 |
| `qwen3-32b-groq` | `TIME-E-004` | False | pass | judge_pass_em_fail | at 0:30 | at 00:30 |
| `qwen3-32b-groq` | `TIME-E-006` | False | pass | judge_pass_em_fail | uh like maybe 4:00 | uh like maybe 04:00 |
| `qwen3-32b-groq` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in ARR |
| `qwen3-32b-groq` | `TIME-Q-001` | False | pass | judge_pass_em_fail | meet at 3:15 PM | meet at 3:15 |
| `qwen3-32b-groq` | `CARD-O-004` | False | pass | judge_pass_em_fail | the 102nd floor | the 102nd Floor |
| `qwen3-32b-groq` | `PCT-E004` | False | pass | judge_pass_em_fail | up 50 bps | up 50 basis points |
| `qwen3-32b-groq` | `PCT-S005` | False | pass | judge_pass_em_fail | around 33.3% | around 33.33% |
| `qwen3-32b-groq` | `PHONE-008` | False | pass | judge_pass_em_fail | front desk 855-555-0999 | front desk (855) 555-0999 |
| `qwen3-32b-groq` | `PHONE-010` | False | pass | judge_pass_em_fail | call 773-555-0404 | call (773) 555-0404 |
| `qwen3-32b-groq` | `PHONE-X003` | False | pass | judge_pass_em_fail | from Paris dial +33 1 42 78 90 12 | from Paris dial +33142789012 |
