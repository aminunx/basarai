import re
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# Providers are no longer a closed set — a brand may register its own. Only the
# shape is checked here; whether the identifier resolves for *this* brand is a
# per-request question the router answers.
PROVIDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,38}[a-z0-9]$")


def validate_provider_id(v: str) -> str:
    v = (v or "").strip()
    if not PROVIDER_ID_RE.match(v):
        raise ValueError(
            "Provider must be 2-40 characters of lowercase letters, digits, "
            "hyphens or underscores"
        )
    return v


class LogoModeEnum(str, Enum):
    none = "none"
    prompt = "prompt"
    watermark = "watermark"
    both = "both"


class GenerationStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"


class PlatformPresetEnum(str, Enum):
    instagram_post = "instagram_post"
    instagram_story = "instagram_story"
    instagram_reel_cover = "instagram_reel_cover"
    facebook_post = "facebook_post"
    facebook_cover = "facebook_cover"
    facebook_story = "facebook_story"
    twitter_post = "twitter_post"
    twitter_header = "twitter_header"
    linkedin_post = "linkedin_post"
    linkedin_banner = "linkedin_banner"
    tiktok_video_cover = "tiktok_video_cover"
    youtube_thumbnail = "youtube_thumbnail"
    youtube_banner = "youtube_banner"


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=4000)
    provider: str
    platform_preset: PlatformPresetEnum
    logo_mode: LogoModeEnum = LogoModeEnum.none

    @field_validator("provider")
    @classmethod
    def check_provider(cls, v: str) -> str:
        return validate_provider_id(v)

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Prompt must be at least 3 characters after trimming")
        if len(v) > 4000:
            raise ValueError("Prompt must be at most 4000 characters after trimming")
        return v


class GenerationResponse(BaseModel):
    id: str
    prompt: str
    provider: str
    model: str
    platform_preset: PlatformPresetEnum
    width: int
    height: int
    logo_mode: LogoModeEnum
    status: GenerationStatusEnum
    image_url: str | None
    download_filename: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class GenerationHistoryStatusEnum(str, Enum):
    succeeded = "succeeded"
    failed = "failed"


class GenerationHistoryItem(BaseModel):
    id: str
    prompt_excerpt: str
    provider: str
    model: str
    platform_preset: PlatformPresetEnum
    width: int
    height: int
    logo_mode: LogoModeEnum
    status: GenerationHistoryStatusEnum
    image_url: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class GenerationHistoryPage(BaseModel):
    items: list[GenerationHistoryItem]
    next_cursor: str | None
    page_size: Literal[24]


class GenerationDetailResponse(BaseModel):
    id: str
    prompt: str
    provider: str
    model: str
    platform_preset: PlatformPresetEnum
    width: int
    height: int
    logo_mode: LogoModeEnum
    status: GenerationHistoryStatusEnum
    provider_request_id: str | None
    image_url: str | None
    download_filename: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
