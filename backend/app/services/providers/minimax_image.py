import base64
import logging

import httpx

from app.services.providers.base import ProviderError, ProviderResult

logger = logging.getLogger(__name__)

MINIMAX_IMAGES_URL = "https://api.minimax.io/v1/image_generation"

# MiniMax accepts a fixed set of aspect ratio strings. The presets map cleanly
# onto these, so the ratio is passed straight through rather than derived from
# pixel dimensions — the exact size is applied afterwards by resize_to_preset.
SUPPORTED_ASPECT_RATIOS = frozenset(
    {"1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"}
)

# MiniMax answers 200 OK for logical failures too, carrying the real outcome in
# base_resp.status_code. These are the ones worth naming for the user; anything
# else falls through to a generic provider error.
_STATUS_TO_ERROR: dict[int, tuple[str, str]] = {
    1004: ("INVALID_KEY", "Your MiniMax key was rejected. Please check your keys."),
    1008: (
        "INVALID_KEY",
        "Your MiniMax account has no balance for this call. Token Plan quota is "
        "billed to the Subscription Key (sk-cp…), not a pay-as-you-go API key.",
    ),
    1002: ("RATE_LIMITED", "MiniMax is currently rate-limiting your account. Please try again in a moment."),
    1026: ("CONTENT_POLICY", "MiniMax refused this prompt due to its content policy. Please try a different description."),
    2013: ("PROVIDER_CLIENT_ERROR", "MiniMax rejected this request. Please try again or adjust your prompt."),
}


async def minimax_generate(
    *,
    api_key: str,
    prompt: str,
    aspect_ratio: str,
    model: str,
) -> ProviderResult:
    logger.info("minimax_generate: model=%s aspect_ratio=%s", model, aspect_ratio)

    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ProviderError(
            "PROVIDER_CLIENT_ERROR",
            f"MiniMax does not support the {aspect_ratio} aspect ratio.",
        )

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        response = await client.post(
            MINIMAX_IMAGES_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "n": 1,
                # base64 avoids a second round trip to the CDN and keeps the
                # image off any third-party URL.
                "response_format": "base64",
            },
        )
        if response.status_code >= 400:
            logger.error(
                "minimax_generate http error: status=%s body=%s",
                response.status_code,
                response.text[:1000],
            )
        response.raise_for_status()
        data = response.json()

    # Transport succeeded; the provider may still have failed.
    base_resp = data.get("base_resp") or {}
    status_code = base_resp.get("status_code")
    if status_code not in (0, None):
        code, message = _STATUS_TO_ERROR.get(
            status_code,
            ("PROVIDER_CLIENT_ERROR", "MiniMax rejected this request. Please try again."),
        )
        logger.error(
            "minimax_generate provider error: status_code=%s status_msg=%s",
            status_code,
            base_resp.get("status_msg"),
        )
        raise ProviderError(code, message)

    try:
        b64 = data["data"]["image_base64"][0]
    except (KeyError, IndexError, TypeError) as e:
        raise ProviderError(
            "EMPTY_RESPONSE",
            "The provider returned no image. Please try again.",
        ) from e

    return ProviderResult(
        image_bytes=base64.b64decode(b64),
        request_id=data.get("id"),
    )
