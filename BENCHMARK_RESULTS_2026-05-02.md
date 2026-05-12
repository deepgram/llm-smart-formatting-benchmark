# Smart-Formatting Benchmark — Full Results

_Run: `phase1-smoke-20260502T021436Z` — generated 2026-05-02_

**Setup:** 53 candidate LLMs scored on 501 synthetic transcripts covering 12 P0 entity classes (MONEY, DATE, TIME, CARDINAL, PERCENT, PHONE_NUMBER, EMAIL_ADDRESS, URL, NUMERIC_ID, CREDIT_CARD, SSN, ADDRESS), 2 P1 classes (DRUG_WITH_DOSE, DATE_INTERVAL), 33 multi-entity rows, 55 adversarial rows (prompt injection / numeric traps / non-formatting requests / refusals), and 9 verified customer-canonical failure cases (Cresta, Five9, Niagara, RingCentral, Avoma, Talkatoo).

**Judge:** Claude Opus 4.7 (`claude-opus-4-7`), three independent dimensions per row (accuracy, promptability, hallucination). 4-method scoring stack: exact match + regex + reference-scored LLM judge + zero-reference hallucination judge.

**Total spend:** ~$1,812 (judge $1,797 + runner ~$15). Judge calls: 53,106. Run time: ~2h 30min.

## Executive Summary

**Top 10 models overall (judge_pass):**

| # | Model | Vendor | Open-weight | Params | Judge pass | Canonical | Catastrophic |
|---|---|---|---|---|---|---|---|
| 1 | `gpt-5-5` | OpenAI | ✗ | undisclosed / undisclosed | 92.8% | 6/9 | 7 |
| 2 | `gemini-3-flash-preview` | Google | ✗ | undisclosed / undisclosed | 90.8% | 8/9 | 11 |
| 3 | `grok-4` | xAI | ✗ | undisclosed / undisclosed | 90.2% | 7/9 | 14 |
| 4 | `gemini-3-1-pro-preview` | Google | ✗ | undisclosed / undisclosed | 89.0% | 7/9 | 11 |
| 5 | `claude-opus-4-7` | Anthropic | ✗ | undisclosed / undisclosed | 88.6% | 6/9 | 15 |
| 6 | `claude-sonnet-4-6` | Anthropic | ✗ | undisclosed / undisclosed | 85.2% | 7/9 | 15 |
| 7 | `qwen3-32b-groq` | Alibaba/Qwen | ✓ | 32B / 32B | 83.4% | 7/9 | 38 |
| 8 | `nemotron-3-super-120b` | Nvidia | ✓ | 12B / 120B | 81.8% | 7/9 | 44 |
| 9 | `gpt-oss-120b-groq` | OpenAI | ✓ | 5.1B / 117B | 81.0% | 7/9 | 39 |
| 10 | `gpt-5-4-mini` | OpenAI | ✗ | undisclosed / undisclosed | 79.6% | 4/9 | 22 |

**Bottom 5 (judge_pass):**

| Model | Vendor | Params | Judge pass | Canonical | Catastrophic |
|---|---|---|---|---|---|
| `gemma-3-4b-it` | Google | 4B / 4B | 24.1% | 0/9 | 115 |
| `qwen3-5-9b` | Alibaba/Qwen | 9B / 9B | 26.4% | 2/9 | 359 |
| `ministral-3b` | Mistral | 3B / 3B | 31.7% | 2/9 | 106 |
| `llama-3-2-3b` | Meta | 3B / 3B | 33.1% | 2/9 | 157 |
| `mistral-nemo` | Mistral | 12B / 12B | 39.5% | 2/9 | 79 |

**Key takeaways:**

