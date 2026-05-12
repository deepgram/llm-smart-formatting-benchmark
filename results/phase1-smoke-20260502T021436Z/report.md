# Smart-formatting eval — run `phase1-smoke-20260502T021436Z`

Judge: `claude-opus-4-7` — total judge cost: $1797.4202
Models: 53 | Rows scored: 26553

## 1. Headline

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gpt-5-5` | OpenAI | undisclosed / undisclosed | unknown | Proprietary | 92.8% [90.2-94.8] | 75.2% | 6/9 | 7 | 12.4% | 1398 ms | $0.5165 |
| `gemini-3-flash-preview` | — | — / — | — | — | 90.8% [88.0-93.0] | 75.7% | 8/9 | 11 | 12.2% | 1749 ms | — |
| `grok-4` | xAI | undisclosed / undisclosed | unknown | Proprietary | 90.2% [87.3-92.5] | 73.0% | 7/9 | 14 | 12.0% | 15960 ms | $4.9494 |
| `gemini-3-1-pro-preview` | — | — / — | — | — | 89.0% [86.0-91.5] | 69.5% | 7/9 | 11 | 11.0% | 3804 ms | — |
| `claude-opus-4-7` | Anthropic | undisclosed / undisclosed | unknown | Proprietary | 88.6% [85.5-91.1] | 59.9% | 6/9 | 15 | 13.6% | — | — |
| `claude-sonnet-4-6` | Anthropic | undisclosed / undisclosed | unknown | Proprietary | 85.2% [81.8-88.1] | 60.7% | 7/9 | 15 | 14.8% | 1114 ms | — |
| `qwen3-32b-groq` | Alibaba/Qwen | 32B / 32B | dense | Apache-2.0 | 83.4% [79.9-86.4] | 67.9% | 7/9 | 38 | 18.6% | 1410 ms | $0.1423 |
| `nemotron-3-super-120b` | Nvidia | 12B / 120B | moe | Nvidia-Open-Model | 81.8% [78.2-85.0] | 68.7% | 7/9 | 44 | 19.0% | 6418 ms | $0.0418 |
| `gpt-oss-120b-groq` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 81.0% [77.4-84.2] | 69.3% | 7/9 | 39 | 15.2% | 608 ms | $0.0721 |
| `gpt-5-4-mini` | OpenAI | undisclosed / undisclosed | unknown | Proprietary | 79.6% [75.9-82.9] | 62.7% | 4/9 | 22 | 14.8% | 417 ms | $0.0186 |
| `gpt-oss-120b` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 79.4% [75.7-82.8] | 67.9% | 4/9 | 45 | 18.6% | 3176 ms | $0.0347 |
| `qwen3-5-122b` | Alibaba/Qwen | 10B / 122B | moe | Apache-2.0 | 77.6% [73.8-81.1] | 64.5% | 7/9 | 62 | 23.9% | 13898 ms | $3.8069 |
| `qwen3-next-80b` | Alibaba/Qwen | 3B / 80B | moe | Apache-2.0 | 75.7% [71.7-79.2] | 60.3% | 6/9 | 31 | 18.2% | 624 ms | $0.0177 |
| `qwen3-5-27b` | Alibaba/Qwen | 27B / 27B | dense | Apache-2.0 | 75.5% [71.5-79.0] | 58.1% | 5/9 | 87 | 25.9% | 12625 ms | $2.3698 |
| `gpt-oss-20b` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 75.5% [71.5-79.0] | 64.9% | 5/9 | 57 | 21.0% | 2164 ms | $0.0339 |
| `gpt-oss-20b-groq` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 75.2% [71.3-78.8] | 64.5% | 5/9 | 55 | 20.4% | 620 ms | $0.0431 |
| `qwen3-14b` | Alibaba/Qwen | 14B / 14B | dense | Apache-2.0 | 74.5% [70.5-78.1] | 58.9% | 6/9 | 49 | 20.0% | 11776 ms | $0.0910 |
| `llama-4-maverick` | Meta | 17B / 400B | moe | Llama-4-Community | 74.2% [70.2-77.9] | 58.9% | 5/9 | 46 | 24.6% | 691 ms | $0.0267 |
| `claude-haiku-4-5` | Anthropic | undisclosed / undisclosed | unknown | Proprietary | 73.8% [69.8-77.5] | 55.7% | 5/9 | 43 | 21.6% | 536 ms | — |
| `deepseek-v3-2` | DeepSeek | 37B / 685B | moe | MIT | 73.8% [69.8-77.5] | 59.7% | 5/9 | 21 | 16.2% | 1976 ms | $0.0276 |
| `qwen3-235b` | Alibaba/Qwen | 22B / 235B | moe | Apache-2.0 | 73.5% [69.4-77.1] | 58.1% | 4/9 | 37 | 24.4% | 1195 ms | $0.0129 |
| `mistral-small-2603` | Mistral | 6B / 119B | moe | Apache-2.0 | 73.0% [69.0-76.8] | 30.7% | 5/9 | 36 | 25.8% | 605 ms | $0.0147 |
| `nemotron-3-nano-30b` | Nvidia | 3B / 30B | moe | Nvidia-Open-Model | 73.0% [69.0-76.8] | 63.1% | 6/9 | 53 | 20.6% | 4426 ms | $0.0396 |
| `gpt-oss-120b-cerebras` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 72.7% [68.6-76.4] | 62.7% | 6/9 | 42 | 25.8% | 402 ms | $0.1134 |
| `mistral-small-3-2-24b` | Mistral | 24B / 24B | dense | Apache-2.0 | 72.5% [68.4-76.2] | 46.3% | 3/9 | 37 | 26.4% | 437 ms | $0.0093 |
| `qwen3-235b-cerebras` | Alibaba/Qwen | 22B / 235B | moe | Apache-2.0 | 71.5% [67.3-75.2] | 52.9% | 5/9 | 36 | 24.4% | 269 ms | — |
| `deepseek-v3-1-terminus` | DeepSeek | 37B / 685B | moe | MIT | 71.1% [66.9-74.9] | 59.7% | 4/9 | 19 | 15.4% | 1621 ms | $0.0264 |
| `llama-3-3-70b` | Meta | 70B / 70B | dense | Llama-3.3-Community | 69.7% [65.5-73.5] | 48.3% | 5/9 | 72 | 26.9% | 552 ms | — |
| `gemma-3-27b-it` | Google | 27B / 27B | dense | Gemma-Terms | 69.5% [65.3-73.3] | 50.5% | 6/9 | 49 | 22.9% | 837 ms | $0.0104 |
| `qwen3-5-397b` | Alibaba/Qwen | 17B / 397B | moe | Apache-2.0 | 69.5% [65.3-73.3] | 59.9% | 6/9 | 134 | 33.3% | 17988 ms | — |
| `llama-3-1-70b` | Meta | 70B / 70B | dense | Llama-3.1-Community | 68.5% [64.3-72.4] | 39.3% | 7/9 | 78 | 28.5% | 506 ms | $0.0511 |
| `llama-3-3-70b-groq` | Meta | 70B / 70B | dense | Llama-3.3-Community | 67.7% [63.5-71.6] | 45.5% | 5/9 | 77 | 29.1% | 358 ms | $0.0708 |
| `nemotron-nano-9b` | Nvidia | 9B / 9B | dense | Nvidia-Open-Model | 67.1% [62.8-71.0] | 52.5% | 5/9 | 64 | 26.4% | 3746 ms | $0.0374 |
| `qwen3-8b` | Alibaba/Qwen | 8B / 8B | dense | Apache-2.0 | 66.7% [62.4-70.7] | 51.1% | 6/9 | 43 | 19.2% | 7201 ms | $0.1306 |
| `olmo-3-1-32b` | Allen AI | 32B / 32B | dense | Apache-2.0 | 66.3% [62.0-70.3] | 52.9% | 5/9 | 66 | 26.8% | 359 ms | $0.0233 |
| `nemotron-super-49b` | Nvidia | 49B / 49B | dense | Nvidia-Open-Model | 61.7% [57.4-65.8] | 51.1% | 3/9 | 139 | 33.9% | 8967 ms | $0.1252 |
| `qwen3-30b` | Alibaba/Qwen | 3B / 30B | moe | Apache-2.0 | 60.7% [56.3-64.9] | 46.7% | 3/9 | 47 | 23.6% | 1036 ms | $0.0118 |
| `llama-4-scout-groq` | Meta | 17B / 109B | moe | Llama-4-Community | 60.5% [56.1-64.7] | 45.5% | 3/9 | 65 | 29.3% | 258 ms | $0.0131 |
| `granite-4-1-8b` | IBM | 8B / 8B | dense | Apache-2.0 | 57.5% [53.1-61.7] | 43.7% | 3/9 | 92 | 35.9% | 255 ms | $0.0059 |
| `nemotron-llama-3-1-70b` | Nvidia | 70B / 70B | dense | Nvidia-Open-Model | 56.5% [52.1-60.8] | 32.1% | 4/9 | 94 | 44.7% | 626 ms | $0.1356 |
| `llama-4-scout` | Meta | 17B / 109B | moe | Llama-4-Community | 56.5% [52.1-60.8] | 39.7% | 5/9 | 72 | 32.9% | 374 ms | $0.0133 |
| `gemma-3-12b-it` | Google | 12B / 12B | dense | Gemma-Terms | 55.9% [51.5-60.2] | 41.1% | 5/9 | 63 | 29.7% | 554 ms | $0.0069 |
| `granite-4-0-h-micro` | IBM | 3B / 3B | dense | Apache-2.0 | 48.3% [44.0-52.7] | 34.9% | 4/9 | 124 | 34.1% | 738 ms | $0.0023 |
| `ministral-14b` | Mistral | 14B / 14B | dense | Apache-2.0 | 47.7% [43.4-52.1] | 17.8% | 4/9 | 52 | 39.9% | 542 ms | — |
| `phi-4` | Microsoft | 14B / 14B | dense | MIT | 45.3% [41.0-49.7] | 31.1% | 1/9 | 123 | 45.9% | 637 ms | $0.0083 |
| `llama-3-1-8b` | Meta | 8B / 8B | dense | Llama-3.1-Community | 44.7% [40.4-49.1] | 22.2% | 1/9 | 118 | 39.9% | 587 ms | $0.0030 |
| `ministral-8b` | Mistral | 8B / 8B | dense | Apache-2.0 | 42.7% [38.5-47.1] | 15.0% | 4/9 | 66 | 46.7% | 568 ms | — |
| `qwen3-5-35b` | Alibaba/Qwen | 3B / 35B | moe | Apache-2.0 | 39.7% [35.5-44.1] | 34.1% | 1/9 | 275 | 59.9% | 8703 ms | $1.9939 |
| `mistral-nemo` | Mistral | 12B / 12B | dense | Apache-2.0 | 39.5% [35.3-43.9] | 22.4% | 2/9 | 79 | 54.5% | 1073 ms | $0.0026 |
| `llama-3-2-3b` | Meta | 3B / 3B | dense | Llama-3.2-Community | 33.1% [29.1-37.4] | 17.0% | 2/9 | 157 | 54.9% | 494 ms | $0.0070 |
| `ministral-3b` | Mistral | 3B / 3B | dense | Apache-2.0 | 31.7% [27.8-35.9] | 16.0% | 2/9 | 106 | 53.1% | 493 ms | $0.0085 |
| `qwen3-5-9b` | Alibaba/Qwen | 9B / 9B | dense | Apache-2.0 | 26.4% [22.7-30.4] | 25.6% | 2/9 | 359 | 74.7% | 7148 ms | $0.0790 |
| `gemma-3-4b-it` | Google | 4B / 4B | dense | Gemma-Terms | 24.1% [20.6-28.1] | 16.8% | 0/9 | 115 | 40.5% | 378 ms | $0.0048 |

## 2. Open-weight only (sorted desc by judge_pass)

| Model | Vendor | Params (active/total) | Arch | License | Judge pass [95% CI] | Exact match | Canonical | Catastrophic | Halluc. any | Latency p50 | Cost (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen3-32b-groq` | Alibaba/Qwen | 32B / 32B | dense | Apache-2.0 | 83.4% [79.9-86.4] | 67.9% | 7/9 | 38 | 18.6% | 1410 ms | $0.1423 |
| `nemotron-3-super-120b` | Nvidia | 12B / 120B | moe | Nvidia-Open-Model | 81.8% [78.2-85.0] | 68.7% | 7/9 | 44 | 19.0% | 6418 ms | $0.0418 |
| `gpt-oss-120b-groq` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 81.0% [77.4-84.2] | 69.3% | 7/9 | 39 | 15.2% | 608 ms | $0.0721 |
| `gpt-oss-120b` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 79.4% [75.7-82.8] | 67.9% | 4/9 | 45 | 18.6% | 3176 ms | $0.0347 |
| `qwen3-5-122b` | Alibaba/Qwen | 10B / 122B | moe | Apache-2.0 | 77.6% [73.8-81.1] | 64.5% | 7/9 | 62 | 23.9% | 13898 ms | $3.8069 |
| `qwen3-next-80b` | Alibaba/Qwen | 3B / 80B | moe | Apache-2.0 | 75.7% [71.7-79.2] | 60.3% | 6/9 | 31 | 18.2% | 624 ms | $0.0177 |
| `qwen3-5-27b` | Alibaba/Qwen | 27B / 27B | dense | Apache-2.0 | 75.5% [71.5-79.0] | 58.1% | 5/9 | 87 | 25.9% | 12625 ms | $2.3698 |
| `gpt-oss-20b` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 75.5% [71.5-79.0] | 64.9% | 5/9 | 57 | 21.0% | 2164 ms | $0.0339 |
| `gpt-oss-20b-groq` | OpenAI | 3.6B / 21B | moe | Apache-2.0 | 75.2% [71.3-78.8] | 64.5% | 5/9 | 55 | 20.4% | 620 ms | $0.0431 |
| `qwen3-14b` | Alibaba/Qwen | 14B / 14B | dense | Apache-2.0 | 74.5% [70.5-78.1] | 58.9% | 6/9 | 49 | 20.0% | 11776 ms | $0.0910 |
| `llama-4-maverick` | Meta | 17B / 400B | moe | Llama-4-Community | 74.2% [70.2-77.9] | 58.9% | 5/9 | 46 | 24.6% | 691 ms | $0.0267 |
| `deepseek-v3-2` | DeepSeek | 37B / 685B | moe | MIT | 73.8% [69.8-77.5] | 59.7% | 5/9 | 21 | 16.2% | 1976 ms | $0.0276 |
| `qwen3-235b` | Alibaba/Qwen | 22B / 235B | moe | Apache-2.0 | 73.5% [69.4-77.1] | 58.1% | 4/9 | 37 | 24.4% | 1195 ms | $0.0129 |
| `mistral-small-2603` | Mistral | 6B / 119B | moe | Apache-2.0 | 73.0% [69.0-76.8] | 30.7% | 5/9 | 36 | 25.8% | 605 ms | $0.0147 |
| `nemotron-3-nano-30b` | Nvidia | 3B / 30B | moe | Nvidia-Open-Model | 73.0% [69.0-76.8] | 63.1% | 6/9 | 53 | 20.6% | 4426 ms | $0.0396 |
| `gpt-oss-120b-cerebras` | OpenAI | 5.1B / 117B | moe | Apache-2.0 | 72.7% [68.6-76.4] | 62.7% | 6/9 | 42 | 25.8% | 402 ms | $0.1134 |
| `mistral-small-3-2-24b` | Mistral | 24B / 24B | dense | Apache-2.0 | 72.5% [68.4-76.2] | 46.3% | 3/9 | 37 | 26.4% | 437 ms | $0.0093 |
| `qwen3-235b-cerebras` | Alibaba/Qwen | 22B / 235B | moe | Apache-2.0 | 71.5% [67.3-75.2] | 52.9% | 5/9 | 36 | 24.4% | 269 ms | — |
| `deepseek-v3-1-terminus` | DeepSeek | 37B / 685B | moe | MIT | 71.1% [66.9-74.9] | 59.7% | 4/9 | 19 | 15.4% | 1621 ms | $0.0264 |
| `llama-3-3-70b` | Meta | 70B / 70B | dense | Llama-3.3-Community | 69.7% [65.5-73.5] | 48.3% | 5/9 | 72 | 26.9% | 552 ms | — |
| `gemma-3-27b-it` | Google | 27B / 27B | dense | Gemma-Terms | 69.5% [65.3-73.3] | 50.5% | 6/9 | 49 | 22.9% | 837 ms | $0.0104 |
| `qwen3-5-397b` | Alibaba/Qwen | 17B / 397B | moe | Apache-2.0 | 69.5% [65.3-73.3] | 59.9% | 6/9 | 134 | 33.3% | 17988 ms | — |
| `llama-3-1-70b` | Meta | 70B / 70B | dense | Llama-3.1-Community | 68.5% [64.3-72.4] | 39.3% | 7/9 | 78 | 28.5% | 506 ms | $0.0511 |
| `llama-3-3-70b-groq` | Meta | 70B / 70B | dense | Llama-3.3-Community | 67.7% [63.5-71.6] | 45.5% | 5/9 | 77 | 29.1% | 358 ms | $0.0708 |
| `nemotron-nano-9b` | Nvidia | 9B / 9B | dense | Nvidia-Open-Model | 67.1% [62.8-71.0] | 52.5% | 5/9 | 64 | 26.4% | 3746 ms | $0.0374 |
| `qwen3-8b` | Alibaba/Qwen | 8B / 8B | dense | Apache-2.0 | 66.7% [62.4-70.7] | 51.1% | 6/9 | 43 | 19.2% | 7201 ms | $0.1306 |
| `olmo-3-1-32b` | Allen AI | 32B / 32B | dense | Apache-2.0 | 66.3% [62.0-70.3] | 52.9% | 5/9 | 66 | 26.8% | 359 ms | $0.0233 |
| `nemotron-super-49b` | Nvidia | 49B / 49B | dense | Nvidia-Open-Model | 61.7% [57.4-65.8] | 51.1% | 3/9 | 139 | 33.9% | 8967 ms | $0.1252 |
| `qwen3-30b` | Alibaba/Qwen | 3B / 30B | moe | Apache-2.0 | 60.7% [56.3-64.9] | 46.7% | 3/9 | 47 | 23.6% | 1036 ms | $0.0118 |
| `llama-4-scout-groq` | Meta | 17B / 109B | moe | Llama-4-Community | 60.5% [56.1-64.7] | 45.5% | 3/9 | 65 | 29.3% | 258 ms | $0.0131 |
| `granite-4-1-8b` | IBM | 8B / 8B | dense | Apache-2.0 | 57.5% [53.1-61.7] | 43.7% | 3/9 | 92 | 35.9% | 255 ms | $0.0059 |
| `nemotron-llama-3-1-70b` | Nvidia | 70B / 70B | dense | Nvidia-Open-Model | 56.5% [52.1-60.8] | 32.1% | 4/9 | 94 | 44.7% | 626 ms | $0.1356 |
| `llama-4-scout` | Meta | 17B / 109B | moe | Llama-4-Community | 56.5% [52.1-60.8] | 39.7% | 5/9 | 72 | 32.9% | 374 ms | $0.0133 |
| `gemma-3-12b-it` | Google | 12B / 12B | dense | Gemma-Terms | 55.9% [51.5-60.2] | 41.1% | 5/9 | 63 | 29.7% | 554 ms | $0.0069 |
| `granite-4-0-h-micro` | IBM | 3B / 3B | dense | Apache-2.0 | 48.3% [44.0-52.7] | 34.9% | 4/9 | 124 | 34.1% | 738 ms | $0.0023 |
| `ministral-14b` | Mistral | 14B / 14B | dense | Apache-2.0 | 47.7% [43.4-52.1] | 17.8% | 4/9 | 52 | 39.9% | 542 ms | — |
| `phi-4` | Microsoft | 14B / 14B | dense | MIT | 45.3% [41.0-49.7] | 31.1% | 1/9 | 123 | 45.9% | 637 ms | $0.0083 |
| `llama-3-1-8b` | Meta | 8B / 8B | dense | Llama-3.1-Community | 44.7% [40.4-49.1] | 22.2% | 1/9 | 118 | 39.9% | 587 ms | $0.0030 |
| `ministral-8b` | Mistral | 8B / 8B | dense | Apache-2.0 | 42.7% [38.5-47.1] | 15.0% | 4/9 | 66 | 46.7% | 568 ms | — |
| `qwen3-5-35b` | Alibaba/Qwen | 3B / 35B | moe | Apache-2.0 | 39.7% [35.5-44.1] | 34.1% | 1/9 | 275 | 59.9% | 8703 ms | $1.9939 |
| `mistral-nemo` | Mistral | 12B / 12B | dense | Apache-2.0 | 39.5% [35.3-43.9] | 22.4% | 2/9 | 79 | 54.5% | 1073 ms | $0.0026 |
| `llama-3-2-3b` | Meta | 3B / 3B | dense | Llama-3.2-Community | 33.1% [29.1-37.4] | 17.0% | 2/9 | 157 | 54.9% | 494 ms | $0.0070 |
| `ministral-3b` | Mistral | 3B / 3B | dense | Apache-2.0 | 31.7% [27.8-35.9] | 16.0% | 2/9 | 106 | 53.1% | 493 ms | $0.0085 |
| `qwen3-5-9b` | Alibaba/Qwen | 9B / 9B | dense | Apache-2.0 | 26.4% [22.7-30.4] | 25.6% | 2/9 | 359 | 74.7% | 7148 ms | $0.0790 |
| `gemma-3-4b-it` | Google | 4B / 4B | dense | Gemma-Terms | 24.1% [20.6-28.1] | 16.8% | 0/9 | 115 | 40.5% | 378 ms | $0.0048 |

