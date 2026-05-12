# Smart-formatting eval — run `or-test-canonicals`

Judge: `claude-opus-4-7` — total judge cost: $0.0000
Models: 4 | Rows scored: 36

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-20b` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 55.6% [26.7-81.1] | 55.6% | 5/9 | 4 | 33.3% | 2673 ms | $0.0012 |
| `llama-3-3-70b` | Meta | 70B / 70B | dense | Llama-3.3-Community | 44.4% [18.9-73.3] | 44.4% | 4/9 | 3 | 33.3% | 865 ms | $0.0003 |
| `mistral-small-3-2-24b` | Mistral | 24B / 24B | dense | Apache-2.0 | 33.3% [12.1-64.6] | 22.2% | 3/9 | 4 | 66.7% | 657 ms | $0.0002 |
| `qwen3-30b` | Alibaba/Qwen | 3B / 30B | moe | Apache-2.0 | 33.3% [12.1-64.6] | 33.3% | 3/9 | 3 | 33.3% | 540 ms | $0.0003 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gpt-oss-20b` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 55.6% [26.7-81.1] | 55.6% | 5/9 | 4 | 33.3% | 2673 ms | $0.0012 |
| `llama-3-3-70b` | Meta | 70B / 70B | dense | Llama-3.3-Community | 44.4% [18.9-73.3] | 44.4% | 4/9 | 3 | 33.3% | 865 ms | $0.0003 |
| `mistral-small-3-2-24b` | Mistral | 24B / 24B | dense | Apache-2.0 | 33.3% [12.1-64.6] | 22.2% | 3/9 | 4 | 66.7% | 657 ms | $0.0002 |
| `qwen3-30b` | Alibaba/Qwen | 3B / 30B | moe | Apache-2.0 | 33.3% [12.1-64.6] | 33.3% | 3/9 | 3 | 33.3% | 540 ms | $0.0003 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| gpt-oss | 1 | 55.6% | 55.6% | 5 | 4 | $0.0012 |
| llama | 1 | 44.4% | 44.4% | 4 | 3 | $0.0003 |
| mistral | 1 | 33.3% | 22.2% | 3 | 4 | $0.0002 |
| qwen | 1 | 33.3% | 33.3% | 3 | 3 | $0.0003 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| OpenAI | 1 | 55.6% | 55.6% | 5 | 4 | $0.0012 |
| Meta | 1 | 44.4% | 44.4% | 4 | 3 | $0.0003 |
| Alibaba/Qwen | 1 | 33.3% | 33.3% | 3 | 3 | $0.0003 |
| Mistral | 1 | 33.3% | 22.2% | 3 | 4 | $0.0002 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| moe | 2 | 44.4% | 44.4% | 8 | 7 | $0.0014 |
| dense | 2 | 38.9% | 33.3% | 7 | 7 | $0.0005 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| Llama-3.3-Community | 1 | 44.4% | 44.4% | 4 | 3 | $0.0003 |
| Apache-2.0 | 3 | 40.7% | 37.0% | 11 | 11 | $0.0016 |

## Canonical case grid

| Sample ID | gpt-oss-20b | llama-3-3-70b | mistral-small-3-2-24b | qwen3-30b |
| --- | --- | --- | --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS | PASS | PASS | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS | PASS | PASS | FAIL |
| `CANONICAL-NIAGARA-ORDERID` | PASS | FAIL | FAIL | PASS |
| `CANONICAL-NIAGARA-PHONE` | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS | PASS | PASS | PASS |
| `CANONICAL-TALKATOO-CENTURY` | PASS | PASS | FAIL | FAIL |

## Per-class accuracy (% judge_pass)

| entity_class | gpt-oss-20b | llama-3-3-70b | mistral-small-3-2-24b | qwen3-30b |
| --- | --- | --- | --- | --- |
| CARDINAL | 50.0% | 50.0% | 50.0% | 50.0% |
| DATE | 100.0% | 100.0% | 0.0% | 0.0% |
| MONEY | 0.0% | 0.0% | 0.0% | 0.0% |
| NUMERIC_ID | 50.0% | 0.0% | 0.0% | 50.0% |
| PERCENT | 100.0% | 100.0% | 100.0% | 0.0% |
| PHONE_NUMBER | 50.0% | 50.0% | 50.0% | 50.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `mistral-small-3-2-24b` | `CANONICAL-RINGCENTRAL-PHONE` | False | pass | judge_pass_em_fail | you can reach us at 800-729-7234 | You can reach us at 800-729-7234 |