- **Closed frontier still leads on overall accuracy** — `gpt-5-5` (92.8%), `gemini-3-flash-preview` (90.8%), `grok-4` (90.2%) take the top three. ~7-point gap to the best open-weight models.
- **Best canonical performance: `gemini-3-flash-preview` at 8/9** — the only model in the bench to clear more than 7 of the 9 customer-canonical failures. Sub-2s latency to boot.
- **Best open-weight ceiling: ~83%** (`qwen3-32b-groq`). Best non-pinned open-weight: `nemotron-3-super-120b` at 81.8%.
- **Speed/quality champion: `gpt-oss-120b-groq`** — 81.0% judge_pass at **608 ms p50**, $0.07 for the 501-row run. Best production-streaming candidate by latency.
- **Catastrophic failures dominate small models** — under 14B parameters, catastrophic counts explode (50–360) and judge_pass drops below 50%. The MONEY / NUMERIC_ID / SSN classes are the primary failure modes.
- **No model passes Cresta-Account-ID** (`one hundred two oh three oh oh four → 100203004`) — the most consistently-failed canonical case.

## 1. Frontier — Non-Self-Hostable (Closed-Source)

Closed-source proprietary models accessed via vendor APIs (Anthropic / OpenAI / Google / xAI). Parameter counts are not publicly disclosed.

**8 models in this tier.**

| # | Model | Vendor | Params (a/t) | Arch | License | Judge pass | Canonical | Catastrophic | Halluc. any | p50 latency | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `gpt-5-5` | OpenAI | undisclosed / undisclosed | unknown | Proprietary | 92.8% [90-95] | 6/9 | 7 | 12.4% | 1397 ms | $0.516 |
| 2 | `gemini-3-flash-preview` | Google | undisclosed / undisclosed | unknown | Proprietary | 90.8% [88-93] | 8/9 | 11 | 12.2% | 1749 ms | — |
| 3 | `grok-4` | xAI | undisclosed / undisclosed | unknown | Proprietary | 90.2% [87-93] | 7/9 | 14 | 12.0% | 15960 ms | $4.949 |
| 4 | `gemini-3-1-pro-preview` | Google | undisclosed / undisclosed | unknown | Proprietary | 89.0% [86-91] | 7/9 | 11 | 11.0% | 3803 ms | — |
| 5 | `claude-opus-4-7` | Anthropic | undisclosed / undisclosed | unknown | Proprietary | 88.6% [86-91] | 6/9 | 15 | 13.6% | — | — |
| 6 | `claude-sonnet-4-6` | Anthropic | undisclosed / undisclosed | unknown | Proprietary | 85.2% [82-88] | 7/9 | 15 | 14.8% | 1114 ms | — |
| 7 | `gpt-5-4-mini` | OpenAI | undisclosed / undisclosed | unknown | Proprietary | 79.6% [76-83] | 4/9 | 22 | 14.8% | 417 ms | $0.019 |
| 8 | `claude-haiku-4-5` | Anthropic | undisclosed / undisclosed | unknown | Proprietary | 73.8% [70-78] | 5/9 | 43 | 21.6% | 536 ms | — |

## 2. Frontier — Self-Hostable (>200B Parameters)

Open-weight models above 200B total parameters — frontier reference for self-hosting. Mostly MoE architectures with much smaller active-parameter footprints, making them deployable on more accessible hardware than dense models of similar quality.

**6 models in this tier.**

| # | Model | Vendor | Params (a/t) | Arch | License | Judge pass | Canonical | Catastrophic | Halluc. any | p50 latency | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `llama-4-maverick` | Meta | 17B / 400B | moe | Llama-4-Community | 74.2% [70-78] | 5/9 | 46 | 24.6% | 691 ms | $0.027 |
| 2 | `deepseek-v3-2` | DeepSeek | 37B / 685B | moe | MIT | 73.8% [70-78] | 5/9 | 21 | 16.2% | 1975 ms | $0.028 |
| 3 | `qwen3-235b` | Alibaba/Qwen | 22B / 235B | moe | Apache-2.0 | 73.5% [69-77] | 4/9 | 37 | 24.4% | 1195 ms | $0.013 |
| 4 | `qwen3-235b-cerebras` | Alibaba/Qwen | 22B / 235B | moe | Apache-2.0 | 71.5% [67-75] | 5/9 | 36 | 24.4% | 269 ms | — |
| 5 | `deepseek-v3-1-terminus` | DeepSeek | 37B / 685B | moe | MIT | 71.1% [67-75] | 4/9 | 19 | 15.4% | 1621 ms | $0.026 |
| 6 | `qwen3-5-397b` | Alibaba/Qwen | 17B / 397B | moe | Apache-2.0 | 69.5% [65-73] | 6/9 | 134 | 33.3% | 17988 ms | — |

