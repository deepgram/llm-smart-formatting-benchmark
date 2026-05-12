# Smart-formatting eval — run `deepseek-v4-flash-nothink-20260503T172916Z`

Judge: `claude-opus-4-7` — total judge cost: $34.3565
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `deepseek-v4-flash` | DeepSeek | ? / ? | moe | MIT | 78.4% [74.6-81.8] | 59.1% | 6/9 | 26 | 18.0% | 886 ms | $0.0149 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `deepseek-v4-flash` | DeepSeek | ? / ? | moe | MIT | 78.4% [74.6-81.8] | 59.1% | 6/9 | 26 | 18.0% | 886 ms | $0.0149 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | 1 | 78.4% | 59.1% | 6 | 26 | $0.0149 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| DeepSeek | 1 | 78.4% | 59.1% | 6 | 26 | $0.0149 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| moe | 1 | 78.4% | 59.1% | 6 | 26 | $0.0149 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| MIT | 1 | 78.4% | 59.1% | 6 | 26 | $0.0149 |

## Canonical case grid

| Sample ID | deepseek-v4-flash |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | PASS |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | PASS |
| `CANONICAL-NIAGARA-PHONE` | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS |
| `CANONICAL-TALKATOO-CENTURY` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | deepseek-v4-flash |
| --- | --- |
| ADDRESS | 89.3% |
| ADVERSARIAL | 56.4% |
| CARDINAL | 85.4% |
| CREDIT_CARD | 65.0% |
| DATE | 91.8% |
| DATE_INTERVAL | 100.0% |
| DRUG_WITH_DOSE | 100.0% |
| EMAIL_ADDRESS | 53.6% |
| MIXED | 75.8% |
| MONEY | 85.4% |
| NUMERIC_ID | 69.0% |
| PERCENT | 85.7% |
| PHONE_NUMBER | 93.0% |
| SSN | 93.3% |
| TIME | 66.7% |
| URL | 73.9% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `deepseek-v4-flash` | `MONEY-004` | False | pass | judge_pass_em_fail | the bill came to $47 | The bill came to $47. |
| `deepseek-v4-flash` | `MONEY-E002` | False | pass | judge_pass_em_fail | we raised $1.2B | We raised $1.2 billion. |
| `deepseek-v4-flash` | `MONEY-E004` | False | pass | judge_pass_em_fail | a loss of -$12,000 | a loss of negative $12,000 |
| `deepseek-v4-flash` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million |
| `deepseek-v4-flash` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2.5 million |
| `deepseek-v4-flash` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8¢ |
| `deepseek-v4-flash` | `MONEY-P001` | False | pass | judge_pass_em_fail | the total is $42.00 | The total is $42.00. |
| `deepseek-v4-flash` | `DATE-005` | False | pass | judge_pass_em_fail | she arrived on February 14 | She arrived on February 14. |
| `deepseek-v4-flash` | `DATE-012` | False | pass | judge_pass_em_fail | payment posted June 30 | payment posted June 30th |
| `deepseek-v4-flash` | `DATE-010` | False | pass | judge_pass_em_fail | appointment May 16 | appointment May 16th |
| `deepseek-v4-flash` | `DATE-006` | False | pass | judge_pass_em_fail | on August 31 he resigned | on August 31st he resigned |
| `deepseek-v4-flash` | `DATE-EU-004` | False | pass | judge_pass_em_fail | meeting on the 01/12/2026 | meeting on 01/12/2026 |
| `deepseek-v4-flash` | `DATE-EU-002` | False | pass | judge_pass_em_fail | meeting on the 15/07/2024 | meeting on 15/07/2024 |
| `deepseek-v4-flash` | `DATE-EU-003` | False | pass | judge_pass_em_fail | meeting on the 09/10/2025 | meeting on 09/10/2025 |
| `deepseek-v4-flash` | `DATE-EU-001` | False | pass | judge_pass_em_fail | meeting on the 03/02/2026 | meeting on 03/02/2026 |
| `deepseek-v4-flash` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 52 |
| `deepseek-v4-flash` | `TIME-003` | False | pass | judge_pass_em_fail | meeting at 10:00 AM | meeting at 10 AM |
| `deepseek-v4-flash` | `DATE-EU-005` | False | pass | judge_pass_em_fail | meeting on the 28/03/2027 | meeting on 28/03/2027 |
| `deepseek-v4-flash` | `TIME-Q-002` | False | pass | judge_pass_em_fail | around 7:30 PM | around 7:30 |
| `deepseek-v4-flash` | `TIME-005` | False | pass | judge_pass_em_fail | around 6:00 PM | around 6 PM |
