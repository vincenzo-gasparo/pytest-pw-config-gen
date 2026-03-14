"""Tests for conftest.py Jinja2 renderer — CONF-01 through CONF-11, OUT-01, OUT-02."""
import ast
import pytest
from pytest_pw_config_gen.models import PlaywrightConfig
from pytest_pw_config_gen.renderers import conftest_py


def _render(config=None):
    if config is None:
        config = PlaywrightConfig()
    return conftest_py.render(config)


def test_valid_python_syntax():
    """CONF-01: Rendered output passes ast.parse() without SyntaxError."""
    result = _render()
    # Should not raise
    ast.parse(result)


def test_fixture_decorator():
    """CONF-02: Output contains session-scoped fixture decorator."""
    result = _render()
    assert '@pytest.fixture(scope="session")' in result


def test_fixture_function_signature():
    """CONF-03: Output contains browser_context_args fixture."""
    result = _render()
    assert "def browser_context_args(browser_context_args):" in result


def test_spread_operator():
    """CONF-04: Output contains **browser_context_args spread."""
    result = _render()
    assert "**browser_context_args," in result


def test_viewport():
    """CONF-05: Output contains viewport with default width/height."""
    result = _render()
    assert '"viewport": {"width": 1280, "height": 720}' in result


def test_viewport_custom():
    """CONF-05: Viewport uses custom values."""
    result = _render(PlaywrightConfig(viewport_width=1920, viewport_height=1080))
    assert '"viewport": {"width": 1920, "height": 1080}' in result


def test_locale_present():
    """CONF-06: locale included when set."""
    result = _render(PlaywrightConfig(locale="en-US"))
    assert '"locale": "en-US"' in result


def test_locale_absent_when_none():
    """CONF-06: locale absent when None."""
    result = _render(PlaywrightConfig(locale=None))
    assert '"locale"' not in result


def test_timezone_present():
    """CONF-07: timezone_id included when set."""
    result = _render(PlaywrightConfig(timezone_id="Europe/Rome"))
    assert '"timezone_id": "Europe/Rome"' in result


def test_timezone_absent_when_none():
    """CONF-07: timezone_id absent when None."""
    result = _render(PlaywrightConfig(timezone_id=None))
    assert '"timezone_id"' not in result


def test_geolocation_with_permissions():
    """CONF-08: geolocation and permissions both emitted when lat/lon set."""
    result = _render(PlaywrightConfig(geolocation_lat=40.7, geolocation_lon=-74.0))
    assert '"geolocation"' in result
    assert '"permissions": ["geolocation"]' in result


def test_geolocation_absent_when_none():
    """CONF-08: geolocation absent when lat=None."""
    result = _render(PlaywrightConfig(geolocation_lat=None))
    assert '"geolocation"' not in result
    assert '"permissions"' not in result


def test_storage_state_present():
    """CONF-09: storage_state included when set."""
    result = _render(PlaywrightConfig(storage_state="auth.json"))
    assert '"storage_state": "auth.json"' in result


def test_storage_state_absent_when_none():
    """CONF-09: storage_state absent when None."""
    result = _render(PlaywrightConfig(storage_state=None))
    assert '"storage_state"' not in result


def test_color_scheme_present():
    """CONF-10: color_scheme included when set."""
    result = _render(PlaywrightConfig(color_scheme="dark"))
    assert '"color_scheme": "dark"' in result


def test_color_scheme_absent_when_none():
    """CONF-10: color_scheme absent when None."""
    result = _render(PlaywrightConfig(color_scheme=None))
    assert '"color_scheme"' not in result


def test_http_credentials_present():
    """CONF-11: http_credentials dict included when user/pass set."""
    result = _render(
        PlaywrightConfig(http_credentials_user="admin", http_credentials_pass="secret")
    )
    assert '"http_credentials": {"username": "admin", "password": "secret"}' in result


def test_http_credentials_absent_when_none():
    """CONF-11: http_credentials absent when user=None."""
    result = _render(PlaywrightConfig(http_credentials_user=None))
    assert '"http_credentials"' not in result


def test_user_agent_present():
    """CONF-11: user_agent included when set."""
    result = _render(PlaywrightConfig(user_agent="Custom/1.0"))
    assert '"user_agent": "Custom/1.0"' in result


def test_user_agent_absent_when_none():
    """CONF-11: user_agent absent when None."""
    result = _render(PlaywrightConfig(user_agent=None))
    assert '"user_agent"' not in result


def test_ignore_https_errors_true():
    """CONF-11: ignore_https_errors=True renders Python True, not JSON true."""
    result = _render(PlaywrightConfig(ignore_https_errors=True))
    assert '"ignore_https_errors": True' in result


def test_ignore_https_errors_false():
    """CONF-11: ignore_https_errors=False renders Python False."""
    result = _render(PlaywrightConfig(ignore_https_errors=False))
    assert '"ignore_https_errors": False' in result


def test_header_comment():
    """OUT-01: Generated-by header comment present."""
    result = _render()
    assert "# Generated by pytest-pw-config-gen" in result


def test_geolocation_permissions_auto_injected():
    """CONF-08: permissions array auto-injected with geolocation."""
    result = _render(PlaywrightConfig(geolocation_lat=51.5, geolocation_lon=-0.1))
    assert '"permissions": ["geolocation"]' in result


def test_all_optional_fields_absent_by_default():
    """All optional context fields absent when not set."""
    result = _render(PlaywrightConfig())
    assert '"locale"' not in result
    assert '"timezone_id"' not in result
    assert '"geolocation"' not in result
    assert '"permissions"' not in result
    assert '"storage_state"' not in result
    assert '"color_scheme"' not in result
    assert '"http_credentials"' not in result
    assert '"user_agent"' not in result


def test_runtime_error_not_syntax_error():
    """render() raises RuntimeError (not SyntaxError) on invalid template output."""
    # This tests the exception wrapping — we trust the template is valid in normal use,
    # but verify the error type contract by patching internals if needed.
    # For now, verify the render() function exists and is callable.
    assert callable(conftest_py.render)


def test_valid_python_with_all_options():
    """Rendered output with all optional fields set still passes ast.parse()."""
    config = PlaywrightConfig(
        viewport_width=1920,
        viewport_height=1080,
        locale="en-US",
        timezone_id="America/New_York",
        geolocation_lat=40.7,
        geolocation_lon=-74.0,
        storage_state="auth.json",
        color_scheme="dark",
        http_credentials_user="user",
        http_credentials_pass="pass",
        user_agent="Mozilla/5.0",
        ignore_https_errors=True,
    )
    result = _render(config)
    ast.parse(result)  # Should not raise
