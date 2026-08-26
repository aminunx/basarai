import pytest

from app.models.custom_provider import CustomProviderRequest
from app.models.generation import validate_provider_id
from app.services.providers.registry import (
    BUILTIN_PROVIDERS,
    BUILTIN_PROVIDER_IDS,
    MODEL_FOR_PROVIDER,
    spec_from_custom_row,
)


# --------------------------------------------------------------------- catalogue


def test_every_builtin_declares_what_the_ui_needs():
    for pid, spec in BUILTIN_PROVIDERS.items():
        assert spec.id == pid, "the dict key must match the spec id"
        assert spec.label
        assert spec.default_model
        assert spec.adapter in ("openai", "gemini", "minimax", "openai_compatible")


def test_openai_compatible_builtins_carry_a_base_url():
    for spec in BUILTIN_PROVIDERS.values():
        if spec.adapter == "openai_compatible":
            assert spec.base_url, f"{spec.id} needs a base_url to be callable"
            assert spec.base_url.startswith("https://")
            assert spec.images_url == f"{spec.base_url}/images/generations"


def test_native_adapters_have_no_images_url():
    for spec in BUILTIN_PROVIDERS.values():
        if spec.adapter != "openai_compatible":
            assert spec.images_url is None


def test_default_model_is_listed_among_models():
    for spec in BUILTIN_PROVIDERS.values():
        if spec.models:
            assert spec.default_model in spec.models


def test_model_for_provider_is_derived_from_the_registry():
    assert MODEL_FOR_PROVIDER == {
        pid: spec.default_model for pid, spec in BUILTIN_PROVIDERS.items()
    }
    assert MODEL_FOR_PROVIDER["openai"] == "gpt-image-2"
    assert MODEL_FOR_PROVIDER["minimax"] == "image-01"


def test_the_three_native_providers_are_still_present():
    for pid in ("openai", "gemini", "minimax"):
        assert pid in BUILTIN_PROVIDER_IDS


# ------------------------------------------------------------------ identifiers


@pytest.mark.parametrize("value", ["openai", "my-gateway", "azure_prod", "a1"])
def test_valid_provider_identifiers(value):
    assert validate_provider_id(value) == value


@pytest.mark.parametrize(
    "value", ["", "x", "UPPER", "has space", "-leading", "trailing-", "sym!bol", "a" * 41]
)
def test_invalid_provider_identifiers(value):
    with pytest.raises(ValueError):
        validate_provider_id(value)


# --------------------------------------------------------------- custom provider


def _valid_custom(**overrides):
    base = {
        "slug": "my-gateway",
        "label": "My Gateway",
        "base_url": "https://gateway.example.com/v1",
        "model": "flux-pro",
    }
    base.update(overrides)
    return base


def test_custom_provider_accepts_a_public_https_endpoint():
    request = CustomProviderRequest(**_valid_custom())
    assert request.base_url == "https://gateway.example.com/v1"
    assert request.auth_style == "bearer"


def test_custom_provider_trailing_slash_is_normalised():
    request = CustomProviderRequest(**_valid_custom(base_url="https://x.example.com/v1/"))
    assert request.base_url == "https://x.example.com/v1"


def test_custom_provider_rejects_plain_http():
    with pytest.raises(ValueError):
        CustomProviderRequest(**_valid_custom(base_url="http://gateway.example.com/v1"))


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost/v1",
        "https://127.0.0.1/v1",
        "https://10.0.0.5/v1",
        "https://192.168.1.10/v1",
        "https://169.254.169.254/latest",
        "https://172.17.0.1/v1",
        "https://metadata.google.internal/v1",
    ],
)
def test_custom_provider_refuses_private_and_metadata_addresses(url):
    """Otherwise a brand could use the server as a proxy into its own network."""
    with pytest.raises(ValueError):
        CustomProviderRequest(**_valid_custom(base_url=url))


def test_custom_provider_rejects_an_unknown_auth_style():
    with pytest.raises(ValueError):
        CustomProviderRequest(**_valid_custom(auth_style="basic"))


def test_custom_row_becomes_an_openai_compatible_spec():
    spec = spec_from_custom_row(
        {
            "slug": "my-gateway",
            "label": "My Gateway",
            "base_url": "https://gateway.example.com/v1/",
            "model": "flux-pro",
            "auth_style": "x-api-key",
        }
    )
    assert spec.adapter == "openai_compatible"
    assert spec.is_custom is True
    assert spec.base_url == "https://gateway.example.com/v1"
    assert spec.images_url == "https://gateway.example.com/v1/images/generations"
    assert spec.validate_url == "https://gateway.example.com/v1/models"
    assert spec.auth_style == "x-api-key"
