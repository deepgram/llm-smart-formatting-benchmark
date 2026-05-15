"""Thin wrapper around the ``together`` SDK for fine-tuning + inference.

We deliberately keep this minimal — the Together SDK is small and the
benchmark already has plenty of glue. This module exists so the CLI in
``main.py`` reads top-to-bottom and so we can stub out the SDK in
``--dry-run`` mode without conditional imports leaking everywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _client():  # lazy import: the SDK is an optional dep
    try:
        from together import Together
    except ImportError as e:  # noqa: BLE001
        raise RuntimeError(
            "The `together` package is not installed. "
            "Run `uv sync` after pulling the updated pyproject.toml, "
            "or `pip install together`."
        ) from e
    key = os.environ.get("TOGETHER_API_KEY")
    if not key:
        raise RuntimeError(
            "TOGETHER_API_KEY env var is not set. Export it before running "
            "any Together commands (upload, train, infer)."
        )
    return Together(api_key=key)


# ----------------- files -----------------


@dataclass
class UploadResult:
    file_id: str
    filename: str
    bytes: int


def upload_training_file(path: str, *, purpose: str = "fine-tune") -> UploadResult:
    c = _client()
    resp = c.files.upload(file=path, purpose=purpose, check=True)
    return UploadResult(
        file_id=resp.id,
        filename=getattr(resp, "filename", path),
        bytes=int(getattr(resp, "bytes", 0) or 0),
    )


# ----------------- fine-tuning -----------------


@dataclass
class FineTuneResult:
    job_id: str
    status: str
    output_name: str | None


def create_lora_finetune(
    *,
    training_file_id: str,
    base_model: str,
    suffix: str,
    n_epochs: int = 3,
    learning_rate: float = 1e-4,
    n_checkpoints: int = 1,
    warmup_ratio: float = 0.03,
    train_on_inputs: str = "auto",
    batch_size: str | int = "max",
) -> FineTuneResult:
    """Kick off a LoRA fine-tune. Returns immediately — poll with ``retrieve``."""
    c = _client()
    resp = c.fine_tuning.create(
        training_file=training_file_id,
        model=base_model,
        train_on_inputs=train_on_inputs,
        n_epochs=n_epochs,
        n_checkpoints=n_checkpoints,
        lora=True,
        warmup_ratio=warmup_ratio,
        learning_rate=learning_rate,
        batch_size=batch_size,
        suffix=suffix,
    )
    return FineTuneResult(
        job_id=resp.id,
        status=str(getattr(resp, "status", "queued")),
        output_name=getattr(resp, "output_name", None),
    )


def retrieve_finetune(job_id: str) -> FineTuneResult:
    c = _client()
    resp = c.fine_tuning.retrieve(job_id)
    return FineTuneResult(
        job_id=resp.id,
        status=str(getattr(resp, "status", "unknown")),
        output_name=getattr(resp, "output_name", None),
    )


def list_finetune_events(job_id: str) -> list[str]:
    c = _client()
    events = c.fine_tuning.list_events(id=job_id).data
    return [getattr(e, "message", str(e)) for e in events]


# ----------------- inference (sync; we add async fan-out in infer.py) -----------------


# ----------------- dedicated endpoints -----------------


@dataclass
class EndpointInfo:
    id: str
    name: str         # full routing handle, e.g. <model>-<8-char hash>; use for chat.completions
    model: str        # the underlying model id (no unique suffix)
    hardware: str
    state: str
    display_name: str | None


def _endpoint_to_info(ep) -> EndpointInfo:
    return EndpointInfo(
        id=ep.id,
        name=str(getattr(ep, "name", "")),
        model=str(getattr(ep, "model", "")),
        hardware=str(getattr(ep, "hardware", "")),
        state=str(getattr(ep, "state", "")),
        display_name=getattr(ep, "display_name", None),
    )


def list_endpoint_hardware(model: str) -> list[dict]:
    c = _client()
    resp = c.endpoints.list_hardware(model=model)
    return [h.model_dump() if hasattr(h, "model_dump") else dict(h) for h in resp.data]


def create_endpoint(
    *,
    model: str,
    hardware: str,
    display_name: str,
    inactive_timeout: int = 10,
    min_replicas: int = 1,
    max_replicas: int = 1,
    availability_zone: str | None = None,
) -> EndpointInfo:
    c = _client()
    kwargs = dict(
        model=model,
        hardware=hardware,
        display_name=display_name,
        autoscaling={"min_replicas": min_replicas, "max_replicas": max_replicas},
        inactive_timeout=inactive_timeout,
        state="STARTED",
    )
    if availability_zone:
        kwargs["availability_zone"] = availability_zone
    ep = c.endpoints.create(**kwargs)
    return _endpoint_to_info(ep)


def retrieve_endpoint(endpoint_id: str) -> EndpointInfo:
    c = _client()
    return _endpoint_to_info(c.endpoints.retrieve(endpoint_id))


def stop_endpoint(endpoint_id: str) -> EndpointInfo:
    c = _client()
    return _endpoint_to_info(c.endpoints.update(endpoint_id, state="STOPPED"))


def delete_endpoint(endpoint_id: str) -> None:
    c = _client()
    c.endpoints.delete(endpoint_id)


def chat_complete(
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> dict:
    """Single chat-completions call. Returns a small dict so callers don't
    couple to the SDK's response objects."""
    c = _client()
    resp = c.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    choice = resp.choices[0]
    usage = getattr(resp, "usage", None)
    return {
        "content": (choice.message.content or "").strip(),
        "finish_reason": str(getattr(choice, "finish_reason", "")),
        "tokens_in": int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0,
        "tokens_out": int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0,
    }
