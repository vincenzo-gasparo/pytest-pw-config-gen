"""Tests for build_defaults() function."""
import pytest
from pytest_pw_config_gen.models import PlaywrightConfig
from pytest_pw_config_gen.defaults import build_defaults


def test_build_defaults_returns_config():
    assert isinstance(build_defaults(), PlaywrightConfig)


def test_build_defaults_chromium():
    assert build_defaults().browsers == ["chromium"]


def test_build_defaults_headless():
    assert build_defaults().headed is False


def test_get_renderer_unknown_raises():
    from pytest_pw_config_gen.renderers import get_renderer
    with pytest.raises(ValueError, match="unknown_format"):
        get_renderer("unknown_format")
