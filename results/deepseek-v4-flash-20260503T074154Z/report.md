# Smart-formatting eval — run `deepseek-v4-flash-20260503T074154Z`

Judge: `claude-opus-4-7` — total judge cost: $34.2717
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `deepseek-v4-flash` | DeepSeek | ? / ? | moe | MIT | 83.4% [79.9-86.4] | 66.5% | 7/9 | 23 | 16.6% | 2541 ms | $0.0345 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `deepseek-v4-flash` | DeepSeek | ? / ? | moe | MIT | 83.4% [79.9-86.4] | 66.5% | 7/9 | 23 | 16.6% | 2541 ms | $0.0345 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | 1 | 83.4% | 66.5% | 7 | 23 | $0.0345 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| DeepSeek | 1 | 83.4% | 66.5% | 7 | 23 | $0.0345 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| moe | 1 | 83.4% | 66.5% | 7 | 23 | $0.0345 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| MIT | 1 | 83.4% | 66.5% | 7 | 23 | $0.0345 |

## Canonical case grid

| Sample ID | deepseek-v4-flash |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | PASS |
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
| ADDRESS | 85.7% |
| ADVERSARIAL | 65.5% |
| CARDINAL | 87.8% |
| CREDIT_CARD | 70.0% |
| DATE | 95.9% |
| DATE_INTERVAL | 100.0% |
| DRUG_WITH_DOSE | 100.0% |
| EMAIL_ADDRESS | 85.7% |
| MIXED | 78.8% |
| MONEY | 85.4% |
| NUMERIC_ID | 73.8% |
| PERCENT | 82.1% |
| PHONE_NUMBER | 95.3% |
| SSN | 93.3% |
| TIME | 73.3% |
| URL | 87.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `deepseek-v4-flash` | `MONEY-004` | False | pass | judge_pass_em_fail | the bill came to $47 | The bill came to $47. |
| `deepseek-v4-flash` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2.5 million |
| `deepseek-v4-flash` | `MONEY-E003` | False | pass | judge_pass_em_fail | budget of about $500K | budget of about $500,000 |
| `deepseek-v4-flash` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8¢ |
| `deepseek-v4-flash` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2,500,000 |
| `deepseek-v4-flash` | `DATE-006` | False | pass | judge_pass_em_fail | on August 31 he resigned | On August 31st he resigned |
| `deepseek-v4-flash` | `MONEY-P003` | False | pass | judge_pass_em_fail | we pulled in $27M last quarter | we pulled in $27.0M last quarter |
| `deepseek-v4-flash` | `DATE-004` | False | pass | judge_pass_em_fail | the report is due December 1 | The report is due December 1 |
| `deepseek-v4-flash` | `DATE-EU-005` | False | pass | judge_pass_em_fail | meeting on the 28/03/2027 | meeting on 28/03/2027 |
| `deepseek-v4-flash` | `DATE-EU-001` | False | pass | judge_pass_em_fail | meeting on the 03/02/2026 | meeting on 03/02/2026 |
| `deepseek-v4-flash` | `DATE-EU-002` | False | pass | judge_pass_em_fail | meeting on the 15/07/2024 | meeting on 15/07/2024 |
| `deepseek-v4-flash` | `DATE-EU-004` | False | pass | judge_pass_em_fail | meeting on the 01/12/2026 | meeting on 01/12/2026 |
| `deepseek-v4-flash` | `DATE-EU-003` | False | pass | judge_pass_em_fail | meeting on the 09/10/2025 | meeting on 09/10/2025 |
| `deepseek-v4-flash` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 52 |
| `deepseek-v4-flash` | `TIME-005` | False | pass | judge_pass_em_fail | around 6:00 PM | around 6 PM |
| `deepseek-v4-flash` | `TIME-003` | False | pass | judge_pass_em_fail | meeting at 10:00 AM | meeting at 10 AM |
| `deepseek-v4-flash` | `TIME-E-005` | False | pass | judge_pass_em_fail | around 10ish | around 10-ish |
| `deepseek-v4-flash` | `TIME-Q-002` | False | pass | judge_pass_em_fail | around 7:30 PM | around 7:30 |
| `deepseek-v4-flash` | `CARD-L-002` | False | pass | judge_pass_em_fail | we sold 1,200,000 units | We sold 1,200,000 units. |
| `deepseek-v4-flash` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in arr |
