import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import User, get_current_user
from app.core.supabase import get_service_client
from app.models.custom_provider import (
    CustomProviderRequest,
    CustomProviderResponse,
    ProviderInfo,
)
from app.services.provider_resolver import available_providers
from app.services.providers.registry import BUILTIN_PROVIDERS, ProviderSpec

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brands/{brand_id}/providers", tags=["providers"])


def _error_response(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message, "request_id": str(uuid4())}},
    )


def _get_brand_or_404(brand_id: UUID, user_id: str) -> dict:
    client = get_service_client()
    result = (
        client.table("brands")
        .select("id")
        .eq("id", str(brand_id))
        .eq("owner_user_id", user_id)
        .maybe_single()
        .execute()
    )
    if result is None or result.data is None:
        raise _error_response(404, "BRAND_NOT_FOUND", "Brand not found")
    return result.data


def _to_info(spec: ProviderSpec) -> ProviderInfo:
    return ProviderInfo(
        id=spec.id,
        label=spec.label,
        adapter=spec.adapter,
        default_model=spec.default_model,
        models=list(spec.models) or [spec.default_model],
        is_custom=spec.is_custom,
        docs_url=spec.docs_url,
        key_hint=spec.key_hint,
        base_url=spec.base_url,
        supports_validation=bool(spec.validate_url),
    )


def _to_custom_response(row: dict) -> CustomProviderResponse:
    return CustomProviderResponse(
        id=str(row["id"]),
        slug=row["slug"],
        label=row["label"],
        base_url=row["base_url"],
        model=row["model"],
        auth_style=row["auth_style"],
        created_at=row["created_at"],
    )


@router.get("", response_model=list[ProviderInfo])
async def list_providers(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
) -> list[ProviderInfo]:
    """Every provider this brand may generate with — catalogue plus its own."""
    _get_brand_or_404(brand_id, current_user.id)
    return [_to_info(spec) for spec in available_providers(str(brand_id))]


@router.get("/custom", response_model=list[CustomProviderResponse])
async def list_custom_providers(
    brand_id: UUID,
    current_user: User = Depends(get_current_user),
) -> list[CustomProviderResponse]:
    _get_brand_or_404(brand_id, current_user.id)
    client = get_service_client()
    result = (
        client.table("custom_providers")
        .select("*")
        .eq("brand_id", str(brand_id))
        .order("created_at", desc=True)
        .execute()
    )
    return [_to_custom_response(row) for row in (result.data or [])]


@router.post("/custom", response_model=CustomProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_provider(
    brand_id: UUID,
    body: CustomProviderRequest,
    current_user: User = Depends(get_current_user),
) -> CustomProviderResponse:
    _get_brand_or_404(brand_id, current_user.id)

    if body.slug in BUILTIN_PROVIDERS:
        raise _error_response(
            400,
            "SLUG_RESERVED",
            f"'{body.slug}' is a built-in provider. Choose a different identifier.",
        )

    client = get_service_client()
    existing = (
        client.table("custom_providers")
        .select("id")
        .eq("brand_id", str(brand_id))
        .eq("slug", body.slug)
        .execute()
    )
    if existing.data:
        raise _error_response(
            409, "SLUG_TAKEN", f"A provider named '{body.slug}' already exists for this brand."
        )

    result = (
        client.table("custom_providers")
        .insert(
            {
                "brand_id": str(brand_id),
                "slug": body.slug,
                "label": body.label,
                "base_url": body.base_url,
                "model": body.model,
                "auth_style": body.auth_style,
            }
        )
        .execute()
    )
    if not result.data:
        raise _error_response(500, "CREATE_FAILED", "Could not create the provider.")

    logger.info(
        "custom provider created brand_id=%s slug=%s host=%s",
        brand_id, body.slug, body.base_url.split("/")[2] if "//" in body.base_url else "?",
    )
    return _to_custom_response(result.data[0])


@router.delete("/custom/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_provider(
    brand_id: UUID,
    provider_id: UUID,
    current_user: User = Depends(get_current_user),
) -> None:
    _get_brand_or_404(brand_id, current_user.id)
    client = get_service_client()

    found = (
        client.table("custom_providers")
        .select("slug")
        .eq("id", str(provider_id))
        .eq("brand_id", str(brand_id))
        .maybe_single()
        .execute()
    )
    if found is None or found.data is None:
        raise _error_response(404, "PROVIDER_NOT_FOUND", "Provider not found")

    slug = found.data["slug"]

    # Keys outlive their provider otherwise, and would be unusable but still
    # listed. Hard delete, consistent with the rest of the system.
    keys = (
        client.table("provider_keys")
        .select("id, vault_secret_id")
        .eq("brand_id", str(brand_id))
        .eq("provider", slug)
        .execute()
    )
    if keys.data:
        from app.core.vault import delete_secret

        for key in keys.data:
            try:
                delete_secret(key["vault_secret_id"])
            except Exception:
                logger.warning(
                    "Could not delete vault secret for key %s (continuing)", key["id"]
                )
        client.table("provider_keys").delete().eq("brand_id", str(brand_id)).eq(
            "provider", slug
        ).execute()

    client.table("custom_providers").delete().eq("id", str(provider_id)).execute()
