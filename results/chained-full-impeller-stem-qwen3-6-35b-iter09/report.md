# Smart-formatting eval — run `chained-full-impeller-stem-qwen3-6-35b-iter09`

Judge: `claude-opus-4-7` — total judge cost: $34.4006
Models: 1 | Rows scored: 502

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-6-35b` | Alibaba/Qwen | 3B / 35B | moe | Apache-2.0 | 81.1% [77.4-84.3] | 68.5% | 5/9 | 43 | 23.3% | 876 ms | $0.2298 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-6-35b` | Alibaba/Qwen | 3B / 35B | moe | Apache-2.0 | 81.1% [77.4-84.3] | 68.5% | 5/9 | 43 | 23.3% | 876 ms | $0.2298 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| qwen | 1 | 81.1% | 68.5% | 5 | 43 | $0.2298 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Alibaba/Qwen | 1 | 81.1% | 68.5% | 5 | 43 | $0.2298 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| moe | 1 | 81.1% | 68.5% | 5 | 43 | $0.2298 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Apache-2.0 | 1 | 81.1% | 68.5% | 5 | 43 | $0.2298 |

## Canonical case grid

| Sample ID | qwen3-6-35b |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | PASS |
| `CANONICAL-NIAGARA-PHONE` | PASS |
| `CANONICAL-RINGCENTRAL-PHONE` | FAIL |
| `CANONICAL-TALKATOO-CENTURY` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | qwen3-6-35b |
| --- | --- |
| ADDRESS | 85.7% |
| ADVERSARIAL | 72.7% |
| CARDINAL | 90.2% |
| CREDIT_CARD | 45.0% |
| DATE | 89.8% |
| DATE_INTERVAL | 80.0% |
| DRUG_WITH_DOSE | 93.3% |
| EMAIL_ADDRESS | 92.9% |
| MIXED | 72.7% |
| MONEY | 80.5% |
| NUMERIC_ID | 69.0% |
| PERCENT | 96.4% |
| PHONE_NUMBER | 86.0% |
| SSN | 100.0% |
| TIME | 61.3% |
| URL | 91.3% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen3-6-35b` | `MONEY-E004` | False | pass | judge_pass_em_fail | a loss of -$12,000 | a loss of negative $12,000 |
| `qwen3-6-35b` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2,500,000 |
| `qwen3-6-35b` | `MONEY-E011` | False | pass | judge_pass_em_fail | $0.99 | 99¢ |
| `qwen3-6-35b` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8¢ |
| `qwen3-6-35b` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50 |
| `qwen3-6-35b` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million |
| `qwen3-6-35b` | `MONEY-P003` | False | pass | judge_pass_em_fail | we pulled in $27M last quarter | we pulled in $27.0M last quarter |
| `qwen3-6-35b` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 1952 |
| `qwen3-6-35b` | `TIME-E-003` | False | pass | judge_pass_em_fail | at 3:00 | at 3 |
| `qwen3-6-35b` | `TIME-24-005` | False | other | regex_judge_disagree | departure 05:15 | departure oh 05:15 |
| `qwen3-6-35b` | `CARD-O-004` | False | pass | judge_pass_em_fail | the 102nd floor | the 102nd Floor |
| `qwen3-6-35b` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in ARR |
| `qwen3-6-35b` | `PCT-E004` | False | pass | judge_pass_em_fail | up 50 bps | up 50 basis points |
| `qwen3-6-35b` | `PCT-D-006` | False | pass | judge_pass_em_fail | 12.3% YoY | 12.3% yoy |
| `qwen3-6-35b` | `PCT-S005` | False | pass | judge_pass_em_fail | around 33.3% | around 33.33% |
| `qwen3-6-35b` | `PHONE-X001` | False | pass | judge_pass_em_fail | call 212-555-1234 ext. 407 | call 212-555-1234 extension 407 |
| `qwen3-6-35b` | `PHONE-X003` | False | pass | judge_pass_em_fail | from Paris dial +33 1 42 78 90 12 | from Paris dial +33142789012 |
| `qwen3-6-35b` | `PHONE-X004` | False | pass | judge_pass_em_fail | call 1-800-FLOWERS | call 1-800-356-9377 |
| `qwen3-6-35b` | `ID-C-004` | False | pass | judge_pass_em_fail | id 100000007 | ID 100000007 |
| `qwen3-6-35b` | `CC-E003` | False | pass | judge_pass_em_fail | expiration is 07/28 | expiration is 07/2028 |