## 3. Large Self-Hostable (50–200B)

Open-weight models 50–200B total parameters — large-tier self-hostable. This tier is where many of the practical production candidates sit (good quality, deployable on a single high-end node or modest cluster).

**13 models in this tier.**

| # | Model | Vendor | Params (a/t) | Arch | License | Judge pass | Canonical | Catastrophic | Halluc. any | p50 latency | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `nemotron-3-super-120b` | Nvidia | 12B / 120B | moe | Nvidia-Open-Model | 81.8% [78-85] | 7/9 | 44 | 19.0% | 6418 ms | $0.042 |
| 2 | `gpt-oss-120b-groq` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 81.0% [77-84] | 7/9 | 39 | 15.2% | 607 ms | $0.072 |
| 3 | `gpt-oss-120b` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 79.4% [76-83] | 4/9 | 45 | 18.6% | 3175 ms | $0.035 |
| 4 | `qwen3-5-122b` | Alibaba/Qwen | 10B / 122B | moe | Apache-2.0 | 77.6% [74-81] | 7/9 | 62 | 23.9% | 13897 ms | $3.807 |
| 5 | `qwen3-next-80b` | Alibaba/Qwen | 3B / 80B | moe | Apache-2.0 | 75.7% [72-79] | 6/9 | 31 | 18.2% | 624 ms | $0.018 |
| 6 | `mistral-small-2603` | Mistral | 6B / 119B | moe | Apache-2.0 | 73.0% [69-77] | 5/9 | 36 | 25.8% | 604 ms | $0.015 |
| 7 | `gpt-oss-120b-cerebras` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 72.7% [69-76] | 6/9 | 42 | 25.8% | 401 ms | $0.113 |
| 8 | `llama-3-3-70b` | Meta | 70B / 70B | dense | Llama-3.3-Community | 69.7% [66-74] | 5/9 | 72 | 26.9% | 552 ms | — |
| 9 | `llama-3-1-70b` | Meta | 70B / 70B | dense | Llama-3.1-Community | 68.5% [64-72] | 7/9 | 78 | 28.5% | 505 ms | $0.051 |
| 10 | `llama-3-3-70b-groq` | Meta | 70B / 70B | dense | Llama-3.3-Community | 67.7% [63-72] | 5/9 | 77 | 29.1% | 358 ms | $0.071 |
| 11 | `llama-4-scout-groq` | Meta | 17B / 109B | moe | Llama-4-Community | 60.5% [56-65] | 3/9 | 65 | 29.3% | 257 ms | $0.013 |
| 12 | `nemotron-llama-3-1-70b` | Nvidia | 70B / 70B | dense | Nvidia-Open-Model | 56.5% [52-61] | 4/9 | 94 | 44.7% | 626 ms | $0.136 |
| 13 | `llama-4-scout` | Meta | 17B / 109B | moe | Llama-4-Community | 56.5% [52-61] | 5/9 | 72 | 32.9% | 373 ms | $0.013 |

## 4. Mid Self-Hostable (20–50B)

Open-weight models 20–50B total parameters — the sweet-spot tier for streaming voice-agent deployments. MoE variants here can serve at small-model latency with mid-model quality.

**11 models in this tier.**

