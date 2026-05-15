# Smart-formatting eval — run `ft-gemma-3-270m-it-smart-fmt-20260512T205258Z`

Judge: `claude-opus-4-7` — total judge cost: $8.8636
Models: 1 | Rows scored: 126

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ft-gemma-3-270m-it-smart-fmt` | — | — / — | — | — | 37.3% [29.4-46.0] | 30.2% | 3/9 | 34 | 40.5% | 3347 ms | — |

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

| Sample ID | ft-gemma-3-270m-it-smart-fmt |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | PASS |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | FAIL |
| `CANONICAL-NIAGARA-PHONE` | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | FAIL |
| `CANONICAL-TALKATOO-CENTURY` | FAIL |

## Per-class accuracy (% judge_pass)

| entity_class | ft-gemma-3-270m-it-smart-fmt |
| --- | --- |
| ADDRESS | 33.3% |
| ADDRESS|PHONE_NUMBER|CARDINAL | 0.0% |
| ADVERSARIAL | 45.5% |
| CARDINAL | 50.0% |
| CREDIT_CARD | 0.0% |
| CREDIT_CARD|MONEY | 0.0% |
| DATE | 18.2% |
| DATE_INTERVAL | 50.0% |
| DRUG_WITH_DOSE | 100.0% |
| EMAIL_ADDRESS | 0.0% |
| MIXED | 75.0% |
| MONEY | 55.6% |
| MONEY|DATE|EMAIL_ADDRESS|PHONE_NUMBER | 0.0% |
| MONEY|PHONE_NUMBER | 0.0% |
| NUMERIC_ID | 20.0% |
| PERCENT | 50.0% |
| PHONE_NUMBER | 30.0% |
| PHONE_NUMBER|CARDINAL | 0.0% |
| PHONE_NUMBER|TIME | 0.0% |
| SSN | 16.7% |
| TIME | 33.3% |
| TIME|DATE | 100.0% |
| URL | 66.7% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `ft-gemma-3-270m-it-smart-fmt` | `ADDR-007` | False | pass | judge_pass_em_fail | send to 999 Sunset Boulevard, Los Angeles, CA 90069 | send to 999 Sunset Boulevard Los Angeles, CA 90069 |
| `ft-gemma-3-270m-it-smart-fmt` | `AUG-DATE-INTERVAL-006-42` | False | pass | judge_pass_em_fail | the fiscal study covers 2019 to 2022 | the fiscal study covers 2019-2022 |
| `ft-gemma-3-270m-it-smart-fmt` | `AUG-DATE-INTERVAL-010-42` | False | pass | judge_pass_em_fail | the campaign will run January – March 2025 | the campaign will run January through March 2025 |
| `ft-gemma-3-270m-it-smart-fmt` | `AUG-DRUG-WITH-DOSE-003-42` | False | pass | judge_pass_em_fail | give amoxicillin suspension 5 ml twice daily for 10 days | give amoxicillin suspension 5ml twice daily for 10 days |
| `ft-gemma-3-270m-it-smart-fmt` | `AUG-DRUG-WITH-DOSE-011-42` | False | pass | judge_pass_em_fail | gabapentin 300 mg at bedtime | gabapentin 300mg at bedtime |
| `ft-gemma-3-270m-it-smart-fmt` | `DRUG-002` | False | pass | judge_pass_em_fail | amoxicillin 250 mg three times a day | amoxicillin 250mg 3 times a day |
| `ft-gemma-3-270m-it-smart-fmt` | `ID-L-005` | False | pass | judge_pass_em_fail | passport number M23456789 | passport number m23456789 |
| `ft-gemma-3-270m-it-smart-fmt` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2.5 million |
| `ft-gemma-3-270m-it-smart-fmt` | `PHONE-X001` | False | pass | judge_pass_em_fail | call 212-555-1234 ext. 407 | call 212-555-1234 extension 407 |
