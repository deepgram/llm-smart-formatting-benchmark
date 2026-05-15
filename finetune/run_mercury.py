"""Run Mercury 2 (Inception Labs diffusion LLM) on the eval set.

Uses the same eval.csv held-out test set that the fine-tunes were graded
on, and the same system prompt (build_messages). Runs once per reasoning
level so we can see the speed/accuracy curve.

Rate limit: capped at 4 requests/second (Inception's documented limit).

Outputs:
    finetune/runs/mercury-2/<level>/responses.csv

Columns:
    id, entity_class, expected_output, response, latency_ms,
    reasoning_tokens, completion_tokens, total_tokens, error

Usage:
    INCEPTION_API_KEY=... uv run python -m finetune.run_mercury \\
        --levels instant,low,medium,high
    uv run python -m finetune.run_mercury --levels high --limit 5  # smoke
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
import time
from pathlib import Path

import httpx

from finetune.prompts import build_messages

HERE = Path(__file__).resolve().parent
RUNS_ROOT = HERE / "runs" / "mercury-2"
EVAL_CSV = HERE / "data" / "eval.csv"
API_URL = "https://api.inceptionlabs.ai/v1/chat/completions"
MODEL = "mercury-2"
RATE_LIMIT_RPS = 4.0
LEVELS = ["instant", "low", "medium", "high"]

FIELDS = [
    "id", "entity_class", "expected_output", "response",
    "latency_ms", "reasoning_tokens", "completion_tokens", "total_tokens", "error",
]


class RateLimiter:
    """Simple async token-bucket: at most `rps` requests/sec."""
    def __init__(self, rps: float):
        self.min_interval = 1.0 / rps
        self.lock = asyncio.Lock()
        self.next_slot = 0.0

    async def acquire(self) -> None:
        async with self.lock:
            now = time.monotonic()
            wait = max(0.0, self.next_slot - now)
            self.next_slot = max(now, self.next_slot) + self.min_interval
        if wait > 0:
            await asyncio.sleep(wait)


def _load_done(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open() as f:
        return {row["id"] for row in csv.DictReader(f) if not row.get("error")}


async def _call_mercury(
    client: httpx.AsyncClient,
    api_key: str,
    level: str,
    row: dict,
    max_tokens: int,
) -> dict:
    messages = build_messages(
        input_text=row["input_text"],
        formatting_prompt=row.get("prompt") or None,
    )
    body = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.5,  # Mercury rejects <0.5
        "reasoning_effort": level,
    }
    t0 = time.perf_counter()
    # Retry on 429 (output TPM exhaustion at high reasoning) with backoff
    backoffs = [5.0, 12.0, 25.0, 45.0]
    try:
        r = None
        for attempt in range(len(backoffs) + 1):
            r = await client.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=body,
                timeout=180.0,
            )
            if r.status_code != 429 or attempt == len(backoffs):
                break
            retry_after = r.headers.get("retry-after")
            sleep_s = float(retry_after) if retry_after and retry_after.replace(".", "").isdigit() else backoffs[attempt]
            await asyncio.sleep(sleep_s)
        dt = int((time.perf_counter() - t0) * 1000)
        if r.status_code != 200:
            return _err(row, dt, f"http_{r.status_code}: {r.text[:300]}")
        j = r.json()
        choice = j["choices"][0]
        content = (choice["message"].get("content") or "").strip()
        usage = j.get("usage", {})
        return {
            "id": row["id"],
            "entity_class": row["entity_class"],
            "expected_output": row["expected_output"],
            "response": content,
            "latency_ms": dt,
            "reasoning_tokens": usage.get("reasoning_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "error": "" if content else f"empty_content (finish_reason={choice.get('finish_reason')})",
        }
    except Exception as e:  # noqa: BLE001
        dt = int((time.perf_counter() - t0) * 1000)
        return _err(row, dt, f"{type(e).__name__}: {e}")


def _err(row: dict, dt: int, msg: str) -> dict:
    return {
        "id": row["id"],
        "entity_class": row["entity_class"],
        "expected_output": row["expected_output"],
        "response": "",
        "latency_ms": dt,
        "reasoning_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "error": msg,
    }


async def _run_level(level: str, rows: list[dict], max_tokens: int, concurrency: int) -> None:
    out_dir = RUNS_ROOT / level
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "responses.csv"
    done = _load_done(out_csv)
    todo = [r for r in rows if r["id"] not in done]
    print(f"[{level}] total={len(rows)}  done={len(done)}  todo={len(todo)}")
    if not todo:
        return

    api_key = os.environ["INCEPTION_API_KEY"]
    limiter = RateLimiter(RATE_LIMIT_RPS)
    sem = asyncio.Semaphore(concurrency)

    write_header = not out_csv.exists()
    f = out_csv.open("a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if write_header:
        w.writeheader()
        f.flush()

    lock = asyncio.Lock()
    started = time.time()
    completed = 0
    fail = 0

    async with httpx.AsyncClient() as client:
        async def worker(row: dict) -> None:
            nonlocal completed, fail
            async with sem:
                await limiter.acquire()
                res = await _call_mercury(client, api_key, level, row, max_tokens)
            async with lock:
                w.writerow(res)
                f.flush()
                completed += 1
                if res["error"]:
                    fail += 1
                    print(f"  [{level} {completed}/{len(todo)}] FAIL {res['id']}: {res['error'][:120]}")
                else:
                    preview = res["response"][:60].replace("\n", " ")
                    print(f"  [{level} {completed}/{len(todo)}] ok  {res['id']} ({res['latency_ms']}ms, rt={res['reasoning_tokens']}) {preview!r}")

        await asyncio.gather(*[worker(r) for r in todo])

    f.close()
    elapsed = time.time() - started
    print(f"[{level}] done in {elapsed:.1f}s — {len(todo)-fail} ok, {fail} failed")


async def _amain(levels: list[str], limit: int, max_tokens: int, concurrency: int) -> None:
    rows = list(csv.DictReader(EVAL_CSV.open()))
    if limit:
        rows = rows[:limit]
    print(f"Mercury 2 eval — {len(rows)} rows, levels={levels}, max_tokens={max_tokens}, rps≤{RATE_LIMIT_RPS}")
    for lvl in levels:
        await _run_level(lvl, rows, max_tokens, concurrency)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--levels", default=",".join(LEVELS),
                   help=f"comma-separated subset of {LEVELS}")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--max-tokens", type=int, default=4096,
                   help="must be large enough to cover reasoning_tokens + completion at 'high'")
    p.add_argument("--concurrency", type=int, default=4,
                   help="async concurrency; rate limiter caps overall RPS regardless")
    args = p.parse_args()

    if not os.environ.get("INCEPTION_API_KEY"):
        print("ERROR: INCEPTION_API_KEY not set", file=sys.stderr)
        return 1

    levels = [x.strip() for x in args.levels.split(",") if x.strip()]
    unknown = [x for x in levels if x not in LEVELS]
    if unknown:
        print(f"ERROR: unknown reasoning levels: {unknown}; valid={LEVELS}", file=sys.stderr)
        return 1

    asyncio.run(_amain(levels, args.limit, args.max_tokens, args.concurrency))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
