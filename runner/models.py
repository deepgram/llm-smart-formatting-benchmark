"""Model registry for the benchmark.

Each entry is keyed by ``model_id`` — that's the value that lands in
``responses.csv``. ``openrouter_slug`` is the slug we send to OpenRouter when
``route == "openrouter"``; for the three native routes (``anthropic``,
``openai``, ``google``) the ``native_model`` field is what's sent to the
respective provider SDK.

Metadata fields (``family``, ``size_tier``, ``params_total``, ``params_active``,
``architecture``, ``license``, ``open_weight``, ``thinking``,
``pinned_provider``) are recorded in the run manifest and written to
``models_used.csv`` per run so reports can group/filter by them.

Verification: closed-source slugs (Anthropic / OpenAI / Google native, Grok)
are best-effort speculative. OpenRouter slugs were verified live on
``https://openrouter.ai/api/v1/models`` on 2026-05-01.
"""

from __future__ import annotations

from typing import Any, TypedDict


# Size tiers — keep these short enums so reports can group.
SIZE_FRONTIER = "frontier"   # >200B total OR top-tier closed (Opus/GPT-5.5-pro)
SIZE_LARGE = "large"         # 50–200B
SIZE_MID = "mid"             # 20–50B
SIZE_SMALL = "small"         # 5–20B
SIZE_TINY = "tiny"           # <5B
SIZE_UNKNOWN = "unknown"

# Architecture
ARCH_DENSE = "dense"
ARCH_MOE = "moe"
ARCH_DIFFUSION = "diffusion"
ARCH_UNKNOWN = "unknown"

# Common license tags
LIC_APACHE2 = "Apache-2.0"
LIC_MIT = "MIT"
LIC_MIT_MOD = "MIT-Modified"
LIC_LLAMA33 = "Llama-3.3-Community"
LIC_LLAMA31 = "Llama-3.1-Community"
LIC_LLAMA32 = "Llama-3.2-Community"
LIC_LLAMA4 = "Llama-4-Community"
LIC_GEMMA = "Gemma-Terms"
LIC_NVIDIA_OPEN = "Nvidia-Open-Model"
LIC_PROPRIETARY = "Proprietary"
LIC_LFM = "LFM-Open"
LIC_COHERE_CC_BY_NC = "CC-BY-NC-4.0"
LIC_QWEN = "Qwen-License"


class ModelEntry(TypedDict, total=False):
    # ---- routing ----
    model_id: str          # unique key, written to responses.csv
    provider: str          # human-readable provider tag (lab or pinned-provider)
    route: str             # "openrouter" | "anthropic" | "openai" | "google"
    openrouter_slug: str   # used when route == "openrouter"
    native_model: str      # used when route is one of the native provider APIs
    # ---- request shape ----
    temperature: float
    top_p: float
    max_tokens: int
    extra_body: dict[str, Any]      # thinking/reasoning toggles
    provider_routing: dict[str, Any]  # Groq/Cerebras pinning
    supports_streaming: bool
    concurrency: int                # per-model in-flight cap; 0/missing = use global
    # ---- metadata for grouping / reporting ----
    family: str            # "claude" | "gpt" | "gpt-oss" | "gemini" | "gemma" | "grok" |
                           # "deepseek" | "qwen" | "kimi" | "minimax" | "mimo" | "glm" |
                           # "mercury" | "owl" | "llama" | "mistral" | "ministral" |
                           # "phi" | "olmo" | "granite" | "nemotron"
    size_tier: str         # one of SIZE_*
    params_total: str      # e.g. "70B", "1T", "?" — string for flexibility
    params_active: str     # active params (== total for dense), e.g. "32B" for MoE
    architecture: str      # one of ARCH_*
    license: str           # short license tag
    open_weight: bool      # True if self-hostable for production
    thinking: bool         # whether THIS entry uses reasoning/thinking mode
    pinned_provider: str   # "Groq" | "Cerebras" | "" (default routing)
    # ---- free-form notes ----
    notes: str


