# Competitor STT smart-formatting eval

Synthesizes audio from our held-out test set with Deepgram TTS, then
transcribes each clip with competitor STT providers to compare how well
their built-in smart-formatting handles entities (money, dates, phones,
addresses, etc.).

## Layout

```
competitor-formatting/
├── manifest.csv          160 rows (10 per entity class) — id, entity_class, input_text, expected_output, ...
├── audio/<class>/<id>.mp3   Deepgram Aura-2 TTS of input_text
├── responses/<provider>.csv         raw STT output per provider
├── responses/<provider>.scored.csv  judged output per provider
├── synthesize.py         TTS — manifest → audio/
├── transcribe.py         STT — audio/ → responses/<provider>.csv
└── score.py              Claude Opus 4.7 judge → responses/<provider>.scored.csv
```

## Setup

```bash
export DEEPGRAM_API_KEY=...        # for TTS + Deepgram STT baseline
export ELEVENLABS_API_KEY=...      # optional, for Scribe
export OPENAI_API_KEY=...          # optional, for gpt-4o-transcribe
export AZURE_SPEECH_KEY=...        # optional, for Azure Fast Transcription
export AZURE_SPEECH_REGION=eastus  #   (defaults to eastus)
export GOOGLE_API_KEY=...          # optional, for Google Cloud Speech v1
export SONIOX_API_KEY=...          # optional, for Soniox stt-async-preview
export ANTHROPIC_API_KEY=...       # for scoring
```

## Run

```bash
# 1. Generate 160 mp3s (~3 min @ concurrency 6)
uv run python competitor-formatting/synthesize.py

# 2. Transcribe with one or more providers
uv run python competitor-formatting/transcribe.py --providers all
# or pick a subset:
uv run python competitor-formatting/transcribe.py --providers deepgram,azure,google

# 3. Score each provider against expected_output
for p in deepgram elevenlabs openai azure google soniox; do
  uv run python competitor-formatting/score.py --provider $p
done
```

All scripts are resumable — re-running skips rows that already have output.

## Notes

- TTS voice: `aura-2-thalia-en`. Override with `--voice`.
- Deepgram STT: `nova-3` + `smart_format=true` + `punctuate=true`.
- ElevenLabs STT: `scribe_v1`.
- OpenAI STT: `gpt-4o-transcribe`.
- Azure STT: Fast Transcription API (`api-version=2024-11-15`, locale `en-US`).
- Google STT: Cloud Speech v1 sync `recognize` + `enableAutomaticPunctuation`.
- Soniox STT: `stt-async-preview` (async with polling).
- The judge model is Claude Opus 4.7 (same one used by `evaluator/`).
