import re
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator

from app.models.generation import validate_provider_id

_LABEL_MAX = 60
_MODEL_MAX = 200

# Registering a private-network endpoint would let a brand use the server as a
# proxy into whatever it can reach. Blocked outright rather than filtered later.
_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}
_BLOCKED_PREFIXES = ("10.", "192.168.", "169.254.", "172.16.", "172.17.", "172.18.",
                     "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                     "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.",
                     "172.31.")


def _validate_base_url(v: str) -> str:
    v = (v or "").strip().rstrip("/")
    parsed = urlparse(v)
    if parsed.scheme != "https":
        raise ValueError("Base URL must use https — an API key must not travel in clear text")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("Base URL must include a host")
    if host in _BLOCKED_HOSTS or host.startswith(_BLOCKED_PREFIXES):
        raise ValueError("Base URL must be a public address")
    return v


class CustomProviderRequest(BaseModel):
    slug: str
    label: str
    base_url: str
    model: str
    auth_style: str = "bearer"

    @field_validator("slug")
    @classmethod
    def check_slug(cls, v: str) -> str:
        return validate_provider_id(v)

    @field_validator("label")
    @classmethod
    def check_label(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("Label cannot be empty")
        if len(v) > _LABEL_MAX:
            raise ValueError(f"Label must be {_LABEL_MAX} characters or less")
        return v

    @field_validator("base_url")
    @classmethod
    def check_base_url(cls, v: str) -> str:
        return _validate_base_url(v)

    @field_validator("model")
    @classmethod
    def check_model(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("Model cannot be empty")
        if len(v) > _MODEL_MAX:
            raise ValueError(f"Model must be {_MODEL_MAX} characters or less")
        return v

    @field_validator("auth_style")
    @classmethod
    def check_auth_style(cls, v: str) -> str:
        v = (v or "bearer").strip()
        if v not in ("bearer", "x-api-key"):
            raise ValueError("Auth style must be 'bearer' or 'x-api-key'")
        return v


class CustomProviderResponse(BaseModel):
    id: str
    slug: str
    label: str
    base_url: str
    model: str
    auth_style: str
    created_at: datetime


class ProviderInfo(BaseModel):
    """What the UI needs to render a provider choice."""

    id: str
    label: str
    adapter: str
    default_model: str
    models: list[str]
    is_custom: bool
    docs_url: str = ""
    key_hint: str = ""
    base_url: str | None = None
    supports_validation: bool = True