def _entry(
    model_id: str,
    provider: str,
    slug: str,
    *,
    route: str = "openrouter",
    native_model: str = "",
    temperature: float = 0.0,
    top_p: float = 1.0,
    max_tokens: int = 1024,
    extra_body: dict[str, Any] | None = None,
    provider_routing: dict[str, Any] | None = None,
    supports_streaming: bool = True,
    concurrency: int = 0,
    # metadata
    family: str = "",
    size_tier: str = SIZE_UNKNOWN,
    params_total: str = "?",
    params_active: str = "?",
    architecture: str = ARCH_UNKNOWN,
    license: str = "",
    open_weight: bool = False,
    thinking: bool = False,
    pinned_provider: str = "",
    notes: str = "",
) -> ModelEntry:
    e: ModelEntry = {
        "model_id": model_id,
        "provider": provider,
        "route": route,
        "openrouter_slug": slug,
        "native_model": native_model,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "extra_body": extra_body or {},
        "provider_routing": provider_routing or {},
        "supports_streaming": supports_streaming,
        "concurrency": concurrency,
        "family": family,
        "size_tier": size_tier,
        "params_total": params_total,
        "params_active": params_active,
        "architecture": architecture,
        "license": license,
        "open_weight": open_weight,
        "thinking": thinking,
        "pinned_provider": pinned_provider,
        "notes": notes,
    }
    return e


# Thinking / reasoning toggles for models that *can* think but don't by default.
_CLAUDE_THINKING = {"thinking": {"type": "enabled", "budget_tokens": 1024}}
_OPENAI_REASONING_LOW = {"reasoning": {"effort": "low"}}
_GEMINI_THINKING_ON = {"reasoning": {"effort": "low"}}
_THINKING_MAX_TOKENS = 4096

# Latency matters for ASR-formatting; some OR models think by default and silently
# burn hundreds of reasoning tokens per call. Apply this to those entries.
_REASONING_OFF = {"reasoning": {"enabled": False}}

_GROQ = {"order": ["Groq"], "allow_fallbacks": False}
_CEREBRAS = {"order": ["Cerebras"], "allow_fallbacks": False}