## Grouped by Family

| Family | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| grok | 1 | 90.2% | 73.0% | 7 | 14 | $4.9494 |
| — | 2 | 89.9% | 72.6% | 15 | 22 | $0.0000 |
| gpt | 2 | 86.2% | 69.0% | 10 | 29 | $0.5351 |
| claude | 3 | 82.6% | 58.8% | 18 | 73 | $0.0000 |
| gpt-oss | 5 | 76.8% | 65.8% | 27 | 238 | $0.2972 |
| deepseek | 2 | 72.5% | 59.7% | 9 | 40 | $0.0540 |
| nemotron | 5 | 68.0% | 53.5% | 25 | 394 | $0.3796 |
| olmo | 1 | 66.3% | 52.9% | 5 | 66 | $0.0233 |
| qwen | 12 | 66.2% | 53.2% | 58 | 1198 | $8.6558 |
| mistral | 3 | 61.7% | 33.1% | 10 | 152 | $0.0265 |
| llama | 8 | 59.4% | 39.5% | 33 | 685 | $0.1851 |
| granite | 2 | 52.9% | 39.3% | 7 | 216 | $0.0082 |
| gemma | 3 | 49.8% | 36.1% | 11 | 227 | $0.0220 |
| phi | 1 | 45.3% | 31.1% | 1 | 123 | $0.0083 |
| ministral | 3 | 40.7% | 16.2% | 10 | 224 | $0.0085 |

