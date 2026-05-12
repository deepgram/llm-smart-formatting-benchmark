# Smart-formatting eval — run `nothink-rerun-20260503T181812Z`

Judge: `claude-opus-4-7` — total judge cost: $137.3806
Models: 4 | Rows scored: 2004

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-5-27b` | Alibaba/Qwen | 27B / 27B | dense | Apache-2.0 | 81.6% [78.0-84.8] | 64.7% | 6/9 | 27 | 16.6% | 1000 ms | $0.0393 |
| `qwen3-5-122b` | Alibaba/Qwen | 10B / 122B | moe | Apache-2.0 | 76.0% [72.1-79.6] | 61.1% | 6/9 | 31 | 18.8% | 770 ms | $0.0488 |
| `nemotron-3-super-120b` | Nvidia | 12B / 120B | moe | Nvidia-Open-Model | 68.1% [63.9-72.0] | 56.5% | 6/9 | 36 | 18.2% | 896 ms | $0.0187 |
| `qwen3-14b` | Alibaba/Qwen | 14B / 14B | dense | Apache-2.0 | 63.5% [59.2-67.6] | 49.7% | 5/9 | 54 | 19.4% | 8110 ms | $0.0543 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-5-27b` | Alibaba/Qwen | 27B / 27B | dense | Apache-2.0 | 81.6% [78.0-84.8] | 64.7% | 6/9 | 27 | 16.6% | 1000 ms | $0.0393 |
| `qwen3-5-122b` | Alibaba/Qwen | 10B / 122B | moe | Apache-2.0 | 76.0% [72.1-79.6] | 61.1% | 6/9 | 31 | 18.8% | 770 ms | $0.0488 |
| `nemotron-3-super-120b` | Nvidia | 12B / 120B | moe | Nvidia-Open-Model | 68.1% [63.9-72.0] | 56.5% | 6/9 | 36 | 18.2% | 896 ms | $0.0187 |
| `qwen3-14b` | Alibaba/Qwen | 14B / 14B | dense | Apache-2.0 | 63.5% [59.2-67.6] | 49.7% | 5/9 | 54 | 19.4% | 8110 ms | $0.0543 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| qwen | 3 | 73.7% | 58.5% | 17 | 112 | $0.1424 |
| nemotron | 1 | 68.1% | 56.5% | 6 | 36 | $0.0187 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Alibaba/Qwen | 3 | 73.7% | 58.5% | 17 | 112 | $0.1424 |
| Nvidia | 1 | 68.1% | 56.5% | 6 | 36 | $0.0187 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| dense | 2 | 72.6% | 57.2% | 11 | 81 | $0.0936 |
| moe | 2 | 72.1% | 58.8% | 12 | 67 | $0.0675 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Apache-2.0 | 3 | 73.7% | 58.5% | 17 | 112 | $0.1424 |
| Nvidia-Open-Model | 1 | 68.1% | 56.5% | 6 | 36 | $0.0187 |

## Canonical case grid

| Sample ID | nemotron-3-super-120b | qwen3-14b | qwen3-5-122b | qwen3-5-27b |
| --- | --- | --- | --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS | PASS | PASS | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | PASS | PASS | PASS | PASS |
| `CANONICAL-CRESTA-PERCENT` | PASS | PASS | PASS | PASS |
| `CANONICAL-NIAGARA-ORDERID` | PASS | FAIL | PASS | PASS |
| `CANONICAL-NIAGARA-PHONE` | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS | PASS | PASS | PASS |
| `CANONICAL-TALKATOO-CENTURY` | PASS | PASS | PASS | PASS |

## Per-class accuracy (% judge_pass)

