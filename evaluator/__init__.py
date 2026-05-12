"""Evaluator package for the smart-formatting benchmark.

Scores responses produced by ``runner`` along four axes:

1. Programmatic exact-match (whitespace-normalized, NFC).
2. Programmatic regex checks for canonical-form prompts.
3. LLM-judge accuracy + promptability + catastrophic flag (Anthropic Opus).
4. LLM-judge hallucination check (separate Anthropic call).

CLI entry: ``uv run evaluator score --responses results/<run_id>/responses.csv``.
"""

from __future__ import annotations