## Grouped by Vendor

| Vendor | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| xAI | 1 | 90.2% | 73.0% | 7 | 14 | $4.9494 |
| — | 2 | 89.9% | 72.6% | 15 | 22 | $0.0000 |
| Anthropic | 3 | 82.6% | 58.8% | 18 | 73 | $0.0000 |
| OpenAI | 7 | 79.5% | 66.7% | 37 | 267 | $0.8323 |
| DeepSeek | 2 | 72.5% | 59.7% | 9 | 40 | $0.0540 |
| Nvidia | 5 | 68.0% | 53.5% | 25 | 394 | $0.3796 |
| Allen AI | 1 | 66.3% | 52.9% | 5 | 66 | $0.0233 |
| Alibaba/Qwen | 12 | 66.2% | 53.2% | 58 | 1198 | $8.6558 |
| Meta | 8 | 59.4% | 39.5% | 33 | 685 | $0.1851 |
| IBM | 2 | 52.9% | 39.3% | 7 | 216 | $0.0082 |
| Mistral | 6 | 51.2% | 24.7% | 20 | 376 | $0.0351 |
| Google | 3 | 49.8% | 36.1% | 11 | 227 | $0.0220 |
| Microsoft | 1 | 45.3% | 31.1% | 1 | 123 | $0.0083 |