| entity_class | nemotron-3-super-120b | qwen3-14b | qwen3-5-122b | qwen3-5-27b |
| --- | --- | --- | --- | --- |
| ADDRESS | 60.7% | 57.1% | 96.4% | 100.0% |
| ADVERSARIAL | 45.5% | 61.8% | 70.9% | 65.5% |
| CARDINAL | 68.3% | 73.2% | 80.5% | 92.7% |
| CREDIT_CARD | 45.0% | 25.0% | 55.0% | 60.0% |
| DATE | 95.9% | 85.7% | 89.8% | 93.9% |
| DATE_INTERVAL | 70.0% | 70.0% | 100.0% | 100.0% |
| DRUG_WITH_DOSE | 86.7% | 73.3% | 93.3% | 100.0% |
| EMAIL_ADDRESS | 60.7% | 50.0% | 25.0% | 53.6% |
| MIXED | 54.5% | 45.5% | 60.6% | 66.7% |
| MONEY | 73.2% | 63.4% | 87.8% | 92.7% |
| NUMERIC_ID | 69.0% | 66.7% | 61.9% | 69.0% |
| PERCENT | 71.4% | 53.6% | 60.7% | 92.9% |
| PHONE_NUMBER | 79.1% | 69.8% | 95.3% | 95.3% |
| SSN | 66.7% | 60.0% | 66.7% | 66.7% |
| TIME | 63.3% | 63.3% | 80.0% | 70.0% |
| URL | 78.3% | 73.9% | 95.7% | 95.7% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen3-5-122b` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2.5 million |
| `qwen3-5-122b` | `MONEY-E002` | False | pass | judge_pass_em_fail | we raised $1.2B | we raised $1.2 billion |
| `qwen3-5-122b` | `MONEY-E005` | False | pass | judge_pass_em_fail | the refund was -$47.50 | the refund was minus $47.50 |
| `qwen3-5-122b` | `MONEY-E010` | False | pass | judge_pass_em_fail | $0.08 | 8 cents |
| `qwen3-5-122b` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million |
| `qwen3-5-122b` | `MONEY-E004` | False | pass | judge_pass_em_fail | a loss of -$12,000 | a loss of negative $12,000 |
| `qwen3-5-122b` | `MONEY-P003` | False | pass | judge_pass_em_fail | we pulled in $27M last quarter | we pulled in $27.0M last quarter |
| `qwen3-5-122b` | `DATE-010` | False | pass | judge_pass_em_fail | appointment May 16 | appointment May 16th |
| `qwen3-5-122b` | `DATE-012` | False | pass | judge_pass_em_fail | payment posted June 30 | payment posted June 30th |
| `qwen3-5-122b` | `DATE-008` | False | pass | judge_pass_em_fail | audit was October 22 | audit was October 22nd |
| `nemotron-3-super-120b` | `MONEY-E002` | False | pass | judge_pass_em_fail | we raised $1.2B | we raised $1.2 billion |
| `nemotron-3-super-120b` | `MONEY-E001` | False | pass | judge_pass_em_fail | the contract is worth $2.5M | the contract is worth $2.5 million |
| `nemotron-3-super-120b` | `MONEY-E012` | False | pass | judge_pass_em_fail | $2.5M | $2.5 million |
| `qwen3-5-122b` | `DATE-E001` | False | pass | judge_pass_em_fail | she was born in '52 | she was born in 1952 |
| `qwen3-5-122b` | `TIME-003` | False | pass | judge_pass_em_fail | meeting at 10:00 AM | meeting at 10 AM |
| `nemotron-3-super-120b` | `MONEY-P003` | False | pass | judge_pass_em_fail | we pulled in $27M last quarter | we pulled in $27.0M last quarter |
| `qwen3-5-122b` | `TIME-005` | False | pass | judge_pass_em_fail | around 6:00 PM | around 6 PM |
| `nemotron-3-super-120b` | `DATE-005` | False | pass | judge_pass_em_fail | she arrived on February 14 | She arrived on February 14. |
| `nemotron-3-super-120b` | `DATE-006` | False | pass | judge_pass_em_fail | on August 31 he resigned | on August 31st he resigned |
| `qwen3-5-122b` | `TIME-Q-001` | False | pass | judge_pass_em_fail | meet at 3:15 PM | meet at 3:15 |
