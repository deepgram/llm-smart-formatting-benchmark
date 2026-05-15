# Smart-formatting eval — run `ft-qwen3-8b-smart-fmt-20260512T195149Z`

Judge: `claude-opus-4-7` — total judge cost: $8.6198
Models: 1 | Rows scored: 126

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ft-qwen3-8b-smart-fmt` | — | — / — | — | — | 91.3% [85.0-95.1] | 85.7% | 5/9 | 5 | 13.5% | 5285 ms | — |

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

| Sample ID | ft-qwen3-8b-smart-fmt |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | PASS |
| `CANONICAL-CRESTA-PERCENT` | PASS |
| `CANONICAL-NIAGARA-ORDERID` | PASS |
| `CANONICAL-NIAGARA-PHONE` | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS |
| `CANONICAL-TALKATOO-CENTURY` | FAIL |

## Per-class accuracy (% judge_pass)

| entity_class | ft-qwen3-8b-smart-fmt |
| --- | --- |
| ADDRESS | 100.0% |
| ADDRESS|PHONE_NUMBER|CARDINAL | 100.0% |
| ADVERSARIAL | 72.7% |
| CARDINAL | 80.0% |
| CREDIT_CARD | 100.0% |
| CREDIT_CARD|MONEY | 100.0% |
| DATE | 90.9% |
| DATE_INTERVAL | 83.3% |
| DRUG_WITH_DOSE | 100.0% |
| EMAIL_ADDRESS | 83.3% |
| MIXED | 100.0% |
| MONEY | 100.0% |
| MONEY|DATE|EMAIL_ADDRESS|PHONE_NUMBER | 100.0% |
| MONEY|PHONE_NUMBER | 100.0% |
| NUMERIC_ID | 90.0% |
| PERCENT | 83.3% |
| PHONE_NUMBER | 90.0% |
| PHONE_NUMBER|CARDINAL | 100.0% |
| PHONE_NUMBER|TIME | 100.0% |
| SSN | 100.0% |
| TIME | 100.0% |
| TIME|DATE | 100.0% |
| URL | 100.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `ft-qwen3-8b-smart-fmt` | `ADDR-E007` | False | pass | judge_pass_em_fail | 200 Queen Street, Toronto, ON M5H 2M9, Canada | 200 Queen Street, Toronto, Ontario M5H 2M9, Canada |
| `ft-qwen3-8b-smart-fmt` | `ADDR-E001` | False | pass | judge_pass_em_fail | send to 123 Main Street, Apt 7B, New York, NY 10001 | send to 123 Main Street, Apartment 7B, New York, NY 10001 |
| `ft-qwen3-8b-smart-fmt` | `AUG-DATE-INTERVAL-010-42` | False | pass | judge_pass_em_fail | the campaign will run January – March 2025 | the campaign will run January through March 2025 |
| `ft-qwen3-8b-smart-fmt` | `AUG-DRUG-WITH-DOSE-003-42` | False | pass | judge_pass_em_fail | give amoxicillin suspension 5 ml twice daily for 10 days | give amoxicillin suspension 5 mL twice daily for 10 days |
| `ft-qwen3-8b-smart-fmt` | `ID-C-009` | False | pass | judge_pass_em_fail | id 800555000 | id 8005550000 |
| `ft-qwen3-8b-smart-fmt` | `MESSY-005` | False | pass | judge_pass_em_fail | alright so the technician will come uh between 2 and 4 on Thursday and if you n… | alright so the technician will come uh between 2:00 PM and 4:00 PM on Thursday … |
| `ft-qwen3-8b-smart-fmt` | `MESSY-007` | False | pass | judge_pass_em_fail | caller says the incident is at uh 452 North Maple Street Apartment 3B and the c… | caller says the incident is at uh 452 N Maple Street Apt 3B and the callback is… |