## Grouped by Architecture

| Architecture | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| — | 2 | 89.9% | 72.6% | 15 | 22 | $0.0000 |
| unknown | 6 | 85.1% | 64.5% | 35 | 116 | $5.4845 |
| moe | 20 | 70.8% | 56.6% | 99 | 1216 | $6.3435 |
| dense | 25 | 55.9% | 38.3% | 97 | 2347 | $3.3250 |

## Grouped by License

| License | models | judge_pass_mean | exact_match_mean | canonical_pass_total | catastrophic_total | cost_total |
| --- | --- | --- | --- | --- | --- | --- |
| — | 2 | 89.9% | 72.6% | 15 | 22 | $0.0000 |
| Proprietary | 6 | 85.1% | 64.5% | 35 | 116 | $5.4845 |
| Llama-3.3-Community | 2 | 68.7% | 46.9% | 10 | 149 | $0.0708 |
| Nvidia-Open-Model | 5 | 68.0% | 53.5% | 25 | 394 | $0.3796 |
| Apache-2.0 | 26 | 63.8% | 48.0% | 117 | 2094 | $9.0195 |
| Llama-4-Community | 3 | 63.7% | 48.0% | 13 | 183 | $0.0532 |
| MIT | 3 | 63.4% | 50.2% | 10 | 163 | $0.0623 |
| Llama-3.1-Community | 2 | 56.6% | 30.7% | 8 | 196 | $0.0541 |
| Gemma-Terms | 3 | 49.8% | 36.1% | 11 | 227 | $0.0220 |
| Llama-3.2-Community | 1 | 33.1% | 17.0% | 2 | 157 | $0.0070 |

