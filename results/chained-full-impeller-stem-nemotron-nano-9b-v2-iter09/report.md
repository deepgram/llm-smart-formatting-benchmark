# Smart-formatting eval — run `chained-full-impeller-stem-nemotron-nano-9b-v2-iter09`

Judge: `claude-opus-4-7` — total judge cost: $34.6823
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `nemotron-nano-9b` | Nvidia | 9B / 9B | dense | Nvidia-Open-Model | 65.9% [61.6-69.9] | 54.3% | 4/9 | 57 | 30.3% | 1093 ms | $0.0453 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `nemotron-nano-9b` | Nvidia | 9B / 9B | dense | Nvidia-Open-Model | 65.9% [61.6-69.9] | 54.3% | 4/9 | 57 | 30.3% | 1093 ms | $0.0453 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| nemotron | 1 | 65.9% | 54.3% | 4 | 57 | $0.0453 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Nvidia | 1 | 65.9% | 54.3% | 4 | 57 | $0.0453 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| dense | 1 | 65.9% | 54.3% | 4 | 57 | $0.0453 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Nvidia-Open-Model | 1 | 65.9% | 54.3% | 4 | 57 | $0.0453 |

## Canonical case grid

| Sample ID | nemotron-nano-9b |
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

| entity_class | nemotron-nano-9b |
| --- | --- |
| ADDRESS | 85.7% |
| ADVERSARIAL | 43.6% |
| CARDINAL | 75.6% |
| CREDIT_CARD | 25.0% |
| DATE | 83.7% |
| DATE_INTERVAL | 80.0% |
| DRUG_WITH_DOSE | 93.3% |
| EMAIL_ADDRESS | 85.7% |
| MIXED | 60.6% |
| MONEY | 70.7% |
| NUMERIC_ID | 57.1% |
| PERCENT | 64.3% |
| PHONE_NUMBER | 51.2% |
| SSN | 86.7% |
| TIME | 50.0% |
| URL | 78.3% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `nemotron-nano-9b` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | +1-734-272-2384  |
| `nemotron-nano-9b` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50  |
| `nemotron-nano-9b` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2,500,000  |
| `nemotron-nano-9b` | `MONEY-E004` | False | pass | judge_pass_em_fail | a loss of -$12,000 | a loss of negative $12,000  |
| `nemotron-nano-9b` | `MONEY-E011` | False | pass | judge_pass_em_fail | $0.99 | 99¢  |
| `nemotron-nano-9b` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8 cents  |
| `nemotron-nano-9b` | `DATE-ISO-001` | False | other | regex_judge_disagree | the launch is 2026-03-05 | 2026-03-05  |
| `nemotron-nano-9b` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 1952  |
| `nemotron-nano-9b` | `DATE-EU-005` | False | pass | judge_pass_em_fail | meeting on the 28/03/2027 | meeting on 28/03/2027  |
| `nemotron-nano-9b` | `DATE-EU-002` | False | pass | judge_pass_em_fail | meeting on the 15/07/2024 | meeting on 15/07/2024  |
| `nemotron-nano-9b` | `TIME-24-003` | False | other | regex_judge_disagree | flight at 16:45 | 16:45  |
| `nemotron-nano-9b` | `TIME-24-006` | False | other | regex_judge_disagree | the cron runs at 23:59 | 23:59  |
| `nemotron-nano-9b` | `TIME-Q-002` | False | pass | judge_pass_em_fail | around 7:30 PM | 7:30 PM  |
| `nemotron-nano-9b` | `TIME-Q-001` | False | pass | judge_pass_em_fail | meet at 3:15 PM | meet at 3:15  |
| `nemotron-nano-9b` | `TIME-Q-004` | False | pass | judge_pass_em_fail | 11:15 AM | 11:15  |
| `nemotron-nano-9b` | `TIME-24-004` | False | other | regex_judge_disagree | the call is at 21:00 | 21:00  |
| `nemotron-nano-9b` | `CARD-Y-002` | False | pass | judge_pass_em_fail | back in 1973 | Back in 1973  |
| `nemotron-nano-9b` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in ARR  |
| `nemotron-nano-9b` | `PCT-E004` | False | pass | judge_pass_em_fail | up 50 bps | up 0.50%  |
| `nemotron-nano-9b` | `PHONE-E164-001` | False | other | regex_judge_disagree | call +15105552233 | +15105552233  |
