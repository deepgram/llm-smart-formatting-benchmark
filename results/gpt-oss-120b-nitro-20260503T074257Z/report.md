# Smart-formatting eval — run `gpt-oss-120b-nitro-20260503T074257Z`

Judge: `claude-opus-4-7` — total judge cost: $34.4090
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-120b-nitro` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 73.2% [69.2-76.9] | 62.3% | 6/9 | 39 | 24.8% | 346 ms | $0.1135 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-120b-nitro` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 73.2% [69.2-76.9] | 62.3% | 6/9 | 39 | 24.8% | 346 ms | $0.1135 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| gpt-oss | 1 | 73.2% | 62.3% | 6 | 39 | $0.1135 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| OpenAI | 1 | 73.2% | 62.3% | 6 | 39 | $0.1135 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| moe | 1 | 73.2% | 62.3% | 6 | 39 | $0.1135 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Apache-2.0 | 1 | 73.2% | 62.3% | 6 | 39 | $0.1135 |

## Canonical case grid

| Sample ID | gpt-oss-120b-nitro |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | PASS |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | PASS |
| `CANONICAL-NIAGARA-PHONE` | PASS |
| `CANONICAL-RINGCENTRAL-PHONE` | FAIL |
| `CANONICAL-TALKATOO-CENTURY` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | gpt-oss-120b-nitro |
| --- | --- |
| ADDRESS | 64.3% |
| ADVERSARIAL | 54.5% |
| CARDINAL | 80.5% |
| CREDIT_CARD | 65.0% |
| DATE | 89.8% |
| DATE_INTERVAL | 80.0% |
| DRUG_WITH_DOSE | 60.0% |
| EMAIL_ADDRESS | 85.7% |
| MIXED | 60.6% |
| MONEY | 68.3% |
| NUMERIC_ID | 64.3% |
| PERCENT | 89.3% |
| PHONE_NUMBER | 81.4% |
| SSN | 86.7% |
| TIME | 66.7% |
| URL | 87.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-120b-nitro` | `CANONICAL-AVOMA-RANGE` | False | pass | judge_pass_em_fail | the budget range is 80,000–90,000 | the budget range is 80–90 thousand |
| `gpt-oss-120b-nitro` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is +1 (734) 272-2384 |
| `gpt-oss-120b-nitro` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2.5 million |
| `gpt-oss-120b-nitro` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million |
| `gpt-oss-120b-nitro` | `MONEY-P003` | False | pass | judge_pass_em_fail | we pulled in $27M last quarter | we pulled in $27.0M last quarter |
| `gpt-oss-120b-nitro` | `DATE-EU-001` | False | pass | judge_pass_em_fail | meeting on the 03/02/2026 | meeting on 03/02/2026 |
| `gpt-oss-120b-nitro` | `DATE-EU-003` | False | pass | judge_pass_em_fail | meeting on the 09/10/2025 | meeting on 09/10/2025 |
| `gpt-oss-120b-nitro` | `DATE-EU-005` | False | pass | judge_pass_em_fail | meeting on the 28/03/2027 | meeting on 28/03/2027 |
| `gpt-oss-120b-nitro` | `DATE-EU-002` | False | pass | judge_pass_em_fail | meeting on the 15/07/2024 | meeting on 15/07/2024 |
| `gpt-oss-120b-nitro` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 52 |
| `gpt-oss-120b-nitro` | `TIME-005` | False | pass | judge_pass_em_fail | around 6:00 PM | around 6 PM |
| `gpt-oss-120b-nitro` | `TIME-24-002` | False | other | regex_judge_disagree | system reboots at 02:30 | system rebootsat 02:30 |
| `gpt-oss-120b-nitro` | `TIME-Q-001` | False | pass | judge_pass_em_fail | meet at 3:15 PM | meet at 3:15 |
| `gpt-oss-120b-nitro` | `TIME-Q-003` | False | pass | judge_pass_em_fail | quarter to nine | 8:45 |
| `gpt-oss-120b-nitro` | `TIME-Q-002` | False | pass | judge_pass_em_fail | around 7:30 PM | around 7:30 |
| `gpt-oss-120b-nitro` | `TIME-Q-004` | False | pass | judge_pass_em_fail | 11:15 AM | 11:15 |
| `gpt-oss-120b-nitro` | `DATE-EU-004` | False | pass | judge_pass_em_fail | meeting on the 01/12/2026 | meeting on 01/12/2026 |
| `gpt-oss-120b-nitro` | `TIME-E-001` | False | pass | judge_pass_em_fail | 12:00 AM | 12:00 a.m. |
| `gpt-oss-120b-nitro` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in arr |
| `gpt-oss-120b-nitro` | `CARD-E002` | False | pass | judge_pass_em_fail | 2.5 cups | 2½ cups |
