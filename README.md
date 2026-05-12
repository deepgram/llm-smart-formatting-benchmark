# smart-formatting-llm-benchmark

Async runner that drives the synthetic-data CSV through every selected LLM via
OpenRouter, capturing model output and latency per row. Resumable, with one
folder per run under `results/`.

## Install

Requires Python 3.11+.

```bash
uv sync
```

(Or `pip install -e .` if you prefer.)

## Environment

```bash
export OPENROUTER_API_KEY=<your-key>
```

The runner refuses to start without it.

## Quick sanity check (no API calls)

```bash
uv run runner run --dry-run --limit 3 --models claude-opus-4-7
```

This prints the first three fully-rendered request bodies — system prompt,
user message, sampling params, thinking/reasoning extras, and provider
routing — so you can verify what will be sent before spending any money.

List the registered models and OpenRouter slugs:

```bash
uv run runner list-models
```

Inspect the base prompt (and its hash, recorded with every result):

```bash
uv run runner show-prompt
```

## Real run

All models, full dataset:

```bash
uv run runner run --models all --dataset synthetic_data.csv --run-id auto
```

Subset of models with a small smoke run:

```bash
uv run runner run --models claude-opus-4-7,gpt-5-5 --limit 50
```

Higher concurrency or parallel models:

```bash
uv run runner run --models all --concurrency 16 --parallel-models 2
```

## Existing Pipeline Baseline

This repo can also run Deepgram's existing smart-formatting pipeline as a
benchmark baseline:

```text
Impeller /v2/read -> inline entity tag adapter -> Stem /dev/format-entities
```

Start the services locally with Cargo first. Use local config files that enable
Impeller NER, Stem dev mode, and point Stem at `http://localhost:8080/v2`.
With the model files in the Impeller repo root, Impeller's model search path can
include that root directory.

```bash
# Terminal 1
cd ../impeller
cargo run -- -v serve conf/<your-local-impeller-config>.toml

# Terminal 2
cd ../stem
cargo run -- -v serve conf/<your-local-stem-config>.toml
```

Expected local ports:

- Impeller: `http://localhost:8080/v2`
- Stem: `http://localhost:8888/v1`

Smoke test Stem's formatter directly:

```bash
curl -s -X POST http://localhost:8888/v1/dev/format-entities \
  -H 'Content-Type: application/json' \
  -d '{"entity_tagged_text":"my number is <entity> two four eight one two three four five six seven </entity_PHONE_NUMBER>"}'
```

Then run a baseline benchmark:

```bash
uv run runner baseline --limit 50 --run-id impeller-stem-smoke
```

For the full dataset:

```bash
uv run runner baseline --dataset synthetic_data.csv --run-id impeller-stem-full
```

The output is a normal `results/<run_id>/responses.csv` with
`model_id=impeller-stem-baseline`, so the existing evaluator can score it:

```bash
uv run evaluator score --responses results/impeller-stem-smoke
```

Notes:

- The baseline ignores `formatting_prompt`; the existing pipeline has no prompt
  channel and only formats spans detected by Impeller's NER.
- `entity-detector.batch.06bc8f36.dg` is the model `/v2/read` needs for NER.
- `nova-3-general.en.batch.2187e11a.dg` is not required by `runner baseline`,
  but can stay in the same local Impeller model search path if you want the
  local stack to mirror the broader Stem/Impeller setup.

Optional Docker path:

```bash
cp .env.baseline.example .env
docker compose -f docker-compose.baseline.yml build
docker compose -f docker-compose.baseline.yml up
uv run runner baseline \
  --impeller-url http://localhost:18080/v2 \
  --stem-url http://localhost:18888 \
  --limit 50 \
  --run-id impeller-stem-smoke
```

## Resume

If the runner crashes, re-run with the same `--run-id`, or use the resume
command which reads the run manifest:

```bash
uv run runner resume <run_id>
```

Rows already in `responses.csv` for that `(model_id, sample_id)` are skipped.
Failed rows (those with `error` populated) are also considered "done" — delete
them from `responses.csv` before resume if you want a retry.

## Output

Per run, under `results/<run_id>/`:

- `responses.csv` — one row per `(model_id, sample_id)` with columns:
  `run_id, model_id, provider, sample_id, base_prompt_hash, formatting_prompt,
   input_text, expected_output, actual_output, latency_total_ms,
   latency_ttft_ms, tokens_in, tokens_out, cost_usd, finish_reason, error,
   attempted_at, completed_at`
- `run_manifest.json` — timestamp, model list, base prompt + hash, sampling
  defaults, git SHA, dataset checksum.

At the end of the run the CLI prints total `$` spent (summed from the
`cost_usd` field returned by OpenRouter's `usage.include` flag).

## Editing models / prompts

- Models live in `runner/models.py` as a dict-of-dicts. Add or remove entries
  freely; `model_id` is the unique key written to `responses.csv`.
- The base prompt lives at the top of `runner/prompts.py`. If you change it,
  the hash changes, and that hash is recorded with every row — so old and new
  results stay distinguishable.
- Several OpenRouter slugs are best-effort (flagged with `TODO`); verify
  against `https://openrouter.ai/api/v1/models` before the live run.
