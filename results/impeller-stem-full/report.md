# Smart-formatting eval — run `impeller-stem-full`

Judge: `claude-opus-4-7` — total judge cost: $34.5459
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `impeller-stem-baseline` | Deepgram | undisclosed / undisclosed | distilbert-plus-rules | Proprietary | 45.7% [41.4-50.1] | 38.5% | 3/9 | 55 | 18.4% | 45 ms | $0.0000 |

## 2. Open-weight only (sorted desc by judge_pass)

_No open-weight models scored._

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| smart-formatting | 1 | 45.7% | 38.5% | 3 | 55 | $0.0000 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Deepgram | 1 | 45.7% | 38.5% | 3 | 55 | $0.0000 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| distilbert-plus-rules | 1 | 45.7% | 38.5% | 3 | 55 | $0.0000 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Proprietary | 1 | 45.7% | 38.5% | 3 | 55 | $0.0000 |

## Canonical case grid

| Sample ID | impeller-stem-baseline |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | FAIL |
| `CANONICAL-NIAGARA-PHONE` | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | FAIL |
| `CANONICAL-TALKATOO-CENTURY` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | impeller-stem-baseline |
| --- | --- |
| ADDRESS | 46.4% |
| ADVERSARIAL | 60.0% |
| CARDINAL | 51.2% |
| CREDIT_CARD | 15.0% |
| DATE | 40.8% |
| DATE_INTERVAL | 80.0% |
| DRUG_WITH_DOSE | 0.0% |
| EMAIL_ADDRESS | 78.6% |
| MIXED | 30.3% |
| MONEY | 56.1% |
| NUMERIC_ID | 45.2% |
| PERCENT | 71.4% |
| PHONE_NUMBER | 34.9% |
| SSN | 40.0% |
| TIME | 13.3% |
| URL | 52.2% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `impeller-stem-baseline` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2,500,000 |
| `impeller-stem-baseline` | `MONEY-E004` | False | pass | judge_pass_em_fail | a loss of -$12,000 | a loss of negative $12,000 |
| `impeller-stem-baseline` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50 |
| `impeller-stem-baseline` | `MONEY-E011` | False | pass | judge_pass_em_fail | $0.99 | 99¢ |
| `impeller-stem-baseline` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8¢ |
| `impeller-stem-baseline` | `TIME-005` | False | pass | judge_pass_em_fail | around 6:00 PM | around 6PM |
| `impeller-stem-baseline` | `TIME-24-002` | False | other | regex_judge_disagree | system reboots at 02:30 | system reboots at oh 02:30 |
| `impeller-stem-baseline` | `TIME-24-005` | False | other | regex_judge_disagree | departure 05:15 | departure oh 05:15 |
| `impeller-stem-baseline` | `TIME-E-006` | False | pass | judge_pass_em_fail | uh like maybe 4:00 | uh like maybe 04:00 |
| `impeller-stem-baseline` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in arr |
| `impeller-stem-baseline` | `CARD-O-004` | False | pass | judge_pass_em_fail | the 102nd floor | the 102nd Floor |
| `impeller-stem-baseline` | `PCT-D-005` | False | pass | judge_pass_em_fail | 6.75% APR | 6.75% apr |
| `impeller-stem-baseline` | `PCT-D-006` | False | pass | judge_pass_em_fail | 12.3% YoY | 12.3% yoy |
| `impeller-stem-baseline` | `PCT-E004` | False | pass | judge_pass_em_fail | up 50 bps | up 50 basis points |
| `impeller-stem-baseline` | `PCT-E002` | False | pass | judge_pass_em_fail | down -5% | down negative 5% |
| `impeller-stem-baseline` | `PHONE-008` | False | pass | judge_pass_em_fail | front desk 855-555-0999 | front desk (855) 555-0999 |
| `impeller-stem-baseline` | `PHONE-010` | False | pass | judge_pass_em_fail | call 773-555-0404 | call (773) 555-0404 |
| `impeller-stem-baseline` | `PHONE-X005` | False | pass | judge_pass_em_fail | call 555-555-5555 | call (555) 555-5555 |
| `impeller-stem-baseline` | `PHONE-X001` | False | pass | judge_pass_em_fail | call 212-555-1234 ext. 407 | call (212) 555-1234 extension 407 |
| `impeller-stem-baseline` | `CC-E003` | False | pass | judge_pass_em_fail | expiration is 07/28 | expiration is 07/2028 |
