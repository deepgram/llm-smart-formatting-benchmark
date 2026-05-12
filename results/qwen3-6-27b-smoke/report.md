# Smart-formatting eval — run `qwen3-6-27b-smoke`

Judge: `claude-opus-4-7` — total judge cost: $34.4077
Models: 1 | Rows scored: 501

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-6-27b` | — | — / — | — | — | 81.6% [78.0-84.8] | 60.1% | 5/9 | 28 | 18.2% | 1088 ms | $0.0612 |

## 2. Open-weight only (sorted desc by judge_pass)

_No open-weight models scored._

## Grouped by Family

_No Family grouping available._

## Grouped by Vendor

_No Vendor grouping available._

## Grouped by Architecture

_No Architecture grouping available._

## Grouped by License

_No License grouping available._

## Canonical case grid

| Sample ID | qwen3-6-27b |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | PASS |
| `CANONICAL-NIAGARA-PHONE` | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS |
| `CANONICAL-TALKATOO-CENTURY` | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | qwen3-6-27b |
| --- | --- |
| ADDRESS | 96.4% |
| ADVERSARIAL | 70.9% |
| CARDINAL | 92.7% |
| CREDIT_CARD | 65.0% |
| DATE | 87.8% |
| DATE_INTERVAL | 100.0% |
| DRUG_WITH_DOSE | 100.0% |
| EMAIL_ADDRESS | 57.1% |
| MIXED | 72.7% |
| MONEY | 87.8% |
| NUMERIC_ID | 66.7% |
| PERCENT | 89.3% |
| PHONE_NUMBER | 95.3% |
| SSN | 66.7% |
| TIME | 80.0% |
| URL | 87.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen3-6-27b` | `MONEY-E002` | False | pass | judge_pass_em_fail | we raised $1.2B | we raised $1.2 billion |
| `qwen3-6-27b` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million |
| `qwen3-6-27b` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2.5 million |
| `qwen3-6-27b` | `DATE-006` | False | pass | judge_pass_em_fail | on August 31 he resigned | on August 31st he resigned |
| `qwen3-6-27b` | `DATE-004` | False | pass | judge_pass_em_fail | the report is due December 1 | the report is due December 1st |
| `qwen3-6-27b` | `DATE-008` | False | pass | judge_pass_em_fail | audit was October 22 | audit was October 22nd |
| `qwen3-6-27b` | `DATE-010` | False | pass | judge_pass_em_fail | appointment May 16 | appointment May 16th |
| `qwen3-6-27b` | `MONEY-T002` | False | pass | judge_pass_em_fail | the charge will be $342.99 | The charge will be $342.99. |
| `qwen3-6-27b` | `DATE-EU-001` | False | pass | judge_pass_em_fail | meeting on the 03/02/2026 | meeting on 03/02/2026 |
| `qwen3-6-27b` | `DATE-012` | False | pass | judge_pass_em_fail | payment posted June 30 | payment posted June 30th |
| `qwen3-6-27b` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 1952 |
| `qwen3-6-27b` | `TIME-Q-001` | False | pass | judge_pass_em_fail | meet at 3:15 PM | meet at 3:15 |
| `qwen3-6-27b` | `TIME-005` | False | pass | judge_pass_em_fail | around 6:00 PM | around 6 PM |
| `qwen3-6-27b` | `TIME-Q-004` | False | pass | judge_pass_em_fail | 11:15 AM | 11:15 |
| `qwen3-6-27b` | `TIME-E-004` | False | pass | judge_pass_em_fail | at 0:30 | at 00:30 |
| `qwen3-6-27b` | `TIME-Q-002` | False | pass | judge_pass_em_fail | around 7:30 PM | around 7:30 |
| `qwen3-6-27b` | `TIME-E-001` | False | pass | judge_pass_em_fail | 12:00 AM | 12:00 AM sharp |
| `qwen3-6-27b` | `TIME-Q-003` | False | pass | judge_pass_em_fail | quarter to nine | 8:45 |
| `qwen3-6-27b` | `TIME-Q-005` | False | pass | judge_pass_em_fail | 12:30 PM | 12:30 p.m. |
| `qwen3-6-27b` | `CARD-L-005` | False | pass | judge_pass_em_fail | 700,000 in ARR | $700,000 in ARR |
