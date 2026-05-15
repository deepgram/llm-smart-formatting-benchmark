#!/usr/bin/env bash
# Wait → deploy → eval (concurrency=1) → stop+delete → score, in parallel
# across all 5 v3 fine-tune runs. Triggered after `finetune train` has
# submitted the jobs.
#
# Each model writes its own log under finetune/runs/<dir>/orchestrate.log.
set -uo pipefail

cd "$(dirname "$0")/../.."  # repo root

run_pipeline() {
  local OUT="finetune/runs/$1"
  local MODEL_ID="$2"
  local LOG="$OUT/orchestrate.log"
  : > "$LOG"

  {
    echo "[$(date -u +%FT%TZ)] [$MODEL_ID] waiting for FT to produce an output_name…"
    # We poll `finetune status` and gate on output_name being populated in
    # job_info.json. Together's GET sometimes returns output_name=None even
    # for completed jobs (race during the upload step), so checking
    # `status == completed` is unreliable — output_name presence is what
    # deploy-eval-stop actually needs.
    OUTPUT_NAME=""
    for i in $(seq 1 360); do  # 360 * 60s = 6h cap
      uv run finetune status --out-dir "$OUT" --events > /dev/null 2>&1 || true
      OUTPUT_NAME=$(python3 -c "import json; print(json.load(open('$OUT/job_info.json')).get('output_name') or '')")
      STATUS=$(python3 -c "import json; print(json.load(open('$OUT/job_info.json')).get('status') or '')")
      if [ -n "$OUTPUT_NAME" ]; then
        echo "[$(date -u +%FT%TZ)] [$MODEL_ID] FT ready (output_name set, status=$STATUS)."
        break
      fi
      case "$STATUS" in
        error|failed|cancelled)
          echo "[$(date -u +%FT%TZ)] [$MODEL_ID] FT in terminal failure: $STATUS"
          return 1
          ;;
      esac
      sleep 60
    done
    if [ -z "$OUTPUT_NAME" ]; then
      echo "[$(date -u +%FT%TZ)] [$MODEL_ID] timed out waiting for output_name."
      return 1
    fi

    echo "[$(date -u +%FT%TZ)] [$MODEL_ID] deploy → eval (concurrency=1) → stop+delete…"
    uv run finetune deploy-eval-stop \
      --model-id "$MODEL_ID" \
      --out-dir "$OUT" \
      --eval-csv finetune/data/eval.csv \
      --concurrency 1 \
      --delete-after

    # Find the newly-created results dir for this model_id.
    RUN_DIR=$(ls -td "results/${MODEL_ID}-"* 2>/dev/null | head -1)
    if [ -z "$RUN_DIR" ]; then
      echo "[$(date -u +%FT%TZ)] [$MODEL_ID] could not find results dir — skipping score."
      return 2
    fi
    echo "[$(date -u +%FT%TZ)] [$MODEL_ID] scoring ${RUN_DIR}"
    uv run python -m evaluator.main score \
      --responses "$RUN_DIR" \
      --dataset finetune/data/eval.csv

    echo "[$(date -u +%FT%TZ)] [$MODEL_ID] DONE"
  } >> "$LOG" 2>&1
}

run_pipeline gemma-3-270m-v3 ft-gemma-3-270m-v3-c1 &
PID1=$!
run_pipeline gemma-3-1b-v3   ft-gemma-3-1b-v3-c1   &
PID2=$!
run_pipeline llama-3.2-3b-v3 ft-llama-3.2-3b-v3-c1 &
PID3=$!
run_pipeline qwen3-8b-v3     ft-qwen3-8b-v3-c1     &
PID4=$!
run_pipeline qwen3.5-9b-v3   ft-qwen3.5-9b-v3-c1   &
PID5=$!

echo "Launched 5 pipelines: $PID1 $PID2 $PID3 $PID4 $PID5"
wait $PID1; R1=$?
wait $PID2; R2=$?
wait $PID3; R3=$?
wait $PID4; R4=$?
wait $PID5; R5=$?
echo "Exit codes: gemma-270m=$R1 gemma-1b=$R2 llama-3b=$R3 qwen3-8b=$R4 qwen3.5-9b=$R5"
exit 0
