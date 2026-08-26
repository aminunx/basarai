"""Adapter for anything speaking OpenAI's /v1/images/generations contract.

This is what makes arbitrary providers possible: Together, xAI, DeepInfra,
Nebius, Azure OpenAI deployments and self-hosted gateways all implement the
same request shape, so one well-tested adapter serves them and every custom
endpoint a user registers.

Two facts about the wider ecosystem shape this code:

* Responses come back as either ``b64_json`` or ``url`` depending on the
  provider, and some ignore ``response_format`` entirely. Both are handled.
* ``size`` is an OpenAI-ism that several compatible providers reject. It is
  sent, but a 400 mentioning ``size`` is retried without it rather than
  surfaced as a failure — otherwise half the catalogue would appear broken.
"""

import base64
import logging

import httpx

from app.services.providers.base import ProviderError, ProviderResult
from app.services.providers.registry import ProviderSpec

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(120.0)


def _size_for(width: int, height: int) -> str:
    if width == height:
        return "1024x1024"
    return "1536x1024" if width > height else "1024x1536"


def _auth_headers(spec: ProviderSpec, api_key: str) -> dict[str, str]:
    if spec.auth_style == "x-api-key":
        return {"x-api-key": api_key}
    return {"Authorization": f"Bearer {api_key}"}


async def _post(
    client: httpx.AsyncClient, url: str, headers: dict[str, str], payload: dict
) -> httpx.Response:
    return await client.post(url, headers=headers, json=payload)


async def openai_compatible_generate(
    *,
    spec: ProviderSpec,
    api_key: str,
    prompt: str,
    width: int,
    height: int,
    model: str,
) -> ProviderResult:
    url = spec.images_url
    if not url:
        raise ProviderError(
            "PROVIDER_CLIENT_ERROR",
            f"{spec.label} has no image endpoint configured.",
        )

    logger.info(
        "openai_compatible_generate: provider=%s model=%s size=%dx%d",
        spec.id, model, width, height,
    )

    headers = _auth_headers(spec, api_key)
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": _size_for(width, height),
        "response_format": "b64_json",
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await _post(client, url, headers, payload)

        # Several compatible providers reject OpenAI-only fields. Drop them and
        # retry once rather than reporting a failure the user cannot act on.
        if response.status_code == 400:
            body = response.text.lower()
            retry = dict(payload)
            if "size" in body:
                retry.pop("size", None)
            if "response_format" in body:
                retry.pop("response_format", None)
            if retry != payload:
                logger.info(
                    "openai_compatible_generate: retrying %s without %s",
                    spec.id,
                    sorted(set(payload) - set(retry)),
                )
                response = await _post(client, url, headers, retry)

        if response.status_code >= 400:
            logger.error(
                "openai_compatible_generate http error: provider=%s status=%s body=%s",
                spec.id, response.status_code, response.text[:1000],
            )
        response.raise_for_status()
        data = response.json()

        image_bytes = await _extract_image(client, data)

    return ProviderResult(
        image_bytes=image_bytes,
        request_id=response.headers.get("x-request-id") or data.get("id"),
    )


async def _extract_image(client: httpx.AsyncClient, data: dict) -> bytes:
    """Pull image bytes out of an OpenAI-shaped response, base64 or URL."""
    try:
        item = data["data"][0]
    except (KeyError, IndexError, TypeError) as e:
        raise ProviderError(
            "EMPTY_RESPONSE",
            "The provider returned no image. Please try again.",
        ) from e

    b64 = item.get("b64_json")
    if b64:
        try:
            return base64.b64decode(b64)
        except (ValueError, TypeError) as e:
            raise ProviderError(
                "EMPTY_RESPONSE",
                "The provider returned an image that could not be decoded.",
            ) from e

    url = item.get("url")
    if url:
        fetched = await client.get(url)
        fetched.raise_for_status()
        return fetched.content

    raise ProviderError(
        "EMPTY_RESPONSE",
        "The provider returned no image. Please try again.",
    )