| # | Model | Vendor | Params (a/t) | Arch | License | Judge pass | Canonical | Catastrophic | Halluc. any | p50 latency | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `qwen3-32b-groq` | Alibaba/Qwen | 32B / 32B | dense | Apache-2.0 | 83.4% [80-86] | 7/9 | 38 | 18.6% | 1409 ms | $0.142 |
| 2 | `qwen3-5-27b` | Alibaba/Qwen | 27B / 27B | dense | Apache-2.0 | 75.5% [72-79] | 5/9 | 87 | 25.9% | 12625 ms | $2.370 |
| 3 | `gpt-oss-20b` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 75.5% [72-79] | 5/9 | 57 | 21.0% | 2164 ms | $0.034 |
| 4 | `gpt-oss-20b-groq` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 75.2% [71-79] | 5/9 | 55 | 20.4% | 620 ms | $0.043 |
| 5 | `nemotron-3-nano-30b` | Nvidia | 3B / 30B | moe | Nvidia-Open-Model | 73.0% [69-77] | 6/9 | 53 | 20.6% | 4426 ms | $0.040 |
| 6 | `mistral-small-3-2-24b` | Mistral | 24B / 24B | dense | Apache-2.0 | 72.5% [68-76] | 3/9 | 37 | 26.4% | 437 ms | $0.0093 |
| 7 | `gemma-3-27b-it` | Google | 27B / 27B | dense | Gemma-Terms | 69.5% [65-73] | 6/9 | 49 | 22.9% | 837 ms | $0.010 |
| 8 | `olmo-3-1-32b` | Allen AI | 32B / 32B | dense | Apache-2.0 | 66.3% [62-70] | 5/9 | 66 | 26.8% | 358 ms | $0.023 |
| 9 | `nemotron-super-49b` | Nvidia | 49B / 49B | dense | Nvidia-Open-Model | 61.7% [57-66] | 3/9 | 139 | 33.9% | 8967 ms | $0.125 |
| 10 | `qwen3-30b` | Alibaba/Qwen | 3B / 30B | moe | Apache-2.0 | 60.7% [56-65] | 3/9 | 47 | 23.6% | 1036 ms | $0.012 |
| 11 | `qwen3-5-35b` | Alibaba/Qwen | 3B / 35B | moe | Apache-2.0 | 39.7% [36-44] | 1/9 | 275 | 59.9% | 8703 ms | $1.994 |

## 5. Small Self-Hostable (5–20B)

Open-weight models 5–20B total parameters — cost-baseline tier. Note the steep drop in quality and the explosion in catastrophic counts; these models are NOT safe for the formatting task without fine-tuning.

**11 models in this tier.**

| # | Model | Vendor | Params (a/t) | Arch | License | Judge pass | Canonical | Catastrophic | Halluc. any | p50 latency | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `qwen3-14b` | Alibaba/Qwen | 14B / 14B | dense | Apache-2.0 | 74.5% [70-78] | 6/9 | 49 | 20.0% | 11775 ms | $0.091 |
| 2 | `nemotron-nano-9b` | Nvidia | 9B / 9B | dense | Nvidia-Open-Model | 67.1% [63-71] | 5/9 | 64 | 26.4% | 3746 ms | $0.037 |
| 3 | `qwen3-8b` | Alibaba/Qwen | 8B / 8B | dense | Apache-2.0 | 66.7% [62-71] | 6/9 | 43 | 19.2% | 7201 ms | $0.131 |
| 4 | `granite-4-1-8b` | IBM | 8B / 8B | dense | Apache-2.0 | 57.5% [53-62] | 3/9 | 92 | 35.9% | 255 ms | $0.0059 |
| 5 | `gemma-3-12b-it` | Google | 12B / 12B | dense | Gemma-Terms | 55.9% [52-60] | 5/9 | 63 | 29.7% | 554 ms | $0.0069 |
| 6 | `ministral-14b` | Mistral | 14B / 14B | dense | Apache-2.0 | 47.7% [43-52] | 4/9 | 52 | 39.9% | 542 ms | — |
| 7 | `phi-4` | Microsoft | 14B / 14B | dense | MIT | 45.3% [41-50] | 1/9 | 123 | 45.9% | 636 ms | $0.0083 |
| 8 | `llama-3-1-8b` | Meta | 8B / 8B | dense | Llama-3.1-Community | 44.7% [40-49] | 1/9 | 118 | 39.9% | 587 ms | $0.0030 |
| 9 | `ministral-8b` | Mistral | 8B / 8B | dense | Apache-2.0 | 42.7% [38-47] | 4/9 | 66 | 46.7% | 568 ms | — |
| 10 | `mistral-nemo` | Mistral | 12B / 12B | dense | Apache-2.0 | 39.5% [35-44] | 2/9 | 79 | 54.5% | 1072 ms | $0.0026 |
| 11 | `qwen3-5-9b` | Alibaba/Qwen | 9B / 9B | dense | Apache-2.0 | 26.4% [23-30] | 2/9 | 359 | 74.7% | 7148 ms | $0.079 |

