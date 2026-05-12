# Smart-formatting eval — run `kimi-k2-6-20260503T055658Z`

Judge: `claude-opus-4-7` — total judge cost: $34.1710
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `kimi-k2-6` | Moonshot AI | 32B / 1T | moe | MIT-Modified | 77.8% [74.0-81.3] | 69.5% | 7/9 | 89 | 28.9% | 11952 ms | — |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `kimi-k2-6` | Moonshot AI | 32B / 1T | moe | MIT-Modified | 77.8% [74.0-81.3] | 69.5% | 7/9 | 89 | 28.9% | 11952 ms | — |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| kimi | 1 | 77.8% | 69.5% | 7 | 89 | $0.0000 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Moonshot AI | 1 | 77.8% | 69.5% | 7 | 89 | $0.0000 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| moe | 1 | 77.8% | 69.5% | 7 | 89 | $0.0000 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| MIT-Modified | 1 | 77.8% | 69.5% | 7 | 89 | $0.0000 |

## Canonical case grid

| Sample ID | kimi-k2-6 |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | PASS |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | PASS |
| `CANONICAL-NIAGARA-PHONE` | PASS |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS |
| `CANONICAL-TALKATOO-CENTURY` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | kimi-k2-6 |
| --- | --- |
| ADDRESS | 42.9% |
| ADVERSARIAL | 60.0% |
| CARDINAL | 87.8% |
| CREDIT_CARD | 40.0% |
| DATE | 85.7% |
| DATE_INTERVAL | 90.0% |
| DRUG_WITH_DOSE | 86.7% |
| EMAIL_ADDRESS | 92.9% |
| MIXED | 60.6% |
| MONEY | 75.6% |
| NUMERIC_ID | 78.6% |
| PERCENT | 100.0% |
| PHONE_NUMBER | 95.3% |
| SSN | 100.0% |
| TIME | 73.3% |
| URL | 91.3% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `kimi-k2-6` | `CANONICAL-AVOMA-RANGE` | False | pass | judge_pass_em_fail | the budget range is 80,000–90,000 | the budget range is 80,000-90,000 |
| `kimi-k2-6` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `kimi-k2-6` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million |
| `kimi-k2-6` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M |  the contract is worth $2.5 million |
| `kimi-k2-6` | `DATE-006` | False | pass | judge_pass_em_fail | on August 31 he resigned |  on August 31st he resigned |
| `kimi-k2-6` | `DATE-EU-002` | False | pass | judge_pass_em_fail | meeting on the 15/07/2024 | meeting on 15/07/2024 |
| `kimi-k2-6` | `DATE-EU-003` | False | pass | judge_pass_em_fail | meeting on the 09/10/2025 |  meeting on 09/10/2025 |
| `kimi-k2-6` | `DATE-EU-004` | False | pass | judge_pass_em_fail | meeting on the 01/12/2026 |  meeting on 01/12/2026 |
| `kimi-k2-6` | `TIME-Q-004` | False | pass | judge_pass_em_fail | 11:15 AM |  11:15 |
| `kimi-k2-6` | `TIME-Q-002` | False | pass | judge_pass_em_fail | around 7:30 PM |  around 7:30 |
| `kimi-k2-6` | `TIME-Q-001` | False | pass | judge_pass_em_fail | meet at 3:15 PM |  meet at 3:15 |
| `kimi-k2-6` | `TIME-Q-003` | False | pass | judge_pass_em_fail | quarter to nine | 8:45 |
| `kimi-k2-6` | `TIME-E-001` | False | pass | judge_pass_em_fail | 12:00 AM | 12:00 AM sharp |
| `kimi-k2-6` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in ARR |
| `kimi-k2-6` | `CARD-E002` | False | pass | judge_pass_em_fail | 2.5 cups | 2 1/2 cups |
| `kimi-k2-6` | `PCT-E004` | False | pass | judge_pass_em_fail | up 50 bps |  up 50 basis points |
| `kimi-k2-6` | `PCT-S005` | False | pass | judge_pass_em_fail | around 33.3% |  around 33 1/3% |
| `kimi-k2-6` | `PHONE-X003` | False | pass | judge_pass_em_fail | from Paris dial +33 1 42 78 90 12 | from paris dial +33 1 42 78 90 12 |
| `kimi-k2-6` | `PHONE-X004` | False | pass | judge_pass_em_fail | call 1-800-FLOWERS | call 1-800-356-9377 |
| `kimi-k2-6` | `PHONE-X002` | False | pass | judge_pass_em_fail | in London it's +44 20 7946 0958 |  in london it's +44 20 7946 0958 |
