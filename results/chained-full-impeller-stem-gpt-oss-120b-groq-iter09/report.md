# Smart-formatting eval — run `chained-full-impeller-stem-gpt-oss-120b-groq-iter09`

Judge: `claude-opus-4-7` — total judge cost: $34.3798
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-120b-groq` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 81.6% [78.0-84.8] | 72.3% | 5/9 | 33 | 22.6% | 736 ms | $0.1396 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-120b-groq` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 81.6% [78.0-84.8] | 72.3% | 5/9 | 33 | 22.6% | 736 ms | $0.1396 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| gpt-oss | 1 | 81.6% | 72.3% | 5 | 33 | $0.1396 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| OpenAI | 1 | 81.6% | 72.3% | 5 | 33 | $0.1396 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| moe | 1 | 81.6% | 72.3% | 5 | 33 | $0.1396 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Apache-2.0 | 1 | 81.6% | 72.3% | 5 | 33 | $0.1396 |

## Canonical case grid

| Sample ID | gpt-oss-120b-groq |
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

| entity_class | gpt-oss-120b-groq |
| --- | --- |
| ADDRESS | 89.3% |
| ADVERSARIAL | 67.3% |
| CARDINAL | 87.8% |
| CREDIT_CARD | 55.0% |
| DATE | 89.8% |
| DATE_INTERVAL | 90.0% |
| DRUG_WITH_DOSE | 100.0% |
| EMAIL_ADDRESS | 96.4% |
| MIXED | 69.7% |
| MONEY | 80.5% |
| NUMERIC_ID | 73.8% |
| PERCENT | 100.0% |
| PHONE_NUMBER | 74.4% |
| SSN | 100.0% |
| TIME | 70.0% |
| URL | 95.7% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-120b-groq` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `gpt-oss-120b-groq` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2,500,000 |
| `gpt-oss-120b-groq` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50 |
| `gpt-oss-120b-groq` | `MONEY-P003` | False | pass | judge_pass_em_fail | we pulled in $27M last quarter | we pulled in $27.0M last quarter |
| `gpt-oss-120b-groq` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 1952 |
| `gpt-oss-120b-groq` | `TIME-005` | False | pass | judge_pass_em_fail | around 6:00 PM | around 6 PM |
| `gpt-oss-120b-groq` | `TIME-E-001` | False | pass | judge_pass_em_fail | 12:00 AM | 12:00 AM sharp |
| `gpt-oss-120b-groq` | `CARD-R-002` | False | pass | judge_pass_em_fail | expect 20 to 30 seats | expect 20–30 seats |
| `gpt-oss-120b-groq` | `CARD-R-005` | False | pass | judge_pass_em_fail | around 15 to 20 minutes | around 15–20 minutes |
| `gpt-oss-120b-groq` | `CARD-O-004` | False | pass | judge_pass_em_fail | the 102nd floor | the 102nd Floor |
| `gpt-oss-120b-groq` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in arr |
| `gpt-oss-120b-groq` | `PCT-D-006` | False | pass | judge_pass_em_fail | 12.3% YoY | 12.3% yoy |
| `gpt-oss-120b-groq` | `PCT-D-005` | False | pass | judge_pass_em_fail | 6.75% APR | 6.75% apr |
| `gpt-oss-120b-groq` | `PCT-S005` | False | pass | judge_pass_em_fail | around 33.3% | around 33.33% |
| `gpt-oss-120b-groq` | `PCT-E004` | False | pass | judge_pass_em_fail | up 50 bps | up 0.5% |
| `gpt-oss-120b-groq` | `PHONE-X001` | False | pass | judge_pass_em_fail | call 212-555-1234 ext. 407 | call 212-555-1234 extension 407 |
| `gpt-oss-120b-groq` | `PHONE-X004` | False | pass | judge_pass_em_fail | call 1-800-FLOWERS | call 1-800-356-9377 |
| `gpt-oss-120b-groq` | `URL-S-007` | False | pass | judge_pass_em_fail | my-store.net | type in my-store.net |
| `gpt-oss-120b-groq` | `ID-C-009` | False | pass | judge_pass_em_fail | id 800555000 | id 8005550000 |
| `gpt-oss-120b-groq` | `CC-R-005` | False | pass | judge_pass_em_fail | the visa ending in 5555 | the visa ending in XXXX XXXX XXXX 5555 |