## 6. Tiny Self-Hostable (<5B)

Open-weight models under 5B parameters — edge/fine-tune candidates. Performance here is poor across the board, but these are useful as fine-tuning starting points or as cost-floor references.

**4 models in this tier.**

| # | Model | Vendor | Params (a/t) | Arch | License | Judge pass | Canonical | Catastrophic | Halluc. any | p50 latency | Cost (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `granite-4-0-h-micro` | IBM | 3B / 3B | dense | Apache-2.0 | 48.3% [44-53] | 4/9 | 124 | 34.1% | 738 ms | $0.0023 |
| 2 | `llama-3-2-3b` | Meta | 3B / 3B | dense | Llama-3.2-Community | 33.1% [29-37] | 2/9 | 157 | 54.9% | 493 ms | $0.0070 |
| 3 | `ministral-3b` | Mistral | 3B / 3B | dense | Apache-2.0 | 31.7% [28-36] | 2/9 | 106 | 53.1% | 493 ms | $0.0085 |
| 4 | `gemma-3-4b-it` | Google | 4B / 4B | dense | Gemma-Terms | 24.1% [21-28] | 0/9 | 115 | 40.5% | 377 ms | $0.0048 |

## 7. Speed-Tier Pinned Variants (Groq / Cerebras)

Side-by-side comparison of the same base model under default OR routing vs. pinned to a speed-tier provider. The pinning costs roughly the same on a per-token basis but delivers 1.5–4× lower p50 latency.

| Base model | Default p50 | Default judge_pass | Groq p50 | Groq judge_pass | Cerebras p50 | Cerebras judge_pass |
|---|---|---|---|---|---|---|
| `llama-3-3-70b` | 552 ms | 69.7% | 358 ms | 67.7% | — | — |
| `llama-4-scout` | 373 ms | 56.5% | 257 ms | 60.5% | — | — |
| `gpt-oss-120b` | 3175 ms | 79.4% | 607 ms | 81.0% | 401 ms | 72.7% |
| `gpt-oss-20b` | 2164 ms | 75.5% | 620 ms | 75.2% | — | — |
| `qwen3-235b` | 1195 ms | 73.5% | — | — | 269 ms | 71.5% |

## 8. Customer-Canonical Case Grid

Pass/fail per model on the 9 verified production failure cases. **No row is optional** — these represent real customer-blocking failures from $13.85M ARR worth of accounts.

**Pass rate per canonical case (across all 53 models):**

| Canonical case | Pass count | Pass rate |
|---|---|---|
| `CANONICAL-CRESTA-PERCENT` | 46 / 53 | 86.8% |
| `CANONICAL-AVOMA-YEAR` | 45 / 53 | 84.9% |
| `CANONICAL-RINGCENTRAL-PHONE` | 35 / 53 | 66.0% |
| `CANONICAL-NIAGARA-ORDERID` | 33 / 53 | 62.3% |
| `CANONICAL-TALKATOO-CENTURY` | 31 / 53 | 58.5% |
| `CANONICAL-CRESTA-CURRENCY` | 27 / 53 | 50.9% |
| `CANONICAL-NIAGARA-PHONE` | 22 / 53 | 41.5% |
| `CANONICAL-AVOMA-RANGE` | 6 / 53 | 11.3% |
| `CANONICAL-CRESTA-ACCOUNT-ID` | 1 / 53 | 1.9% |

**Models that pass the most canonical cases:**

