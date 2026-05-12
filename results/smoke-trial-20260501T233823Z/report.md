# Smart-formatting eval — run `smoke-trial-20260501T233823Z`

Judge: `claude-opus-4-7` — total judge cost: $2.5061
Models: 3 | Rows scored: 36

## 1. Headline

| Model | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `claude-haiku-4-5` | 58.3% [31.9-80.7] | 50.0% | 5/9 | 3 | 50.0% | 624 ms | $0.0034 |
| `gpt-4o-mini` | 58.3% [31.9-80.7] | 58.3% | 5/9 | 1 | 25.0% | 555 ms | $0.0004 |
| `gpt-5-4-mini` | 50.0% [25.4-74.6] | 41.7% | 4/9 | 4 | 16.7% | 880 ms | $0.0013 |

## 2. Canonical case grid

| Sample ID | claude-haiku-4-5 | gpt-4o-mini | gpt-5-4-mini |
| --- | --- | --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL | FAIL | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS | PASS | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL | FAIL | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL | PASS | FAIL |
| `CANONICAL-CRESTA-PERCENT` | PASS | PASS | PASS |
| `CANONICAL-NIAGARA-ORDERID` | FAIL | FAIL | PASS |
| `CANONICAL-NIAGARA-PHONE` | PASS | FAIL | FAIL |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS | PASS | PASS |
| `CANONICAL-TALKATOO-CENTURY` | PASS | PASS | FAIL |

## 3. Per-class accuracy (% judge_pass)

| entity_class | claude-haiku-4-5 | gpt-4o-mini | gpt-5-4-mini |
| --- | --- | --- | --- |
| ADVERSARIAL | 0.0% | 0.0% | 100.0% |
| CARDINAL | 50.0% | 50.0% | 50.0% |
| DATE | 100.0% | 100.0% | 50.0% |
| MONEY | 50.0% | 100.0% | 0.0% |
| NUMERIC_ID | 0.0% | 0.0% | 50.0% |
| PERCENT | 100.0% | 100.0% | 100.0% |
| PHONE_NUMBER | 100.0% | 50.0% | 50.0% |

## 4. Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `claude-haiku-4-5` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `gpt-5-4-mini` | `CANONICAL-RINGCENTRAL-PHONE` | False | pass | judge_pass_em_fail | you can reach us at 800-729-7234 | you can reach us at 800 729 7234 |
