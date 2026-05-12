# Smart-formatting eval — run `chained-full-impeller-stem-granite-4-1-8b-iter09`

Judge: `claude-opus-4-7` — total judge cost: $34.5199
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `granite-4-1-8b` | IBM | 8B / 8B | dense | Apache-2.0 | 72.1% [68.0-75.8] | 60.1% | 4/9 | 62 | 27.5% | 246 ms | $0.0541 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `granite-4-1-8b` | IBM | 8B / 8B | dense | Apache-2.0 | 72.1% [68.0-75.8] | 60.1% | 4/9 | 62 | 27.5% | 246 ms | $0.0541 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| granite | 1 | 72.1% | 60.1% | 4 | 62 | $0.0541 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| IBM | 1 | 72.1% | 60.1% | 4 | 62 | $0.0541 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| dense | 1 | 72.1% | 60.1% | 4 | 62 | $0.0541 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Apache-2.0 | 1 | 72.1% | 60.1% | 4 | 62 | $0.0541 |

## Canonical case grid

| Sample ID | granite-4-1-8b |
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

| entity_class | granite-4-1-8b |
| --- | --- |
| ADDRESS | 71.4% |
| ADVERSARIAL | 47.3% |
| CARDINAL | 87.8% |
| CREDIT_CARD | 30.0% |
| DATE | 77.6% |
| DATE_INTERVAL | 90.0% |
| DRUG_WITH_DOSE | 80.0% |
| EMAIL_ADDRESS | 85.7% |
| MIXED | 75.8% |
| MONEY | 75.6% |
| NUMERIC_ID | 66.7% |
| PERCENT | 92.9% |
| PHONE_NUMBER | 67.4% |
| SSN | 86.7% |
| TIME | 76.7% |
| URL | 65.2% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `granite-4-1-8b` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50 |
| `granite-4-1-8b` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2,500,000 |
| `granite-4-1-8b` | `MONEY-E004` | False | pass | judge_pass_em_fail | a loss of -$12,000 | a loss of negative $12,000 |
| `granite-4-1-8b` | `DATE-ISO-001` | False | other | regex_judge_disagree | the launch is 2026-03-05 | 2026-03-05 |
| `granite-4-1-8b` | `DATE-ISO-006` | False | other | regex_judge_disagree | end of fiscal is 2026-12-31 | 2026-12-31 |
| `granite-4-1-8b` | `DATE-ISO-007` | False | other | regex_judge_disagree | flight is on 2026-10-14 | 2026-10-14 |
| `granite-4-1-8b` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 1952 |
| `granite-4-1-8b` | `TIME-Q-001` | False | pass | judge_pass_em_fail | meet at 3:15 PM | meet at 3:15 |
| `granite-4-1-8b` | `TIME-Q-002` | False | pass | judge_pass_em_fail | around 7:30 PM | around 7:30 |
| `granite-4-1-8b` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in ARR |
| `granite-4-1-8b` | `CARD-O-004` | False | pass | judge_pass_em_fail | the 102nd floor | the 102nd Floor |
| `granite-4-1-8b` | `PCT-D-006` | False | pass | judge_pass_em_fail | 12.3% YoY | 12.3% yoy |
| `granite-4-1-8b` | `PCT-E004` | False | pass | judge_pass_em_fail | up 50 bps | up 0.50% |
| `granite-4-1-8b` | `PCT-S005` | False | pass | judge_pass_em_fail | around 33.3% | around 33.333% |
| `granite-4-1-8b` | `PHONE-008` | False | pass | judge_pass_em_fail | front desk 855-555-0999 | front desk (855) 555-0999 |
| `granite-4-1-8b` | `PHONE-E164-007` | False | numeric_drift | regex_judge_disagree | +19175554321 | +19175553421 |
| `granite-4-1-8b` | `PHONE-E164-002` | False | numeric_drift | regex_judge_disagree | the number is +16465558901 | the number is +1645558901 |
| `granite-4-1-8b` | `PHONE-E164-008` | False | numeric_drift | regex_judge_disagree | +16025550910 | +6025550910 |
| `granite-4-1-8b` | `PHONE-E164-003` | False | style_violation | regex_judge_disagree | ring +12025553456 | +2025553456 |
| `granite-4-1-8b` | `PHONE-X002` | False | pass | judge_pass_em_fail | in London it's +44 20 7946 0958 | in London it's +442079460958 |