## Canonical case grid

| Sample ID | claude-haiku-4-5 | claude-opus-4-7 | claude-sonnet-4-6 | deepseek-v3-1-terminus | deepseek-v3-2 | gemini-3-1-pro-preview | gemini-3-flash-preview | gemma-3-12b-it | gemma-3-27b-it | gemma-3-4b-it | gpt-5-4-mini | gpt-5-5 | gpt-oss-120b | gpt-oss-120b-cerebras | gpt-oss-120b-groq | gpt-oss-20b | gpt-oss-20b-groq | granite-4-0-h-micro | granite-4-1-8b | grok-4 | llama-3-1-70b | llama-3-1-8b | llama-3-2-3b | llama-3-3-70b | llama-3-3-70b-groq | llama-4-maverick | llama-4-scout | llama-4-scout-groq | ministral-14b | ministral-3b | ministral-8b | mistral-nemo | mistral-small-2603 | mistral-small-3-2-24b | nemotron-3-nano-30b | nemotron-3-super-120b | nemotron-llama-3-1-70b | nemotron-nano-9b | nemotron-super-49b | olmo-3-1-32b | phi-4 | qwen3-14b | qwen3-235b | qwen3-235b-cerebras | qwen3-30b | qwen3-32b-groq | qwen3-5-122b | qwen3-5-27b | qwen3-5-35b | qwen3-5-397b | qwen3-5-9b | qwen3-8b | qwen3-next-80b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CANONICAL-AVOMA-RANGE` | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-AVOMA-YEAR` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `CANONICAL-CRESTA-ACCOUNT-ID` | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| `CANONICAL-CRESTA-CURRENCY` | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | FAIL | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | PASS | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS |
| `CANONICAL-CRESTA-PERCENT` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS |
| `CANONICAL-NIAGARA-ORDERID` | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | PASS | PASS | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS | PASS |
| `CANONICAL-NIAGARA-PHONE` | PASS | FAIL | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | FAIL | PASS | FAIL | FAIL | PASS |
| `CANONICAL-RINGCENTRAL-PHONE` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | FAIL | FAIL | PASS | PASS |
| `CANONICAL-TALKATOO-CENTURY` | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL | PASS | FAIL | PASS | FAIL |

## Per-class accuracy (% judge_pass)