MODEL_REGISTRY: dict[str, ModelEntry] = {
    # ============================================================
    # Anthropic — direct API
    # ============================================================
    "claude-opus-4-7": _entry(
        "claude-opus-4-7", "anthropic", "anthropic/claude-opus-4-7",
        route="anthropic", native_model="claude-opus-4-7",
        family="claude", size_tier=SIZE_FRONTIER, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
        notes="Anthropic Opus 4.7, no extended thinking.",
    ),
    "claude-sonnet-4-6": _entry(
        "claude-sonnet-4-6", "anthropic", "anthropic/claude-sonnet-4-6",
        route="anthropic", native_model="claude-sonnet-4-6",
        family="claude", size_tier=SIZE_LARGE, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
    ),
    "claude-haiku-4-5": _entry(
        "claude-haiku-4-5", "anthropic", "anthropic/claude-haiku-4-5",
        route="anthropic", native_model="claude-haiku-4-5",
        family="claude", size_tier=SIZE_MID, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
    ),
    # ============================================================
    # OpenAI — direct API
    # ============================================================
    "gpt-5-5": _entry(
        "gpt-5-5", "openai", "openai/gpt-5.5",
        route="openai", native_model="gpt-5.5",
        family="gpt", size_tier=SIZE_FRONTIER, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
    ),
    "gpt-5-4-mini": _entry(
        "gpt-5-4-mini", "openai", "openai/gpt-5.4-mini",
        route="openai", native_model="gpt-5.4-mini",
        family="gpt", size_tier=SIZE_MID, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
    ),
    # ============================================================
    # Google — direct API
    # ============================================================
    "gemini-3-1-pro-preview": _entry(
        "gemini-3-1-pro-preview", "google", "google/gemini-3.1-pro-preview",
        route="google", native_model="gemini-3.1-pro-preview",
        family="gemini", size_tier=SIZE_FRONTIER, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
        notes="Gemini 3.1 Pro preview — actual current Pro slug.",
    ),
    "gemini-3-flash-preview": _entry(
        "gemini-3-flash-preview", "google", "google/gemini-3-flash-preview",
        route="google", native_model="gemini-3-flash-preview",
        family="gemini", size_tier=SIZE_MID, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
        notes="Gemini 3 Flash preview.",
    ),
    # ============================================================
    # xAI
    # ============================================================
    "grok-4": _entry(
        "grok-4", "x-ai", "x-ai/grok-4",
        extra_body=_REASONING_OFF,
        family="grok", size_tier=SIZE_FRONTIER, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
    ),
    # ============================================================
    # DeepSeek — open-weight MIT
    # ============================================================
    "deepseek-v3-1-terminus": _entry(
        "deepseek-v3-1-terminus", "deepseek", "deepseek/deepseek-v3.1-terminus",
        extra_body=_REASONING_OFF,
        family="deepseek", size_tier=SIZE_FRONTIER, params_total="685B",
        params_active="37B", architecture=ARCH_MOE,
        license=LIC_MIT, open_weight=True,
    ),
    "deepseek-v3-2": _entry(
        "deepseek-v3-2", "deepseek", "deepseek/deepseek-v3.2",
        extra_body=_REASONING_OFF,
        family="deepseek", size_tier=SIZE_FRONTIER, params_total="685B",
        params_active="37B", architecture=ARCH_MOE,
        license=LIC_MIT, open_weight=True,
    ),
    "deepseek-v4-flash": _entry(
        "deepseek-v4-flash", "deepseek", "deepseek/deepseek-v4-flash",
        extra_body=_REASONING_OFF,
        family="deepseek", size_tier=SIZE_LARGE, params_total="284B",
        params_active="13B", architecture=ARCH_MOE,
        license=LIC_MIT, open_weight=True,
        notes="DeepSeek V4 Flash — 1M context. Reasoning disabled (default-on).",
    ),
    # ============================================================
    # Moonshot AI Kimi — open-weight Modified MIT
    # ============================================================
    "kimi-k2-6": _entry(
        "kimi-k2-6", "moonshotai", "moonshotai/kimi-k2.6",
        extra_body=_REASONING_OFF,
        family="kimi", size_tier=SIZE_FRONTIER, params_total="1T",
        params_active="32B", architecture=ARCH_MOE,
        license=LIC_MIT_MOD, open_weight=True,
        notes="Moonshot Kimi K2.6 — reasoning disabled; 256K context.",
    ),
    # ============================================================
    # Qwen — open-weight Apache 2.0
    # ============================================================
    "qwen3-235b": _entry(
        "qwen3-235b", "qwen", "qwen/qwen3-235b-a22b-2507",
        family="qwen", size_tier=SIZE_FRONTIER, params_total="235B",
        params_active="22B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-5-397b": _entry(
        "qwen3-5-397b", "qwen", "qwen/qwen3.5-397b-a17b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_FRONTIER, params_total="397B",
        params_active="17B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-next-80b": _entry(
        "qwen3-next-80b", "qwen", "qwen/qwen3-next-80b-a3b-instruct",
        family="qwen", size_tier=SIZE_LARGE, params_total="80B",
        params_active="3B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-5-122b": _entry(
        "qwen3-5-122b", "qwen", "qwen/qwen3.5-122b-a10b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_LARGE, params_total="122B",
        params_active="10B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-30b": _entry(
        "qwen3-30b", "qwen", "qwen/qwen3-30b-a3b-instruct-2507",
        family="qwen", size_tier=SIZE_MID, params_total="30B",
        params_active="3B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-5-27b": _entry(
        "qwen3-5-27b", "qwen", "qwen/qwen3.5-27b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_MID, params_total="27B",
        params_active="27B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-5-35b": _entry(
        "qwen3-5-35b", "qwen", "qwen/qwen3.5-35b-a3b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_MID, params_total="35B",
        params_active="3B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-6-35b": _entry(
        "qwen3-6-35b", "qwen", "qwen/qwen3.6-35b-a3b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_MID, params_total="35B",
        params_active="3B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-6-27b": _entry(
        "qwen3-6-27b", "qwen", "qwen/qwen3.6-27b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_MID, params_total="27B",
        params_active="27B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-14b": _entry(
        "qwen3-14b", "qwen", "qwen/qwen3-14b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_SMALL, params_total="14B",
        params_active="14B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-8b": _entry(
        "qwen3-8b", "qwen", "qwen/qwen3-8b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_SMALL, params_total="8B",
        params_active="8B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-5-9b": _entry(
        "qwen3-5-9b", "qwen", "qwen/qwen3.5-9b",
        extra_body=_REASONING_OFF,
        family="qwen", size_tier=SIZE_SMALL, params_total="9B",
        params_active="9B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "qwen3-6-flash": _entry(
        "qwen3-6-flash", "qwen", "qwen/qwen3.6-flash",
        family="qwen", size_tier=SIZE_UNKNOWN, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
        notes="Qwen3.6 Flash — closed hosted, 1M context.",
    ),
    # ============================================================
    # Poolside — closed hosted (free tier on OpenRouter)
    # ============================================================
    "laguna-xs-2-free": _entry(
        "laguna-xs-2-free", "poolside", "poolside/laguna-xs.2:free",
        family="laguna", size_tier=SIZE_UNKNOWN, params_total="undisclosed",
        params_active="undisclosed", architecture=ARCH_UNKNOWN,
        license=LIC_PROPRIETARY, open_weight=False,
        extra_body={"reasoning": {"enabled": False}},
        concurrency=1,
        notes="Poolside Laguna XS.2 free tier on OpenRouter — reasoning off, "
              "concurrency=1 to stay under the free-models 20 RPM cap.",
    ),
    # ============================================================
    # OpenAI gpt-oss — open-weight Apache 2.0
    # ============================================================
    "gpt-oss-120b": _entry(
        "gpt-oss-120b", "openai", "openai/gpt-oss-120b",
        family="gpt-oss", size_tier=SIZE_LARGE, params_total="117B",
        params_active="5.1B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
        notes="gpt-oss requires reasoning to be enabled; do not disable.",
    ),
    "gpt-oss-20b": _entry(
        "gpt-oss-20b", "openai", "openai/gpt-oss-20b",
        family="gpt-oss", size_tier=SIZE_MID, params_total="21B",
        params_active="3.6B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
        notes="gpt-oss requires reasoning to be enabled; do not disable.",
    ),
    # ============================================================
    # Mistral / Ministral — open-weight Apache 2.0
    # ============================================================
    # mistral-small-3-1-24b dropped 2026-05-01 — all OR provider routes 500ing.
    # mistral-small-3-2-24b covers the same lineage and works.
    "mistral-small-3-2-24b": _entry(
        "mistral-small-3-2-24b", "mistralai", "mistralai/mistral-small-3.2-24b-instruct",
        family="mistral", size_tier=SIZE_MID, params_total="24B",
        params_active="24B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "mistral-small-2603": _entry(
        "mistral-small-2603", "mistralai", "mistralai/mistral-small-2603",
        family="mistral", size_tier=SIZE_LARGE, params_total="119B",
        params_active="6B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True,
        notes="Mistral Small 4 119B 2603 — MoE despite the 'small' name; 256K context.",
    ),
    "mistral-nemo": _entry(
        "mistral-nemo", "mistralai", "mistralai/mistral-nemo",
        family="mistral", size_tier=SIZE_SMALL, params_total="12B",
        params_active="12B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "ministral-14b": _entry(
        "ministral-14b", "mistralai", "mistralai/ministral-14b-2512",
        family="ministral", size_tier=SIZE_SMALL, params_total="14B",
        params_active="14B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "ministral-8b": _entry(
        "ministral-8b", "mistralai", "mistralai/ministral-8b-2512",
        family="ministral", size_tier=SIZE_SMALL, params_total="8B",
        params_active="8B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "ministral-3b": _entry(
        "ministral-3b", "mistralai", "mistralai/ministral-3b-2512",
        family="ministral", size_tier=SIZE_TINY, params_total="3B",
        params_active="3B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    # ============================================================
    # Meta Llama — open-weight Llama Community License
    # ============================================================
    "llama-3-3-70b": _entry(
        "llama-3-3-70b", "meta-llama", "meta-llama/llama-3.3-70b-instruct",
        family="llama", size_tier=SIZE_LARGE, params_total="70B",
        params_active="70B", architecture=ARCH_DENSE,
        license=LIC_LLAMA33, open_weight=True,
    ),
    "llama-3-1-70b": _entry(
        "llama-3-1-70b", "meta-llama", "meta-llama/llama-3.1-70b-instruct",
        family="llama", size_tier=SIZE_LARGE, params_total="70B",
        params_active="70B", architecture=ARCH_DENSE,
        license=LIC_LLAMA31, open_weight=True,
    ),
    "llama-3-1-8b": _entry(
        "llama-3-1-8b", "meta-llama", "meta-llama/llama-3.1-8b-instruct",
        family="llama", size_tier=SIZE_SMALL, params_total="8B",
        params_active="8B", architecture=ARCH_DENSE,
        license=LIC_LLAMA31, open_weight=True,
    ),
    "llama-3-2-3b": _entry(
        "llama-3-2-3b", "meta-llama", "meta-llama/llama-3.2-3b-instruct",
        family="llama", size_tier=SIZE_TINY, params_total="3B",
        params_active="3B", architecture=ARCH_DENSE,
        license=LIC_LLAMA32, open_weight=True,
    ),
    "llama-4-scout": _entry(
        "llama-4-scout", "meta-llama", "meta-llama/llama-4-scout",
        family="llama", size_tier=SIZE_LARGE, params_total="109B",
        params_active="17B", architecture=ARCH_MOE,
        license=LIC_LLAMA4, open_weight=True,
    ),
    "llama-4-maverick": _entry(
        "llama-4-maverick", "meta-llama", "meta-llama/llama-4-maverick",
        family="llama", size_tier=SIZE_FRONTIER, params_total="400B",
        params_active="17B", architecture=ARCH_MOE,
        license=LIC_LLAMA4, open_weight=True,
    ),
    # ============================================================
    # Google Gemma — open-weight Gemma Terms
    # ============================================================
    "gemma-3-27b-it": _entry(
        "gemma-3-27b-it", "google", "google/gemma-3-27b-it",
        family="gemma", size_tier=SIZE_MID, params_total="27B",
        params_active="27B", architecture=ARCH_DENSE,
        license=LIC_GEMMA, open_weight=True,
    ),
    "gemma-3-12b-it": _entry(
        "gemma-3-12b-it", "google", "google/gemma-3-12b-it",
        family="gemma", size_tier=SIZE_SMALL, params_total="12B",
        params_active="12B", architecture=ARCH_DENSE,
        license=LIC_GEMMA, open_weight=True,
    ),
    "gemma-3-4b-it": _entry(
        "gemma-3-4b-it", "google", "google/gemma-3-4b-it",
        family="gemma", size_tier=SIZE_TINY, params_total="4B",
        params_active="4B", architecture=ARCH_DENSE,
        license=LIC_GEMMA, open_weight=True,
    ),
    # ============================================================
    # Microsoft Phi — open-weight MIT
    # ============================================================
    "phi-4": _entry(
        "phi-4", "microsoft", "microsoft/phi-4",
        family="phi", size_tier=SIZE_SMALL, params_total="14B",
        params_active="14B", architecture=ARCH_DENSE,
        license=LIC_MIT, open_weight=True,
    ),
    # ============================================================
    # Allen AI OLMO — open-weight Apache 2.0 (fully open ecosystem)
    # ============================================================
    "olmo-3-1-32b": _entry(
        "olmo-3-1-32b", "allenai", "allenai/olmo-3.1-32b-instruct",
        family="olmo", size_tier=SIZE_MID, params_total="32B",
        params_active="32B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
        notes="Fully open: weights + data + training code.",
    ),
    # ============================================================
    # IBM Granite — open-weight Apache 2.0
    # ============================================================
    "granite-4-1-8b": _entry(
        "granite-4-1-8b", "ibm-granite", "ibm-granite/granite-4.1-8b",
        family="granite", size_tier=SIZE_SMALL, params_total="8B",
        params_active="8B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    "granite-4-0-h-micro": _entry(
        "granite-4-0-h-micro", "ibm-granite", "ibm-granite/granite-4.0-h-micro",
        family="granite", size_tier=SIZE_TINY, params_total="3B",
        params_active="3B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True,
    ),
    # ============================================================
    # Nvidia Nemotron — Nvidia Open Model License
    # ============================================================
    "nemotron-3-super-120b": _entry(
        "nemotron-3-super-120b", "nvidia", "nvidia/nemotron-3-super-120b-a12b",
        extra_body=_REASONING_OFF,
        family="nemotron", size_tier=SIZE_LARGE, params_total="120B",
        params_active="12B", architecture=ARCH_MOE,
        license=LIC_NVIDIA_OPEN, open_weight=True,
    ),
    "nemotron-super-49b": _entry(
        "nemotron-super-49b", "nvidia", "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        extra_body=_REASONING_OFF,
        family="nemotron", size_tier=SIZE_MID, params_total="49B",
        params_active="49B", architecture=ARCH_DENSE,
        license=LIC_NVIDIA_OPEN, open_weight=True,
    ),
    "nemotron-llama-3-1-70b": _entry(
        "nemotron-llama-3-1-70b", "nvidia", "nvidia/llama-3.1-nemotron-70b-instruct",
        family="nemotron", size_tier=SIZE_LARGE, params_total="70B",
        params_active="70B", architecture=ARCH_DENSE,
        license=LIC_NVIDIA_OPEN, open_weight=True,
    ),
    "nemotron-3-nano-30b": _entry(
        "nemotron-3-nano-30b", "nvidia", "nvidia/nemotron-3-nano-30b-a3b",
        extra_body=_REASONING_OFF,
        family="nemotron", size_tier=SIZE_MID, params_total="30B",
        params_active="3B", architecture=ARCH_MOE,
        license=LIC_NVIDIA_OPEN, open_weight=True,
    ),
    "nemotron-nano-9b": _entry(
        "nemotron-nano-9b", "nvidia", "nvidia/nemotron-nano-9b-v2",
        extra_body=_REASONING_OFF,
        family="nemotron", size_tier=SIZE_SMALL, params_total="9B",
        params_active="9B", architecture=ARCH_DENSE,
        license=LIC_NVIDIA_OPEN, open_weight=True,
    ),
    "llama-nemotron-embed-vl-1b-v2-free": _entry(
        "llama-nemotron-embed-vl-1b-v2-free",
        "nvidia",
        "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        family="nemotron", size_tier=SIZE_TINY, params_total="1B",
        params_active="1B", architecture=ARCH_DENSE,
        license=LIC_NVIDIA_OPEN, open_weight=True, concurrency=1,
        notes="OpenRouter free-tier VL embedding model; may not support chat completions.",
    ),
    # ============================================================
    # Sub-7B candidates — explicitly sized to test the cost/latency floor.
    # Reasoning toggle omitted on all (none of these have native reasoning).
    # ============================================================
    "llama-3-2-1b": _entry(
        "llama-3-2-1b", "meta-llama", "meta-llama/llama-3.2-1b-instruct",
        family="llama", size_tier=SIZE_TINY, params_total="1B",
        params_active="1B", architecture=ARCH_DENSE,
        license=LIC_LLAMA32, open_weight=True,
        notes="Smallest Llama 3.2; 60K context.",
    ),
    "lfm-2-5-1-2b": _entry(
        "lfm-2-5-1-2b", "liquid", "liquid/lfm-2.5-1.2b-instruct",
        family="lfm", size_tier=SIZE_TINY, params_total="1.2B",
        params_active="1.2B", architecture=ARCH_DENSE,
        license=LIC_LFM, open_weight=True,
        notes="Liquid Foundation Model 2.5 — non-transformer architecture.",
    ),
    "gemma-3n-e4b-it": _entry(
        "gemma-3n-e4b-it", "google", "google/gemma-3n-e4b-it",
        family="gemma", size_tier=SIZE_TINY, params_total="4B",
        params_active="4B", architecture=ARCH_DENSE,
        license=LIC_GEMMA, open_weight=True,
        notes="Gemma 3n edge-optimized variant.",
    ),
    "qwen-2-5-7b": _entry(
        "qwen-2-5-7b", "qwen", "qwen/qwen-2.5-7b-instruct",
        family="qwen", size_tier=SIZE_SMALL, params_total="7B",
        params_active="7B", architecture=ARCH_DENSE,
        license=LIC_QWEN, open_weight=True,
        notes="Older Qwen 2.5 generation; smallest Qwen text model on OR.",
    ),
    "command-r7b": _entry(
        "command-r7b", "cohere", "cohere/command-r7b-12-2024",
        family="command-r", size_tier=SIZE_SMALL, params_total="7B",
        params_active="7B", architecture=ARCH_DENSE,
        license=LIC_COHERE_CC_BY_NC, open_weight=True,
        notes="Cohere Command R7B. CC-BY-NC license — research/non-commercial only.",
    ),
    # ============================================================
    # Speed-tier provider-pinned variants (Groq / Cerebras)
    # ============================================================
    "llama-3-3-70b-groq": _entry(
        "llama-3-3-70b-groq", "groq", "meta-llama/llama-3.3-70b-instruct",
        provider_routing=_GROQ,
        family="llama", size_tier=SIZE_LARGE, params_total="70B",
        params_active="70B", architecture=ARCH_DENSE,
        license=LIC_LLAMA33, open_weight=True, pinned_provider="Groq",
    ),
    "llama-4-scout-groq": _entry(
        "llama-4-scout-groq", "groq", "meta-llama/llama-4-scout",
        provider_routing=_GROQ,
        family="llama", size_tier=SIZE_LARGE, params_total="109B",
        params_active="17B", architecture=ARCH_MOE,
        license=LIC_LLAMA4, open_weight=True, pinned_provider="Groq",
    ),
    "qwen3-32b-groq": _entry(
        "qwen3-32b-groq", "groq", "qwen/qwen3-32b",
        extra_body=_REASONING_OFF,
        provider_routing=_GROQ,
        family="qwen", size_tier=SIZE_MID, params_total="32B",
        params_active="32B", architecture=ARCH_DENSE,
        license=LIC_APACHE2, open_weight=True, pinned_provider="Groq",
    ),
    "gpt-oss-120b-groq": _entry(
        "gpt-oss-120b-groq", "groq", "openai/gpt-oss-120b",
        provider_routing=_GROQ,
        family="gpt-oss", size_tier=SIZE_LARGE, params_total="117B",
        params_active="5.1B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True, pinned_provider="Groq",
        notes="Groq endpoint requires reasoning (cannot disable); runs fast anyway.",
    ),
    "gpt-oss-20b-groq": _entry(
        "gpt-oss-20b-groq", "groq", "openai/gpt-oss-20b",
        provider_routing=_GROQ,
        family="gpt-oss", size_tier=SIZE_MID, params_total="21B",
        params_active="3.6B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True, pinned_provider="Groq",
    ),
    "qwen3-235b-cerebras": _entry(
        "qwen3-235b-cerebras", "cerebras", "qwen/qwen3-235b-a22b-2507",
        provider_routing=_CEREBRAS,
        family="qwen", size_tier=SIZE_FRONTIER, params_total="235B",
        params_active="22B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True, pinned_provider="Cerebras",
    ),
    "gpt-oss-120b-cerebras": _entry(
        "gpt-oss-120b-cerebras", "cerebras", "openai/gpt-oss-120b",
        provider_routing=_CEREBRAS,
        family="gpt-oss", size_tier=SIZE_LARGE, params_total="117B",
        params_active="5.1B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True, pinned_provider="Cerebras",
        notes="Reasoning is mandatory on this endpoint (cannot disable).",
    ),
    "gpt-oss-120b-nitro": _entry(
        "gpt-oss-120b-nitro", "openrouter-nitro", "openai/gpt-oss-120b:nitro",
        family="gpt-oss", size_tier=SIZE_LARGE, params_total="117B",
        params_active="5.1B", architecture=ARCH_MOE,
        license=LIC_APACHE2, open_weight=True, pinned_provider="Cerebras",
        notes="OR :nitro routes to fastest provider; currently Cerebras. Reasoning mandatory on this endpoint.",
    ),
}


# ----------------- Helpers -----------------


METADATA_FIELDS = (
    "model_id",
    "provider",
    "route",
    "openrouter_slug",
    "native_model",
    "family",
    "size_tier",
    "params_total",
    "params_active",
    "architecture",
    "license",
    "open_weight",
    "thinking",
    "pinned_provider",
    "max_tokens",
    "temperature",
    "notes",
)


def metadata_row(entry: ModelEntry) -> dict[str, Any]:
    """Project a registry entry into a flat dict suitable for models_used.csv."""
    out: dict[str, Any] = {}
    for k in METADATA_FIELDS:
        v = entry.get(k, "")
        if isinstance(v, bool):
            out[k] = "true" if v else "false"
        else:
            out[k] = v
    return out


def resolve_models(spec: str) -> list[ModelEntry]:
    """Resolve a CLI ``--models`` spec to a list of registry entries.

    ``spec`` is either ``"all"`` or a comma-separated list of ``model_id``s.
    Unknown ids raise ValueError.
    """
    if spec.strip() == "all":
        return list(MODEL_REGISTRY.values())
    ids = [s.strip() for s in spec.split(",") if s.strip()]
    out: list[ModelEntry] = []
    missing: list[str] = []
    for mid in ids:
        if mid not in MODEL_REGISTRY:
            missing.append(mid)
        else:
            out.append(MODEL_REGISTRY[mid])
    if missing:
        raise ValueError(
            f"Unknown model_id(s): {missing}. "
            f"Available: {sorted(MODEL_REGISTRY.keys())}"
        )
    return out
