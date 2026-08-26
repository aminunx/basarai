"""One entry point for generating an image, whichever provider is chosen.

Callers pass a ProviderSpec and never branch on the provider themselves — that
branching lives here, once. Adding a provider that speaks an existing dialect
needs no change to this file at all.
"""

import asyncio
import logging

from app.services.providers.base import ProviderResult
from app.services.providers.gemini_image import gemini_generate
from app.services.providers.minimax_image import minimax_generate
from app.services.providers.openai_compatible import openai_compatible_generate
from app.services.providers.openai_image import openai_generate
from app.services.providers.registry import ProviderSpec

logger = logging.getLogger(__name__)


async def generate_image(
    *,
    spec: ProviderSpec,
    api_key: str,
    prompt: str,
    width: int,
    height: int,
    aspect_ratio: str,
    model: str,
) -> ProviderResult:
    if spec.adapter == "openai":
        return await openai_generate(
            api_key=api_key, prompt=prompt, width=width, height=height, model=model
        )

    if spec.adapter == "minimax":
        return await minimax_generate(
            api_key=api_key, prompt=prompt, aspect_ratio=aspect_ratio, model=model
        )

    if spec.adapter == "openai_compatible":
        return await openai_compatible_generate(
            spec=spec, api_key=api_key, prompt=prompt,
            width=width, height=height, model=model,
        )

    # Gemini's SDK is synchronous; keep it off the event loop.
    return await asyncio.to_thread(
        gemini_generate,
        api_key=api_key, prompt=prompt, aspect_ratio=aspect_ratio, model=model,
    )
