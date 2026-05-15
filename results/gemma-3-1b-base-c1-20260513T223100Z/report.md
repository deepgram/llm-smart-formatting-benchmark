# Smart-formatting eval — run `gemma-3-1b-base-c1-20260513T223100Z`

Judge: `claude-opus-4-7` — total judge cost: $11.7925
Models: 1 | Rows scored: 169

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemma-3-1b-base-c1` | — | — / — | — | — | 3.0% [1.3-6.7] | 3.0% | 0/9 | 49 | 40.8% | 221 ms | — |

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

| Sample ID | gemma-3-1b-base-c1 |
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

| entity_class | gemma-3-1b-base-c1 |
| --- | --- |
| ADDRESS | 0.0% |
| ADVERSARIAL | 15.4% |
| CARDINAL | 0.0% |
| CREDIT_CARD | 0.0% |
| DATE | 9.1% |
| DATE_INTERVAL | 0.0% |
| DRUG_WITH_DOSE | 0.0% |
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
| TIME | 0.0% |
| URL | 0.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `gemma-3-1b-base-c1` | `DATE-PX-002` | False | other | regex_judge_disagree | the deadline is 2026-09-15 | 2026-09-15 |
