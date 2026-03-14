"""Tests for PlaywrightConfig dataclass field defaults and mutable default safety."""
from pytest_pw_config_gen.models import PlaywrightConfig


def test_default_browsers():
    assert PlaywrightConfig().browsers == ["chromium"]


def test_default_headed():
    assert PlaywrightConfig().headed is False


def test_default_viewport():
    cfg = PlaywrightConfig()
    assert cfg.viewport_width == 1280
    assert cfg.viewport_height == 720


def test_mutable_defaults():
    """Two instances must have independent testpaths, markers, and browsers lists."""
    a = PlaywrightConfig()
    b = PlaywrightConfig()
    a.testpaths.append("e2e")
    a.markers.append("smoke: smoke tests")
    a.browsers.append("firefox")
    assert b.testpaths == ["tests"]
    assert b.markers == []
    assert b.browsers == ["chromium"]


def test_optional_fields_none():
    cfg = PlaywrightConfig()
    assert cfg.base_url is None
    assert cfg.device is None
    assert cfg.locale is None
    assert cfg.timezone_id is None
    assert cfg.geolocation_lat is None
    assert cfg.geolocation_lon is None
    assert cfg.storage_state is None
    assert cfg.color_scheme is None
    assert cfg.http_credentials_user is None
    assert cfg.http_credentials_pass is None
    assert cfg.user_agent is None
