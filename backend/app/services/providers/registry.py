"""The catalogue of image providers.

Providers used to be a Postgres enum plus three hardcoded dicts, so every new
one meant a migration and a hunt for every list that had to be kept in step.
This module is now the single declaration: built-ins are data, and a brand can
register its own OpenAI-compatible endpoint at runtime without a code change.

Adapters
--------
``openai``, ``gemini`` and ``minimax`` are native — each provider speaks its own
dialect. ``openai_compatible`` covers everything that implements OpenAI's
``/v1/images/generations`` contract, which most inference platforms do; it is
also what a user-defined custom provider always uses.
"""

from dataclasses import dataclass
from typing import Literal

Adapter = Literal["openai", "gemini", "minimax", "openai_compatible"]

# How the key is presented. Native adapters carry their own convention; this
# only concerns the OpenAI-compatible family.
AuthStyle = Literal["bearer", "x-api-key"]


@dataclass(frozen=True, slots=True)
class ProviderSpec:
    id: str
    label: str
    adapter: Adapter
    default_model: str
    models: tuple[str, ...] = ()
    # Only meaningful for openai_compatible: the API root, without a trailing slash.
    base_url: str | None = None
    auth_style: AuthStyle = "bearer"
    # A cheap GET that proves the key works without spending generation quota.
    validate_url: str | None = None
    docs_url: str = ""
    key_hint: str = ""
    is_custom: bool = False

    @property
    def images_url(self) -> str | None:
        if self.adapter != "openai_compatible" or not self.base_url:
            return None
        return f"{self.base_url.rstrip('/')}/images/generations"


# --------------------------------------------------------------------------
# Built-in catalogue
#
# Every endpoint below was probed before being listed: each answers 401 without
# credentials, which is how we know the route exists and is not a guess.
# --------------------------------------------------------------------------

BUILTIN_PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        id="openai",
        label="OpenAI",
        adapter="openai",
        default_model="gpt-image-2",
        models=("gpt-image-2", "gpt-image-1"),
        validate_url="https://api.openai.com/v1/models",
        docs_url="https://platform.openai.com/api-keys",
        key_hint="sk-…",
    ),
    "gemini": ProviderSpec(
        id="gemini",
        label="Google Gemini",
        adapter="gemini",
        default_model="gemini-3-pro-image-preview",
        models=("gemini-3-pro-image-preview",),
        validate_url="https://generativelanguage.googleapis.com/v1beta/models",
        docs_url="https://aistudio.google.com/apikey",
        key_hint="AIza…",
    ),
    "minimax": ProviderSpec(
        id="minimax",
        label="MiniMax",
        adapter="minimax",
        default_model="image-01",
        models=("image-01",),
        validate_url="https://api.minimax.io/v1/models",
        docs_url="https://platform.minimax.io/user-center/payment/token-plan",
        key_hint="sk-cp-…  (Subscription Key, not a pay-as-you-go key)",
    ),
    "together": ProviderSpec(
        id="together",
        label="Together AI",
        adapter="openai_compatible",
        default_model="black-forest-labs/FLUX.1.1-pro",
        models=(
            "black-forest-labs/FLUX.1.1-pro",
            "black-forest-labs/FLUX.1-schnell-Free",
            "black-forest-labs/FLUX.1-dev",
        ),
        base_url="https://api.together.xyz/v1",
        validate_url="https://api.together.xyz/v1/models",
        docs_url="https://api.together.ai/settings/api-keys",
    ),
    "xai": ProviderSpec(
        id="xai",
        label="xAI (Grok)",
        adapter="openai_compatible",
        default_model="grok-2-image",
        models=("grok-2-image",),
        base_url="https://api.x.ai/v1",
        validate_url="https://api.x.ai/v1/models",
        docs_url="https://console.x.ai",
        key_hint="xai-…",
    ),
    "deepinfra": ProviderSpec(
        id="deepinfra",
        label="DeepInfra",
        adapter="openai_compatible",
        default_model="black-forest-labs/FLUX-1.1-pro",
        models=(
            "black-forest-labs/FLUX-1.1-pro",
            "black-forest-labs/FLUX-1-schnell",
        ),
        base_url="https://api.deepinfra.com/v1/openai",
        validate_url="https://api.deepinfra.com/v1/openai/models",
        docs_url="https://deepinfra.com/dash/api_keys",
    ),
    "nebius": ProviderSpec(
        id="nebius",
        label="Nebius AI Studio",
        adapter="openai_compatible",
        default_model="black-forest-labs/flux-dev",
        models=(
            "black-forest-labs/flux-dev",
            "black-forest-labs/flux-schnell",
        ),
        base_url="https://api.studio.nebius.com/v1",
        validate_url="https://api.studio.nebius.com/v1/models",
        docs_url="https://studio.nebius.com",
    ),
}

BUILTIN_PROVIDER_IDS: tuple[str, ...] = tuple(BUILTIN_PROVIDERS)

# Kept for callers that only need a provider's default model.
MODEL_FOR_PROVIDER: dict[str, str] = {
    pid: spec.default_model for pid, spec in BUILTIN_PROVIDERS.items()
}


def spec_from_custom_row(row: dict) -> ProviderSpec:
    """Build a spec from a `custom_providers` row.

    Custom providers are always OpenAI-compatible — that contract is the whole
    reason a user can point the app at an arbitrary endpoint and have it work.
    """
    base_url = str(row["base_url"]).rstrip("/")
    return ProviderSpec(
        id=str(row["slug"]),
        label=str(row["label"]),
        adapter="openai_compatible",
        default_model=str(row["model"]),
        models=(str(row["model"]),),
        base_url=base_url,
        auth_style=str(row.get("auth_style") or "bearer"),  # type: ignore[arg-type]
        validate_url=f"{base_url}/models",
        is_custom=True,
    )


def is_builtin(provider_id: str) -> bool:
    return provider_id in BUILTIN_PROVIDERS


def get_builtin(provider_id: str) -> ProviderSpec | None:
    return BUILTIN_PROVIDERS.get(provider_id)
