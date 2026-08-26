from datetime import datetime, timezone

from app.services.presets import (
    MODEL_FOR_PROVIDER,
    PLATFORM_PRESETS,
    PRESET_TO_ASPECT_RATIO,
    build_download_filename,
    sanitize_brand_name,
)


def test_presets_has_exactly_13_entries():
    assert len(PLATFORM_PRESETS) == 13


def test_presets_dimensions_within_db_bounds():
    for key, (w, h, _label) in PLATFORM_PRESETS.items():
        assert 256 <= w <= 4096, f"{key} width out of range"
        assert 256 <= h <= 4096, f"{key} height out of range"


def test_every_preset_has_an_aspect_ratio():
    assert set(PLATFORM_PRESETS.keys()) == set(PRESET_TO_ASPECT_RATIO.keys())


def test_aspect_ratios_are_from_supported_set():
    supported = {"1:1", "9:16", "16:9"}
    for ratio in PRESET_TO_ASPECT_RATIO.values():
        assert ratio in supported


def test_model_for_provider():
    # The catalogue is open, so pin only the providers with bespoke adapters.
    # test_provider_registry.py checks the mapping is derived, not duplicated.
    assert MODEL_FOR_PROVIDER["openai"] == "gpt-image-2"
    assert MODEL_FOR_PROVIDER["gemini"] == "gemini-3-pro-image-preview"
    assert MODEL_FOR_PROVIDER["minimax"] == "image-01"


def test_sanitize_brand_name_simple():
    assert sanitize_brand_name("My Brand!") == "my-brand"


def test_sanitize_brand_name_non_ascii_fallback():
    assert sanitize_brand_name("日本語") == "brand"


def test_sanitize_brand_name_only_punctuation_fallback():
    assert sanitize_brand_name("!!!---...") == "brand"


def test_sanitize_brand_name_truncation_at_40():
    raw = "A very long brand name with many many many words to test truncation"
    result = sanitize_brand_name(raw)
    assert len(result) <= 40
    assert not result.endswith("-")


def test_sanitize_brand_name_collapses_hyphens():
    assert sanitize_brand_name("foo  !! bar") == "foo-bar"


def test_build_download_filename_example_from_spec():
    dt = datetime(2026, 4, 11, 14, 30, 52, tzinfo=timezone.utc)
    result = build_download_filename("My Brand!", "instagram_post", dt)
    assert result == "my-brand-instagram_post-20260411-143052.png"


def test_build_download_filename_converts_to_utc():
    from datetime import timedelta, timezone as tz
    eastern = tz(timedelta(hours=-4))
    dt = datetime(2026, 4, 11, 10, 30, 52, tzinfo=eastern)
    result = build_download_filename("My Brand!", "instagram_post", dt)
    assert result == "my-brand-instagram_post-20260411-143052.png"


def test_add_key_accepts_every_builtin_provider():
    """The key form and the generation endpoint must agree on the provider list.

    They were separately hardcoded once, so a provider could be generated with
    but not have its key accepted.
    """
    from app.models.provider_key import AddKeyRequest
    from app.services.providers.registry import BUILTIN_PROVIDER_IDS

    for provider in BUILTIN_PROVIDER_IDS:
        request = AddKeyRequest(provider=provider, key="sk-test-key")
        assert request.provider == provider


def test_add_key_accepts_a_custom_slug():
    """Shape is all the model checks; the router decides if it resolves."""
    from app.models.provider_key import AddKeyRequest

    assert AddKeyRequest(provider="my-gateway", key="sk-x").provider == "my-gateway"


def test_add_key_rejects_a_malformed_provider():
    import pytest as _pytest
    from app.models.provider_key import AddKeyRequest

    for bad in ("Has Spaces", "UPPER", "-leading", "x", "a" * 41, "sym!bol"):
        with _pytest.raises(ValueError):
            AddKeyRequest(provider=bad, key="sk-test-key")
