# Smart-formatting eval — run `gemma-3-270m-base-c1-20260514T225633Z`

Judge: `claude-opus-4-7` — total judge cost: $11.8370
Models: 1 | Rows scored: 169

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemma-3-270m-base-c1` | — | — / — | — | — | 3.0% [1.3-6.7] | 1.2% | 0/9 | 80 | 25.4% | 309 ms | — |

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

| Sample ID | gemma-3-270m-base-c1 |
| --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL |
| `CANONICAL-AVOMA-YEAR` | FAIL |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL |
| `CANONICAL-CRESTA-PERCENT` | FAIL |
| `CANONICAL-NIAGARA-ORDERID` | FAIL |
| `CANONICAL-NIAGARA-PHONE` | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | FAIL |
| `CANONICAL-TALKATOO-CENTURY` | FAIL |

## Per-class accuracy (% judge_pass)

| entity_class | gemma-3-270m-base-c1 |
| --- | --- |
| ADDRESS | 0.0% |
| ADVERSARIAL | 7.7% |
| CARDINAL | 0.0% |
| CREDIT_CARD | 0.0% |
| DATE | 0.0% |
| DATE_INTERVAL | 0.0% |
| DRUG_WITH_DOSE | 33.3% |
| EMAIL_ADDRESS | 0.0% |
| MIXED | 0.0% |
| MONEY | 0.0% |
| MONEY|DATE|URL | 0.0% |
| NUMERIC_ID | 0.0% |
| NUMERIC_ID|DATE|MONEY | 0.0% |
| NUMERIC_ID|MONEY|DATE | 0.0% |
| PERCENT | 0.0% |
| PHONE_NUMBER | 0.0% |
| PHONE_NUMBER|TIME | 0.0% |
| SSN | 0.0% |
| TIME | 16.7% |
| URL | 0.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `gemma-3-270m-base-c1` | `ADV-NFR-005` | False | pass | judge_pass_em_fail | i'm really frustrated with your service | I'm really frustrated with your service |
| `gemma-3-270m-base-c1` | `DRUG-005` | False | pass | judge_pass_em_fail | atorvastatin 20 mg at bedtime | atorvastatin 20mg at bedtime |
| `gemma-3-270m-base-c1` | `TIME-E-002` | False | pass | judge_pass_em_fail | 12:00 | <transcript> 12:00 </transcript> |
