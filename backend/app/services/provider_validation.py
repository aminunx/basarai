"""Check that a provider key works, without spending generation quota.

Every provider in the catalogue declares a cheap ``validate_url`` — almost
always a models listing — which answers 200 for a good key and 401 for a bad
one. That is enough for every case here, so validation is one generic function
rather than one per provider; only Gemini needs its own, because it puts the
key in a header of its own and reports failure as 400/403.
"""

import logging

import httpx

from app.services.providers.registry import ProviderSpec

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


def _auth_headers(spec: ProviderSpec, api_key: str) -> dict[str, str]:
    if spec.adapter == "gemini":
        return {"x-goog-api-key": api_key}
    if spec.auth_style == "x-api-key":
        return {"x-api-key": api_key}
    return {"Authorization": f"Bearer {api_key}"}


def _message_from(resp: httpx.Response) -> str:
    """Pull a human-readable reason out of whatever error shape came back."""
    try:
        data = resp.json()
    except ValueError:
        return "Invalid API key"
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            msg = error.get("message")
            if msg:
                return str(msg)
        if isinstance(error, str) and error:
            return error
        for key in ("detail", "message"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
    return "Invalid API key"


async def validate_key_for_spec(
    spec: ProviderSpec, api_key: str
) -> tuple[bool | None, str | None]:
    """Return (valid, error). ``None`` for valid means the check was inconclusive."""
    if not spec.validate_url:
        # A custom endpoint that exposes no listing cannot be checked cheaply.
        # Report "unknown" rather than guessing — a wrong "invalid" would send
        # the user hunting for a problem with a key that is fine.
        return (None, "This provider does not support key validation")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(
                spec.validate_url, headers=_auth_headers(spec, api_key)
            )
    except httpx.TimeoutException:
        return (None, "Provider API timed out")
    except httpx.HTTPError:
        logger.exception("Key validation request failed for %s", spec.id)
        return (None, "Provider API request failed")

    if resp.status_code == 200:
        return (True, None)
    if resp.status_code in (400, 401, 403):
        return (False, _message_from(resp))
    if resp.status_code == 404:
        # Common for a mistyped custom base_url.
        return (None, "Provider endpoint not found — check the base URL")
    return (False, f"Unexpected status code: {resp.status_code}")


# Kept for callers that only have an identifier and no spec.
async def validate_provider_key(provider: str, api_key: str) -> tuple[bool | None, str | None]:
    from app.services.providers.registry import get_builtin

    spec = get_builtin(provider)
    if spec is None:
        return (False, f"Unsupported provider: {provider}")
    return await validate_key_for_spec(spec, api_key)
