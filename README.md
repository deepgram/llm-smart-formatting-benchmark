# smart-formatting-llm-benchmark

Benchmarks for **smart formatting** — turning raw spoken-form transcripts
(`"my number is two four eight..."`) into clean written form
(`"My number is (248) 123-4567."`).

Three evals, each with its own CLI:

| Eval | Where | Measures |
| --- | --- | --- |
| LLM post-processing | `runner/` + `evaluator/` | Frontier LLMs as a formatting step after STT (text in, text out). |
| Fine-tuned small models | `finetune/` | LoRA fine-tunes on Together.ai (Gemma, Llama, Qwen, Mercury). |
| Competitor STT | `competitor-formatting/` | Deepgram vs ElevenLabs / OpenAI / Azure / Google / Soniox, on audio. |

Also `iterate/` for fast prompt tuning against one or two cheap models.
Task contract: [`GUIDELINE.md`](GUIDELINE.md). Prompt guidance:
[`PROMPT_GUIDE.md`](PROMPT_GUIDE.md). Latest fine-tune writeup:
[`finetune/together_ai_v3.md`](finetune/together_ai_v3.md).

## Install

Python 3.11+. `uv sync` (or `pip install -e .`). Set only the API keys
you need per eval below.

---

## 1. LLM post-processing (`runner` + `evaluator`)

```bash
export OPENROUTER_API_KEY=...   # runner
export ANTHROPIC_API_KEY=...    # evaluator's LLM judge
```

```bash
uv run runner list-models                                   # registered models + slugs
uv run runner show-prompt                                   # base prompt + hash
uv run runner run --dry-run --limit 3 --models claude-opus-4-7   # no API calls
uv run runner run --models all --concurrency 16 --parallel-models 2
uv run runner resume <run_id>                               # re-run, skip done rows
uv run evaluator score --responses results/<run_id>         # writes scored.csv, summary.csv, report.md
```

Output lands in `results/<run_id>/`: `responses.csv`,
`run_manifest.json`, plus `scored.csv` / `summary.csv` /
`canonical.csv` / `report.md` after scoring. Resume is keyed on
`(model_id, sample_id)`; delete failed rows from `responses.csv` to
retry.

Four scorers per row: exact match, entity-class regex, Claude Opus 4.7
judge for accuracy (`pass | style_violation | numeric_drift |
wrong_value | other`, plus `catastrophic` + `promptability`), and the
same judge for hallucination (`none | minor_addition | dropped_content
| fabricated`).

### Baseline + chained

The existing Deepgram pipeline (Impeller `/v2/read` → entity-tag
adapter → Stem `/dev/format-entities`) as a baseline. Start Impeller
and Stem locally with Cargo (or via `docker-compose.baseline.yml`),
then:

```bash
uv run runner baseline --limit 50 --run-id impeller-stem-smoke
uv run runner chained --models qwen3-32b-groq --prompt prompts/system_prompt.md   # baseline → LLM cleanup
uv run runner determinism --models qwen3-32b-groq --prompt iterate/results/iter-009-XXXX/prompt.txt --trials 100
```

Both `baseline` and `chained` write a normal `responses.csv`, so
`evaluator score` works the same on them. The baseline ignores
`formatting_prompt` (no prompt channel in the existing pipeline).

### Editing models / prompts

- `runner/models.py` is the source of truth. `model_id` is the unique key written everywhere — make a new entry rather than reusing one.
- `runner/prompts.py::BASE_PROMPT` is the always-on system prompt; its 12-char SHA-256 is recorded per row, so old/new runs stay distinguishable.
- Reasoning is **off by default** — latency > peak quality for this task.
- A few OpenRouter slugs are speculative; verify against `openrouter.ai/api/v1/models` before a real spend.

---

## 2. Fine-tuning (`finetune`)

```bash
export TOGETHER_API_KEY=...
export ANTHROPIC_API_KEY=...
```

One-shot (`split → upload → train → wait → infer → score`):

```bash
uv run finetune all --base-model meta-llama/Llama-3.2-3B-Instruct
```

Or step by step: `split`, `upload`, `train`, `status`, `deploy`,
`infer`, `score`, `stop` (or `deploy-eval-stop` for the last three).
Per-run artifacts (job ids, endpoint info) land under
`finetune/runs/<run_name>/`. Existing runs: Gemma 3 (270m, 1b),
Llama 3.2 3B, Qwen3 8B, Qwen3.5 9B, Mercury 2. Data augmentation
passes live in `finetune/augment*.py`.

---

## 3. Competitor STT (`competitor-formatting`)

160 audio clips (10 per entity class), synthesized with Deepgram
Aura-2 TTS, transcribed by each provider, judged by Claude Opus 4.7.
See [`competitor-formatting/README.md`](competitor-formatting/README.md).

```bash
export DEEPGRAM_API_KEY=...                      # TTS + Deepgram STT
export ELEVENLABS_API_KEY / OPENAI_API_KEY / \
       AZURE_SPEECH_KEY / GOOGLE_API_KEY / \
       SONIOX_API_KEY=...                        # optional, per provider
export ANTHROPIC_API_KEY=...                     # judge

uv run python competitor-formatting/synthesize.py
uv run python competitor-formatting/transcribe.py --providers all
for p in deepgram elevenlabs openai azure google soniox; do
  uv run python competitor-formatting/score.py --provider $p
done
```

All three steps are resumable.

---

## Prompt iteration (`iterate`)

Tight loop while editing `prompts/system_prompt.md`. Runs a fixed
stratified subset against cheap models, appends to a
per-prompt-hash leaderboard.

```bash
uv run iterate run --prompt prompts/system_prompt.md
uv run iterate show --top 10
uv run iterate failures iterate/results/iter-009-XXXX --model qwen3-32b-groq
uv run iterate matrix --prompts prompts/variants/A.md,prompts/variants/B.md \
                     --models qwen3-32b-groq,gpt-oss-120b-groq
```

`iterate/` deliberately bypasses `runner/prompts.py` and assembles its
own `<transcript>...</transcript>`-spotlit messages — keep that in
mind if you change message construction in either place.
