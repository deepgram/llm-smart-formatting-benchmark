# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Benchmark for LLMs as a post-processing step after Deepgram STT: raw spoken-form transcript → formatted transcript with entities (money, dates, phones, IDs, etc.) normalized. The LLM never sees audio. See `GUIDELINE.md` for the task contract, scored entity classes, and catastrophic-failure definition.

Pipeline-shaped flow:
```
synthetic_data.csv → runner (per model, async) → results/<run_id>/responses.csv
                                                ↓
                                              evaluator (4 scorers + LLM judge) → scored.csv / summary.csv / report.md
```

A separate `iterate` package drives a fast prompt-tuning loop on a small stratified subset against a couple of models, with a per-prompt-hash leaderboard.

## Common commands

Setup (Python ≥ 3.11):
```bash
uv sync                                    # or pip install -e .
export OPENROUTER_API_KEY=...              # required for runner
export ANTHROPIC_API_KEY=...               # required for evaluator (judge) + iterate
```

Runner (CLI: `uv run runner ...`):
```bash
uv run runner list-models                  # registered model_ids + slugs
uv run runner show-prompt                  # base prompt + hash
uv run runner run --dry-run --limit 3 --models claude-opus-4-7
uv run runner run --models all --concurrency 16 --parallel-models 2
uv run runner run --models gpt-5-5 --limit 50          # smoke
uv run runner resume <run_id>                          # re-run skips done (model_id, sample_id)
uv run runner baseline --limit 50 --run-id impeller-stem-smoke    # Impeller→Stem only
uv run runner chained --models qwen3-32b-groq --prompt prompts/system_prompt.md  # Impeller→Stem→LLM
uv run runner determinism --models qwen3-32b-groq --prompt iterate/results/iter-009-*/prompt.txt --trials 100
```

Evaluator (CLI: `uv run evaluator ...`):
```bash
uv run evaluator score --responses results/<run_id>           # writes scored.csv, summary.csv, canonical.csv, report.md
uv run evaluator score --responses results/<run_id> --models claude-opus-4-7,gpt-5-5
uv run evaluator determinism --responses results/<run_id>     # for runs from `runner determinism`
```

Iterate (prompt tuning, CLI: `uv run iterate ...`):
```bash
uv run iterate run --prompt prompts/system_prompt.md          # one iter; appends to iterate/results/leaderboard.csv
uv run iterate show --top 10
uv run iterate failures iterate/results/iter-009-XXXX --model qwen3-32b-groq
uv run iterate matrix --prompts prompts/variants/A_minimal.md,prompts/variants/B_id_focus.md --models qwen3-32b-groq,gpt-oss-120b-groq
```

There is no test suite or linter wired up — `pyproject.toml` declares only runtime deps.

## Architecture: how the runner picks a route

`runner/models.py::MODEL_REGISTRY` is the source of truth. Each `ModelEntry` has a `route` field:

- `"openrouter"` — OpenRouter chat completions (`runner/openrouter.py`). `provider_routing` pins providers (Groq, Cerebras); `extra_body` carries reasoning/thinking toggles.
- `"anthropic"` / `"openai"` / `"google"` — native SDKs (`runner/anthropic_client.py`, `openai_client.py`, `google_client.py`). `native_model` is the slug actually sent.

`runner/runner.py::_build_clients` lazy-imports only the clients needed for the selected models. Everything is async + per-model semaphore (`concurrency` in the entry, or the global `--concurrency`); `--parallel-models` runs N model pipelines concurrently.

Reasoning is **off by default** for benchmark models (latency matters more than peak quality). Models that think-by-default get `extra_body=_REASONING_OFF` in the registry. A few endpoints (gpt-oss on Groq/Cerebras, claude reasoning) cannot disable it — see `notes` in those entries.

## Architecture: prompt assembly

`runner/prompts.py::BASE_PROMPT` is the always-on system prompt. `build_system_prompt(formatting_prompt)` appends the per-row `formatting_prompt` (from the `prompt` column of `synthetic_data.csv`) under a `Formatting instructions:` heading when present. `base_prompt_hash()` (12-char SHA-256) is recorded with every result so old/new prompt results stay distinguishable.

`iterate/main.py` deliberately bypasses `runner/prompts.py` and assembles its own messages with `<transcript>...</transcript>` spotlighting (per `PROMPT_GUIDE.md` §3) — keep that distinction in mind when changing message-construction logic.

## Architecture: scoring stack

`evaluator/main.py::_score_one` runs four independent scorers per row:

1. `exact_match` — string equality (`evaluator/scorers.py`).
2. `regex_pass` — entity-class regex (`evaluator/scorers.py`); returns `None` when no check applies.
3. `judge_accuracy` — Claude Opus 4.7 judge (`evaluator/judge.py`) returns `pass | style_violation | numeric_drift | wrong_value | other` + `catastrophic` + `promptability`.
4. `judge_hallucination` — same model, no reference: `none | minor_addition | dropped_content | fabricated`.

Methods 3 + 4 run as a single `asyncio.gather` per row. Judge default is `claude-opus-4-7` (`JUDGE_MODEL_DEFAULT`). `scored.csv` is appended-as-you-go so re-running skips already-scored `(run_id, model_id, sample_id)` triples.

`classify_disagreement` cross-checks all three deterministic signals to flag rows where methods disagree (worth eyeballing).

## Conventions worth keeping in mind

- `model_id` is the unique key written everywhere (`responses.csv`, `scored.csv`, leaderboards). Don't reuse one for a different config — make a new entry. Pinned-provider variants are suffixed (`-groq`, `-cerebras`, `-nitro`).
- A row with `error` populated is considered "done" by resume; delete it from `responses.csv` to retry.
- `source=customer_canonical` rows in `synthetic_data.csv` are the highest-trust ground truth — `canonical.csv` reports them specifically.
- The baseline path is the existing Deepgram pipeline (Impeller `/v2/read` → entity-tag adapter → Stem `/dev/format-entities`); it has no prompt channel and ignores `formatting_prompt`. See README.md "Existing Pipeline Baseline" for the local Cargo + Docker setup.
- Closed-source model slugs in `MODEL_REGISTRY` are partially speculative (best-effort for forward-looking model IDs); verify against `https://openrouter.ai/api/v1/models` before a real spend.
