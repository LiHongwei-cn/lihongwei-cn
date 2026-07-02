"""模型选择器测试"""

from model_picker import (
    get_provider_models, get_model_display_name,
    list_configured_providers, format_status_model,
)


def test_deepseek_has_v4_variants():
    models = get_provider_models("deepseek")
    ids = {m["id"] for m in models}
    assert "deepseek-v4" in ids
    assert "deepseek-v4-pro" in ids
    assert "deepseek-v4-flash" in ids


def test_get_model_display_name():
    name = get_model_display_name("deepseek", "deepseek-v4-pro")
    assert "V4" in name or "Pro" in name


def test_format_status_model():
    s = format_status_model("deepseek", "deepseek-v4")
    assert "▼" in s


def test_list_configured_providers():
    providers = list_configured_providers()
    assert isinstance(providers, list)