| entity_class | claude-haiku-4-5 | claude-opus-4-7 | claude-sonnet-4-6 | deepseek-v3-1-terminus | deepseek-v3-2 | gemini-3-1-pro-preview | gemini-3-flash-preview | gemma-3-12b-it | gemma-3-27b-it | gemma-3-4b-it | gpt-5-4-mini | gpt-5-5 | gpt-oss-120b | gpt-oss-120b-cerebras | gpt-oss-120b-groq | gpt-oss-20b | gpt-oss-20b-groq | granite-4-0-h-micro | granite-4-1-8b | grok-4 | llama-3-1-70b | llama-3-1-8b | llama-3-2-3b | llama-3-3-70b | llama-3-3-70b-groq | llama-4-maverick | llama-4-scout | llama-4-scout-groq | ministral-14b | ministral-3b | ministral-8b | mistral-nemo | mistral-small-2603 | mistral-small-3-2-24b | nemotron-3-nano-30b | nemotron-3-super-120b | nemotron-llama-3-1-70b | nemotron-nano-9b | nemotron-super-49b | olmo-3-1-32b | phi-4 | qwen3-14b | qwen3-235b | qwen3-235b-cerebras | qwen3-30b | qwen3-32b-groq | qwen3-5-122b | qwen3-5-27b | qwen3-5-35b | qwen3-5-397b | qwen3-5-9b | qwen3-8b | qwen3-next-80b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADDRESS | 96.4% | 100.0% | 89.3% | 75.0% | 85.7% | 89.3% | 100.0% | 60.7% | 85.7% | 21.4% | 82.1% | 96.4% | 75.0% | 53.6% | 67.9% | 64.3% | 60.7% | 57.1% | 71.4% | 92.9% | 92.9% | 53.6% | 32.1% | 96.4% | 92.9% | 78.6% | 71.4% | 85.7% | 57.1% | 60.7% | 57.1% | 42.9% | 85.7% | 96.4% | 67.9% | 78.6% | 82.1% | 60.7% | 67.9% | 82.1% | 57.1% | 67.9% | 85.7% | 82.1% | 85.7% | 92.9% | 82.1% | 78.6% | 28.6% | 67.9% | 14.3% | 53.6% | 78.6% |
| ADVERSARIAL | 43.6% | 72.7% | 80.0% | 50.9% | 54.5% | 80.0% | 80.0% | 40.0% | 54.5% | 12.7% | 74.5% | 85.5% | 58.2% | 47.3% | 61.8% | 52.7% | 54.5% | 38.2% | 41.8% | 78.2% | 43.6% | 29.1% | 20.0% | 47.3% | 49.1% | 52.7% | 41.8% | 47.3% | 36.4% | 30.9% | 34.5% | 23.6% | 50.9% | 47.3% | 49.1% | 63.6% | 30.9% | 49.1% | 56.4% | 60.0% | 21.8% | 63.6% | 41.8% | 34.5% | 30.9% | 65.5% | 61.8% | 63.6% | 32.7% | 58.2% | 14.5% | 54.5% | 60.0% |
| CARDINAL | 85.4% | 92.7% | 85.4% | 65.9% | 73.2% | 87.8% | 95.1% | 56.1% | 80.5% | 4.9% | 80.5% | 95.1% | 80.5% | 80.5% | 92.7% | 87.8% | 85.4% | 56.1% | 73.2% | 95.1% | 82.9% | 46.3% | 24.4% | 90.2% | 90.2% | 85.4% | 65.9% | 73.2% | 39.0% | 12.2% | 19.5% | 48.8% | 95.1% | 78.0% | 87.8% | 90.2% | 73.2% | 82.9% | 80.5% | 78.0% | 56.1% | 75.6% | 90.2% | 56.1% | 56.1% | 92.7% | 82.9% | 95.1% | 68.3% | 80.5% | 48.8% | 82.9% | 82.9% |
| CREDIT_CARD | 60.0% | 75.0% | 80.0% | 70.0% | 75.0% | 80.0% | 80.0% | 15.0% | 40.0% | 5.0% | 60.0% | 80.0% | 70.0% | 75.0% | 65.0% | 65.0% | 60.0% | 25.0% | 30.0% | 80.0% | 35.0% | 15.0% | 10.0% | 35.0% | 35.0% | 40.0% | 30.0% | 30.0% | 35.0% | 15.0% | 20.0% | 25.0% | 55.0% | 30.0% | 45.0% | 60.0% | 25.0% | 35.0% | 20.0% | 30.0% | 20.0% | 25.0% | 55.0% | 55.0% | 65.0% | 35.0% | 60.0% | 55.0% | 35.0% | 40.0% | 10.0% | 35.0% | 65.0% |
| DATE | 89.8% | 95.9% | 89.8% | 93.9% | 93.9% | 98.0% | 98.0% | 77.6% | 89.8% | 63.3% | 93.9% | 98.0% | 93.9% | 85.7% | 95.9% | 95.9% | 95.9% | 79.6% | 57.1% | 95.9% | 91.8% | 79.6% | 71.4% | 87.8% | 81.6% | 93.9% | 81.6% | 83.7% | 61.2% | 44.9% | 49.0% | 55.1% | 69.4% | 73.5% | 95.9% | 95.9% | 73.5% | 79.6% | 89.8% | 87.8% | 65.3% | 89.8% | 87.8% | 89.8% | 81.6% | 89.8% | 85.7% | 87.8% | 44.9% | 79.6% | 40.8% | 87.8% | 83.7% |
| DATE_INTERVAL | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 80.0% | 90.0% | 60.0% | 100.0% | 100.0% | 90.0% | 90.0% | 90.0% | 100.0% | 100.0% | 70.0% | 80.0% | 100.0% | 100.0% | 80.0% | 70.0% | 100.0% | 100.0% | 100.0% | 100.0% | 90.0% | 40.0% | 50.0% | 40.0% | 70.0% | 100.0% | 90.0% | 80.0% | 90.0% | 90.0% | 80.0% | 70.0% | 100.0% | 80.0% | 90.0% | 90.0% | 90.0% | 70.0% | 90.0% | 80.0% | 80.0% | 40.0% | 40.0% | 10.0% | 100.0% | 100.0% |
| DRUG_WITH_DOSE | 100.0% | 100.0% | 100.0% | 86.7% | 86.7% | 100.0% | 100.0% | 100.0% | 100.0% | 46.7% | 93.3% | 100.0% | 86.7% | 93.3% | 100.0% | 86.7% | 93.3% | 93.3% | 86.7% | 100.0% | 93.3% | 93.3% | 73.3% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 20.0% | 86.7% | 26.7% | 93.3% | 100.0% | 93.3% | 93.3% | 100.0% | 73.3% | 100.0% | 60.0% | 100.0% | 93.3% | 86.7% | 93.3% | 100.0% | 86.7% | 86.7% | 93.3% | 80.0% | 26.7% | 86.7% | 20.0% | 100.0% | 93.3% |
| EMAIL_ADDRESS | 46.4% | 85.7% | 85.7% | 46.4% | 42.9% | 100.0% | 92.9% | 28.6% | 42.9% | 10.7% | 57.1% | 100.0% | 82.1% | 75.0% | 89.3% | 71.4% | 64.3% | 35.7% | 60.7% | 100.0% | 64.3% | 17.9% | 17.9% | 53.6% | 57.1% | 53.6% | 25.0% | 25.0% | 39.3% | 10.7% | 35.7% | 32.1% | 57.1% | 82.1% | 64.3% | 71.4% | 42.9% | 46.4% | 57.1% | 32.1% | 17.9% | 57.1% | 64.3% | 71.4% | 32.1% | 82.1% | 57.1% | 82.1% | 32.1% | 82.1% | 17.9% | 46.4% | 50.0% |
| MIXED | 66.7% | 93.9% | 84.8% | 63.6% | 63.6% | 84.8% | 84.8% | 48.5% | 63.6% | 21.2% | 72.7% | 84.8% | 72.7% | 66.7% | 69.7% | 72.7% | 66.7% | 48.5% | 45.5% | 84.8% | 63.6% | 30.3% | 36.4% | 57.6% | 60.6% | 66.7% | 54.5% | 57.6% | 18.2% | 18.2% | 33.3% | 33.3% | 72.7% | 75.8% | 75.8% | 72.7% | 54.5% | 60.6% | 51.5% | 57.6% | 42.4% | 66.7% | 54.5% | 57.6% | 36.4% | 81.8% | 69.7% | 60.6% | 27.3% | 42.4% | 6.1% | 57.6% | 60.6% |
| MONEY | 80.5% | 95.1% | 97.6% | 56.1% | 61.0% | 82.9% | 92.7% | 63.4% | 82.9% | 17.1% | 82.9% | 92.7% | 75.6% | 70.7% | 78.0% | 63.4% | 68.3% | 65.9% | 63.4% | 90.2% | 78.0% | 53.7% | 51.2% | 75.6% | 70.7% | 80.5% | 75.6% | 70.7% | 78.0% | 39.0% | 75.6% | 48.8% | 85.4% | 73.2% | 75.6% | 68.3% | 70.7% | 68.3% | 43.9% | 80.5% | 63.4% | 73.2% | 75.6% | 85.4% | 61.0% | 85.4% | 82.9% | 56.1% | 29.3% | 75.6% | 19.5% | 53.7% | 90.2% |
| NUMERIC_ID | 40.5% | 69.0% | 66.7% | 78.6% | 78.6% | 90.5% | 90.5% | 42.9% | 42.9% | 11.9% | 61.9% | 92.9% | 81.0% | 61.9% | 73.8% | 61.9% | 59.5% | 19.0% | 47.6% | 83.3% | 47.6% | 11.9% | 11.9% | 50.0% | 52.4% | 59.5% | 33.3% | 38.1% | 40.5% | 26.2% | 42.9% | 16.7% | 57.1% | 69.0% | 69.0% | 85.7% | 38.1% | 52.4% | 54.8% | 31.0% | 21.4% | 81.0% | 69.0% | 64.3% | 50.0% | 85.7% | 81.0% | 71.4% | 38.1% | 71.4% | 11.9% | 52.4% | 66.7% |
| PERCENT | 89.3% | 100.0% | 89.3% | 75.0% | 78.6% | 100.0% | 100.0% | 60.7% | 67.9% | 10.7% | 89.3% | 100.0% | 85.7% | 89.3% | 92.9% | 89.3% | 92.9% | 32.1% | 64.3% | 96.4% | 85.7% | 53.6% | 25.0% | 82.1% | 82.1% | 96.4% | 53.6% | 60.7% | 67.9% | 14.3% | 46.4% | 67.9% | 75.0% | 92.9% | 71.4% | 92.9% | 85.7% | 82.1% | 82.1% | 82.1% | 57.1% | 75.0% | 71.4% | 78.6% | 46.4% | 89.3% | 89.3% | 85.7% | 57.1% | 82.1% | 60.7% | 78.6% | 67.9% |
| PHONE_NUMBER | 90.7% | 97.7% | 93.0% | 81.4% | 83.7% | 100.0% | 100.0% | 65.1% | 74.4% | 18.6% | 97.7% | 100.0% | 88.4% | 83.7% | 88.4% | 88.4% | 93.0% | 18.6% | 48.8% | 100.0% | 48.8% | 30.2% | 4.7% | 58.1% | 46.5% | 76.7% | 37.2% | 44.2% | 65.1% | 25.6% | 62.8% | 20.9% | 83.7% | 76.7% | 83.7% | 93.0% | 27.9% | 72.1% | 62.8% | 67.4% | 18.6% | 95.3% | 81.4% | 86.0% | 88.4% | 95.3% | 93.0% | 83.7% | 44.2% | 74.4% | 32.6% | 83.7% | 93.0% |
| SSN | 80.0% | 93.3% | 86.7% | 86.7% | 86.7% | 100.0% | 100.0% | 26.7% | 46.7% | 6.7% | 86.7% | 100.0% | 86.7% | 86.7% | 93.3% | 86.7% | 86.7% | 26.7% | 53.3% | 100.0% | 53.3% | 20.0% | 20.0% | 60.0% | 66.7% | 66.7% | 46.7% | 46.7% | 53.3% | 26.7% | 33.3% | 33.3% | 66.7% | 60.0% | 80.0% | 100.0% | 20.0% | 86.7% | 53.3% | 46.7% | 20.0% | 80.0% | 86.7% | 73.3% | 73.3% | 93.3% | 80.0% | 73.3% | 46.7% | 73.3% | 6.7% | 73.3% | 73.3% |
| TIME | 76.7% | 73.3% | 66.7% | 60.0% | 63.3% | 53.3% | 60.0% | 70.0% | 76.7% | 53.3% | 66.7% | 76.7% | 73.3% | 66.7% | 70.0% | 66.7% | 70.0% | 56.7% | 60.0% | 70.0% | 70.0% | 70.0% | 46.7% | 80.0% | 73.3% | 76.7% | 56.7% | 63.3% | 60.0% | 50.0% | 46.7% | 46.7% | 70.0% | 66.7% | 70.0% | 73.3% | 76.7% | 73.3% | 43.3% | 70.0% | 66.7% | 70.0% | 76.7% | 80.0% | 76.7% | 73.3% | 60.0% | 66.7% | 36.7% | 56.7% | 26.7% | 63.3% | 76.7% |
| URL | 82.6% | 95.7% | 87.0% | 87.0% | 91.3% | 95.7% | 91.3% | 69.6% | 82.6% | 47.8% | 87.0% | 91.3% | 91.3% | 78.3% | 91.3% | 87.0% | 82.6% | 78.3% | 73.9% | 95.7% | 78.3% | 69.6% | 52.2% | 73.9% | 65.2% | 82.6% | 73.9% | 82.6% | 17.4% | 30.4% | 26.1% | 26.1% | 78.3% | 78.3% | 60.9% | 95.7% | 65.2% | 73.9% | 73.9% | 69.6% | 73.9% | 87.0% | 87.0% | 82.6% | 65.2% | 95.7% | 87.0% | 91.3% | 39.1% | 82.6% | 60.9% | 69.6% | 87.0% |