| Model | Canonical | Judge pass | Catastrophic |
|---|---|---|---|
| `gemini-3-flash-preview` | 8/9 | 90.8% | 11 |
| `grok-4` | 7/9 | 90.2% | 14 |
| `gemini-3-1-pro-preview` | 7/9 | 89.0% | 11 |
| `claude-sonnet-4-6` | 7/9 | 85.2% | 15 |
| `qwen3-32b-groq` | 7/9 | 83.4% | 38 |
| `nemotron-3-super-120b` | 7/9 | 81.8% | 44 |
| `gpt-oss-120b-groq` | 7/9 | 81.0% | 39 |
| `qwen3-5-122b` | 7/9 | 77.6% | 62 |
| `llama-3-1-70b` | 7/9 | 68.5% | 78 |
| `gpt-5-5` | 6/9 | 92.8% | 7 |
| `claude-opus-4-7` | 6/9 | 88.6% | 15 |
| `qwen3-next-80b` | 6/9 | 75.7% | 31 |
| `qwen3-14b` | 6/9 | 74.5% | 49 |
| `nemotron-3-nano-30b` | 6/9 | 73.0% | 53 |
| `gpt-oss-120b-cerebras` | 6/9 | 72.7% | 42 |

## 9. Per-Entity-Class Accuracy

Average judge_pass rate per entity class, across all 53 models. Lower numbers = more universally hard for the formatter family.

| Entity class | Mean judge_pass | Total rows |
|---|---|---|
| `DRUG_WITH_DOSE` | 86.9% | 795 |
| `DATE_INTERVAL` | 84.0% | 530 |
| `DATE` | 81.9% | 2597 |
| `URL` | 74.9% | 1219 |
| `PERCENT` | 74.4% | 1484 |
| `CARDINAL` | 72.9% | 2173 |
| `ADDRESS` | 72.5% | 1484 |
| `MONEY` | 69.7% | 2173 |
| `PHONE_NUMBER` | 69.2% | 2279 |
| `TIME` | 65.0% | 1590 |
| `SSN` | 64.4% | 795 |
| `MIXED` | 58.0% | 1749 |
| `NUMERIC_ID` | 54.9% | 2226 |
| `EMAIL_ADDRESS` | 54.6% | 1484 |
| `ADVERSARIAL` | 49.6% | 2915 |
| `CREDIT_CARD` | 44.7% | 1060 |

## 10. Cost & Latency Summary

Five fastest models (by p50 latency) above 70% judge_pass:

| Model | p50 latency | Judge pass | Catastrophic | Cost (USD) |
|---|---|---|---|---|
| `qwen3-235b-cerebras` | 269 ms | 71.5% | 36 | — |
| `gpt-oss-120b-cerebras` | 401 ms | 72.7% | 42 | $0.113 |
| `gpt-5-4-mini` | 417 ms | 79.6% | 22 | $0.019 |
| `mistral-small-3-2-24b` | 437 ms | 72.5% | 37 | $0.0093 |
| `claude-haiku-4-5` | 536 ms | 73.8% | 43 | — |
| `mistral-small-2603` | 604 ms | 73.0% | 36 | $0.015 |
| `gpt-oss-120b-groq` | 607 ms | 81.0% | 39 | $0.072 |
| `gpt-oss-20b-groq` | 620 ms | 75.2% | 55 | $0.043 |

## Methodology Notes

- **Scoring:** 4 independent methods per row (exact match, regex when applicable, LLM-judge with reference, LLM-judge no-reference for hallucination). Headlines use the LLM-judge reference-scored result. Wilson 95% CIs on every proportion. See `evaluator/aggregate.py` for math.
- **Catastrophic** = numeric drift on MONEY / CARDINAL / PERCENT / PHONE_NUMBER / NUMERIC_ID / CREDIT_CARD / SSN, OR digit drop/add/substitute on a numeric entity, OR refusal on a non-adversarial row.
- **Canonical case** = verified customer-reported production failure. 9 cases from Cresta (×3), Niagara (×2), RingCentral, Avoma (×2), Talkatoo. Five9 French-`un` case excluded (Phase 1 is EN-only).
- **Judge:** Claude Opus 4.7. Single judge this run; methodology doc proposes 3-judge ensemble for Phase 2 directional cycles.
- **Latency / cost gaps for Anthropic native models:** TTFT capture not yet wired in the Anthropic streaming client — known bug, listed for fix.
- **Determinism note:** `gpt-5-5` and `claude-opus-4-7` were run with `temperature=1` (vendor constraint), so their results are non-deterministic. All other models ran at `temperature=0`.