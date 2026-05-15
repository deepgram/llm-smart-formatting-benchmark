"""Transcribe each audio file with one or more competitor STT providers.

Reads manifest.csv + audio/<entity_class>/<id>.mp3 and writes per-provider
output to responses/<provider>.csv with columns:
    id, entity_class, expected_output, transcript, error, latency_ms

Resumable — re-running skips rows already present in the provider's CSV.

Providers:
  - deepgram     (baseline; needs DEEPGRAM_API_KEY)         nova-3 + smart_format
  - elevenlabs   (needs ELEVENLABS_API_KEY)                  scribe_v1
  - openai       (needs OPENAI_API_KEY)                      gpt-4o-transcribe
  - azure        (needs AZURE_SPEECH_KEY [+ AZURE_SPEECH_REGION, default eastus])
                                                             fast transcription api
  - google       (needs GOOGLE_API_KEY)                      cloud speech v1
  - soniox       (needs SONIOX_API_KEY)                      stt-async-preview

Usage:
    uv run python competitor-formatting/transcribe.py --providers deepgram
    uv run python competitor-formatting/transcribe.py --providers all
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import httpx

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.csv"
AUDIO_ROOT = HERE / "audio"
RESP_ROOT = HERE / "responses"

ResultRow = dict  # {id, entity_class, expected_output, transcript, error, latency_ms}


# ---------- providers ----------


def transcribe_deepgram(audio: bytes) -> tuple[str, str | None]:
    key = os.environ["DEEPGRAM_API_KEY"]
    r = httpx.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": "nova-3", "smart_format": "true", "punctuate": "true"},
        headers={"Authorization": f"Token {key}", "Content-Type": "audio/mpeg"},
        content=audio,
        timeout=60.0,
    )
    if r.status_code != 200:
        return "", f"http_{r.status_code}: {r.text[:200]}"
    j = r.json()
    try:
        txt = j["results"]["channels"][0]["alternatives"][0]["transcript"]
        return txt, None
    except (KeyError, IndexError) as e:
        return "", f"parse: {e}; body={str(j)[:200]}"


def transcribe_elevenlabs(audio: bytes) -> tuple[str, str | None]:
    key = os.environ["ELEVENLABS_API_KEY"]
    r = httpx.post(
        "https://api.elevenlabs.io/v1/speech-to-text",
        headers={"xi-api-key": key},
        data={"model_id": "scribe_v1"},
        files={"file": ("audio.mp3", audio, "audio/mpeg")},
        timeout=120.0,
    )
    if r.status_code != 200:
        return "", f"http_{r.status_code}: {r.text[:200]}"
    j = r.json()
    txt = j.get("text") or ""
    return txt, None if txt else "empty"


def transcribe_openai(audio: bytes) -> tuple[str, str | None]:
    key = os.environ["OPENAI_API_KEY"]
    r = httpx.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {key}"},
        data={"model": "gpt-4o-transcribe", "response_format": "text"},
        files={"file": ("audio.mp3", audio, "audio/mpeg")},
        timeout=120.0,
    )
    if r.status_code != 200:
        return "", f"http_{r.status_code}: {r.text[:200]}"
    return r.text.strip(), None


def transcribe_azure(audio: bytes) -> tuple[str, str | None]:
    key = os.environ["AZURE_SPEECH_KEY"]
    region = os.environ.get("AZURE_SPEECH_REGION", "eastus")
    url = (
        f"https://{region}.api.cognitive.microsoft.com/speechtotext/"
        "transcriptions:transcribe?api-version=2024-11-15"
    )
    definition = json.dumps({"locales": ["en-US"], "profanityFilterMode": "None"})
    r = httpx.post(
        url,
        headers={"Ocp-Apim-Subscription-Key": key, "Accept": "application/json"},
        files={
            "audio": ("audio.mp3", audio, "audio/mpeg"),
            "definition": (None, definition, "application/json"),
        },
        timeout=120.0,
    )
    if r.status_code != 200:
        return "", f"http_{r.status_code}: {r.text[:200]}"
    j = r.json()
    try:
        phrases = j.get("combinedPhrases") or []
        if phrases:
            return phrases[0].get("text", ""), None
        # fallback to per-phrase
        parts = [p.get("text", "") for p in j.get("phrases", [])]
        return " ".join(parts).strip(), None
    except Exception as e:  # noqa: BLE001
        return "", f"parse: {e}; body={str(j)[:200]}"


def transcribe_google(audio: bytes) -> tuple[str, str | None]:
    key = os.environ["GOOGLE_API_KEY"]
    body = {
        "config": {
            "encoding": "MP3",
            "sampleRateHertz": 24000,
            "languageCode": "en-US",
            "enableAutomaticPunctuation": True,
            "model": "latest_long",
        },
        "audio": {"content": base64.b64encode(audio).decode("ascii")},
    }
    r = httpx.post(
        f"https://speech.googleapis.com/v1/speech:recognize?key={key}",
        json=body,
        timeout=120.0,
    )
    if r.status_code != 200:
        return "", f"http_{r.status_code}: {r.text[:200]}"
    j = r.json()
    results = j.get("results") or []
    parts = []
    for res in results:
        alts = res.get("alternatives") or []
        if alts:
            parts.append(alts[0].get("transcript", ""))
    return " ".join(p.strip() for p in parts if p).strip(), None


def transcribe_soniox(audio: bytes) -> tuple[str, str | None]:
    key = os.environ["SONIOX_API_KEY"]
    auth = {"Authorization": f"Bearer {key}"}

    # 1. Upload file
    r = httpx.post(
        "https://api.soniox.com/v1/files",
        headers=auth,
        files={"file": ("audio.mp3", audio, "audio/mpeg")},
        timeout=60.0,
    )
    if r.status_code not in (200, 201):
        return "", f"upload_http_{r.status_code}: {r.text[:200]}"
    file_id = r.json().get("id")
    if not file_id:
        return "", f"upload: no id; body={r.text[:200]}"

    # 2. Create transcription
    r = httpx.post(
        "https://api.soniox.com/v1/transcriptions",
        headers={**auth, "Content-Type": "application/json"},
        json={"file_id": file_id, "model": "stt-async-preview", "language_hints": ["en"]},
        timeout=60.0,
    )
    if r.status_code not in (200, 201):
        return "", f"create_http_{r.status_code}: {r.text[:200]}"
    tid = r.json().get("id")
    if not tid:
        return "", f"create: no id; body={r.text[:200]}"

    # 3. Poll until completed
    deadline = time.time() + 90.0
    while time.time() < deadline:
        time.sleep(1.5)
        r = httpx.get(
            f"https://api.soniox.com/v1/transcriptions/{tid}",
            headers=auth,
            timeout=30.0,
        )
        if r.status_code != 200:
            return "", f"poll_http_{r.status_code}: {r.text[:200]}"
        status = r.json().get("status")
        if status == "completed":
            break
        if status in ("error", "failed"):
            return "", f"transcription_failed: {r.text[:200]}"
    else:
        return "", "soniox_timeout"

    # 4. Fetch transcript
    r = httpx.get(
        f"https://api.soniox.com/v1/transcriptions/{tid}/transcript",
        headers=auth,
        timeout=30.0,
    )
    if r.status_code != 200:
        return "", f"transcript_http_{r.status_code}: {r.text[:200]}"
    j = r.json()
    return (j.get("text") or "").strip(), None


PROVIDERS: dict[str, tuple[Callable[[bytes], tuple[str, str | None]], str]] = {
    "deepgram":   (transcribe_deepgram,   "DEEPGRAM_API_KEY"),
    "elevenlabs": (transcribe_elevenlabs, "ELEVENLABS_API_KEY"),
    "openai":     (transcribe_openai,     "OPENAI_API_KEY"),
    "azure":      (transcribe_azure,      "AZURE_SPEECH_KEY"),
    "google":     (transcribe_google,     "GOOGLE_API_KEY"),
    "soniox":     (transcribe_soniox,     "SONIOX_API_KEY"),
}


# ---------- runner ----------


FIELDS = ["id", "entity_class", "expected_output", "transcript", "error", "latency_ms"]


def _load_done(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open() as f:
        return {row["id"] for row in csv.DictReader(f) if not row.get("error")}


def _run_provider(name: str, rows: list[dict], concurrency: int) -> None:
    fn, env_var = PROVIDERS[name]
    if not os.environ.get(env_var):
        print(f"[{name}] SKIP — {env_var} not set")
        return

    out_csv = RESP_ROOT / f"{name}.csv"
    done = _load_done(out_csv)
    todo = [r for r in rows if r["id"] not in done]
    print(f"[{name}] manifest={len(rows)}  done={len(done)}  todo={len(todo)}")
    if not todo:
        return

    RESP_ROOT.mkdir(parents=True, exist_ok=True)
    write_header = not out_csv.exists()
    f = out_csv.open("a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if write_header:
        w.writeheader()
        f.flush()

    def worker(row: dict) -> ResultRow:
        path = AUDIO_ROOT / row["entity_class"] / f"{row['id']}.mp3"
        if not path.exists():
            return {**_base(row), "error": "audio_missing"}
        audio = path.read_bytes()
        t0 = time.perf_counter()
        try:
            txt, err = fn(audio)
        except Exception as e:  # noqa: BLE001
            txt, err = "", f"{type(e).__name__}: {e}"
        dt = int((time.perf_counter() - t0) * 1000)
        return {**_base(row), "transcript": txt, "error": err or "", "latency_ms": dt}

    started = time.time()
    fail = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(worker, r): r["id"] for r in todo}
        completed = 0
        for fut in as_completed(futures):
            res = fut.result()
            completed += 1
            w.writerow(res)
            f.flush()
            if res["error"]:
                fail += 1
                print(f"  [{completed}/{len(todo)}] FAIL {res['id']}: {res['error']}")
            else:
                preview = res["transcript"][:60].replace("\n", " ")
                print(f"  [{completed}/{len(todo)}] ok  {res['id']} ({res['latency_ms']}ms) {preview!r}")
    f.close()
    print(f"[{name}] done in {time.time() - started:.1f}s — {len(todo)-fail} ok, {fail} failed")


def _base(row: dict) -> ResultRow:
    return {
        "id": row["id"],
        "entity_class": row["entity_class"],
        "expected_output": row["expected_output"],
        "transcript": "",
        "error": "",
        "latency_ms": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--providers", default="deepgram",
                   help="comma-separated subset of: " + ",".join(PROVIDERS))
    p.add_argument("--concurrency", type=int, default=6)
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    if args.providers.strip() == "all":
        requested = list(PROVIDERS.keys())
    else:
        requested = [p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = [p for p in requested if p not in PROVIDERS]
    if unknown:
        print(f"ERROR: unknown providers: {unknown}. Known: {list(PROVIDERS)}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(MANIFEST.open()))
    if args.limit:
        rows = rows[: args.limit]

    for name in requested:
        _run_provider(name, rows, args.concurrency)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