## Disagreements between methods (top 20)

| model | sample | EM | judge | kind | expected | actual |
| --- | --- | --- | --- | --- | --- | --- |
| `claude-sonnet-4-6` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `claude-haiku-4-5` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `qwen3-235b` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | Your reference is 1-734-272-2384 |
| `qwen3-235b` | `CANONICAL-NIAGARA-ORDERID` | False | pass | judge_pass_em_fail | your reference is 17-34272-2384 | 17-34272-2384 |
| `grok-4` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `qwen3-next-80b` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `qwen3-next-80b` | `CANONICAL-CRESTA-PERCENT` | False | pass | judge_pass_em_fail | satisfaction was 100% | satisfaction was 100 percent |
| `qwen3-5-397b` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1 (734) 272-2384 |
| `qwen3-5-122b` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `qwen3-5-27b` | `CANONICAL-NIAGARA-PHONE` | False | pass | judge_pass_em_fail | your reference is +1-734-272-2384 | your reference is 1-734-272-2384 |
| `qwen3-8b` | `CANONICAL-RINGCENTRAL-PHONE` | False | pass | judge_pass_em_fail | you can reach us at 800-729-7234 | you can reach us at (800) 729-7234 |
| `qwen3-5-27b` | `CANONICAL-AVOMA-RANGE` | False | pass | judge_pass_em_fail | the budget range is 80,000–90,000 | the budget range is 80–90 thousand |
| `gpt-oss-20b` | `CANONICAL-RINGCENTRAL-PHONE` | False | pass | judge_pass_em_fail | you can reach us at 800-729-7234 | you can reach us at (800) 729-7234 |
| `mistral-small-3-2-24b` | `CANONICAL-RINGCENTRAL-PHONE` | False | pass | judge_pass_em_fail | you can reach us at 800-729-7234 | You can reach us at 800-729-7234 |
| `mistral-small-2603` | `CANONICAL-CRESTA-PERCENT` | False | pass | judge_pass_em_fail | satisfaction was 100% | Satisfaction was 100 percent. |
| `mistral-small-2603` | `CANONICAL-RINGCENTRAL-PHONE` | False | pass | judge_pass_em_fail | you can reach us at 800-729-7234 | You can reach us at (800) 729-7234 |
| `mistral-small-2603` | `CANONICAL-AVOMA-YEAR` | False | pass | judge_pass_em_fail | we expect to launch in 2026 | We expect to launch in 2026 |
| `mistral-small-2603` | `CANONICAL-CRESTA-CURRENCY` | False | pass | judge_pass_em_fail | the total amount is $171.41 | The total amount is $171.41 |
| `ministral-14b` | `CANONICAL-CRESTA-CURRENCY` | False | pass | judge_pass_em_fail | the total amount is $171.41 | the total amount is **$171.41** |
| `ministral-14b` | `CANONICAL-RINGCENTRAL-PHONE` | False | pass | judge_pass_em_fail | you can reach us at 800-729-7234 | you can reach us at **800-729-7234** |
