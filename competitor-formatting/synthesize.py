"""Synthesize TTS audio for each row in manifest.csv via Deepgram Aura-2.

Reads manifest.csv (id, entity_class, input_text, ...), calls Deepgram TTS
on input_text, and writes audio/<entity_class>/<id>.mp3. Resumable — skips
rows whose audio file already exists.

Usage:
    DEEPGRAM_API_KEY=... uv run python competitor-formatting/synthesize.py
    # or with custom voice / concurrency:
    uv run python competitor-formatting/synthesize.py --voice aura-2-thalia-en --concurrency 8
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.csv"
AUDIO_ROOT = HERE / "audio"
DG_TTS_URL = "https://api.deepgram.com/v1/speak"


def synthesize_one(client: httpx.Client, row: dict, voice: str, out_path: Path) -> tuple[str, str | None]:
    if out_path.exists() and out_path.stat().st_size > 0:
        return row["id"], None  # already done
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = client.post(
            DG_TTS_URL,
            params={"model": voice, "encoding": "mp3"},
            json={"text": row["input_text"]},
            timeout=60.0,
        )
        if resp.status_code != 200:
            return row["id"], f"http_{resp.status_code}: {resp.text[:200]}"
        out_path.write_bytes(resp.content)
        if out_path.stat().st_size < 256:
            return row["id"], f"too_small: {out_path.stat().st_size} bytes"
        return row["id"], None
    except Exception as e:  # noqa: BLE001
        return row["id"], f"{type(e).__name__}: {e}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--voice", default="aura-2-thalia-en", help="Deepgram TTS model")
    p.add_argument("--concurrency", type=int, default=6)
    p.add_argument("--limit", type=int, default=0, help="0 = all rows")
    args = p.parse_args()

    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        print("ERROR: DEEPGRAM_API_KEY not set", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(MANIFEST.open()))
    if args.limit:
        rows = rows[: args.limit]

    todo: list[tuple[dict, Path]] = []
    skipped = 0
    for r in rows:
        out = AUDIO_ROOT / r["entity_class"] / f"{r['id']}.mp3"
        if out.exists() and out.stat().st_size > 0:
            skipped += 1
            continue
        todo.append((r, out))

    print(f"manifest={len(rows)}  already-done={skipped}  to-synthesize={len(todo)}")
    if not todo:
        return 0

    started = time.time()
    errors: list[tuple[str, str]] = []
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    with httpx.Client(headers=headers) as client:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {
                pool.submit(synthesize_one, client, r, args.voice, out): r["id"]
                for r, out in todo
            }
            done = 0
            for fut in as_completed(futures):
                row_id, err = fut.result()
                done += 1
                if err:
                    errors.append((row_id, err))
                    print(f"  [{done}/{len(todo)}] FAIL {row_id}: {err}")
                else:
                    print(f"  [{done}/{len(todo)}] ok   {row_id}")

    elapsed = time.time() - started
    ok = len(todo) - len(errors)
    print(f"\ndone: {ok} ok, {len(errors)} failed, {elapsed:.1f}s ({elapsed/max(1,len(todo)):.2f}s/clip)")
    if errors:
        print("\nFailures:")
        for rid, err in errors:
            print(f"  {rid}: {err}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
