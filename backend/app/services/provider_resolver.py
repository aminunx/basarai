"""Turn a provider identifier into a usable spec, for one brand.

An identifier is either a built-in catalogue id or the slug of a custom
provider that brand registered. Resolution is always brand-scoped: one brand
can never reach another's endpoint, which is the same isolation rule the rest
of the system follows.
"""

import logging

from app.core.supabase import get_service_client
from app.services.providers.registry import (
    BUILTIN_PROVIDERS,
    ProviderSpec,
    get_builtin,
    spec_from_custom_row,
)

logger = logging.getLogger(__name__)


class UnknownProviderError(Exception):
    def __init__(self, provider_id: str):
        super().__init__(f"Unknown provider: {provider_id}")
        self.provider_id = provider_id


def _custom_rows(brand_id: str) -> list[dict]:
    client = get_service_client()
    result = (
        client.table("custom_providers")
        .select("*")
        .eq("brand_id", str(brand_id))
        .order("created_at", desc=True)
        .execute()
    )
    return list(result.data or [])


def resolve_provider(provider_id: str, brand_id: str) -> ProviderSpec:
    """Resolve an identifier, preferring built-ins.

    Built-ins win on a name clash so a custom provider can never shadow — and
    silently redirect — a known one.
    """
    builtin = get_builtin(provider_id)
    if builtin is not None:
        return builtin

    for row in _custom_rows(brand_id):
        if str(row.get("slug")) == provider_id:
            return spec_from_custom_row(row)

    raise UnknownProviderError(provider_id)


def available_providers(brand_id: str) -> list[ProviderSpec]:
    """Every provider this brand may use: the catalogue plus its own."""
    specs = list(BUILTIN_PROVIDERS.values())
    builtin_ids = set(BUILTIN_PROVIDERS)
    for row in _custom_rows(brand_id):
        if str(row.get("slug")) in builtin_ids:
            # Shadowed by a built-in; unreachable, so do not offer it.
            continue
        specs.append(spec_from_custom_row(row))
    return specs


def available_provider_ids(brand_id: str) -> set[str]:
    return {spec.id for spec in available_providers(brand_id)}
