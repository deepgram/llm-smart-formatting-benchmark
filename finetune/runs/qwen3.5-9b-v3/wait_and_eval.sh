#!/usr/bin/env bash
# Properly-gated watcher for qwen3.5-9b-v3: waits on the LIVE Together API
# until (status == completed AND output_name != ""), then runs
# deploy → eval (concurrency=1) → stop+delete → score.
set -uo pipefail

cd "$(dirname "$0")/../../.."  # repo root
export TOGETHER_API_KEY="$(grep TOGETHER_API_KEY finetune/.env | cut -d= -f2-)"

OUT=finetune/runs/qwen3.5-9b-v3
MODEL_ID=ft-qwen3.5-9b-v3-c1
JOB_ID=$(python3 -c "import json; print(json.load(open('$OUT/job_info.json'))['job_id'])")
LOG=$OUT/orchestrate.log

{
  echo "[$(date -u +%FT%TZ)] [$MODEL_ID] watching job=$JOB_ID via live API…"
  for i in $(seq 1 360); do
    RES=$(uv run python -c "
from finetune.together_client import retrieve_finetune
r = retrieve_finetune('$JOB_ID')
print(f'{r.status}|{r.output_name or \"\"}')
" 2>/dev/null)
    STATUS=$(echo "$RES" | cut -d'|' -f1)
    OUTPUT_NAME=$(echo "$RES" | cut -d'|' -f2)
    echo "[$(date -u +%FT%TZ)] [$MODEL_ID] poll $i: status=$STATUS  output_name=${OUTPUT_NAME: -40}"
    if [ "$STATUS" = "completed" ] && [ -n "$OUTPUT_NAME" ]; then
      # Persist the latest values to job_info.json so deploy-eval-stop can read them.
      python3 -c "
import json
p = '$OUT/job_info.json'
j = json.load(open(p))
j['status'] = '$STATUS'
j['output_name'] = '$OUTPUT_NAME'
open(p,'w').write(json.dumps(j, indent=2, sort_keys=True))
"
      echo "[$(date -u +%FT%TZ)] [$MODEL_ID] FT ready. Proceeding to deploy."
      break
    fi
    case "$STATUS" in
      error|failed|cancelled)
        echo "[$(date -u +%FT%TZ)] [$MODEL_ID] FT failed: $STATUS"
        exit 1
        ;;
    esac
    sleep 60
  done

  echo "[$(date -u +%FT%TZ)] [$MODEL_ID] deploy → eval (concurrency=1) → stop+delete…"
  uv run finetune deploy-eval-stop \
    --model-id "$MODEL_ID" \
    --out-dir "$OUT" \
    --eval-csv finetune/data/eval.csv \
    --concurrency 1 \
    --delete-after

  RUN_DIR=$(ls -td "results/${MODEL_ID}-"* 2>/dev/null | head -1)
  if [ -z "$RUN_DIR" ]; then
    echo "[$(date -u +%FT%TZ)] [$MODEL_ID] no results dir found — skip score."
    exit 2
  fi
  echo "[$(date -u +%FT%TZ)] [$MODEL_ID] scoring ${RUN_DIR}"
  uv run python -m evaluator.main score --responses "$RUN_DIR" --dataset finetune/data/eval.csv
  echo "[$(date -u +%FT%TZ)] [$MODEL_ID] DONE"
} >> "$LOG" 2>&1
