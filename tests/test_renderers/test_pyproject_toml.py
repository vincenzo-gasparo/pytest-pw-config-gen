"""Tests for pyproject.toml renderer — TOML-01 through TOML-03, OUT-01, OUT-02."""
import tomlkit
from pytest_pw_config_gen.models import PlaywrightConfig
from pytest_pw_config_gen.renderers import pyproject_toml


def test_section():
    """TOML-01: Output contains [tool.pytest.ini_options]."""
    result = pyproject_toml.render(PlaywrightConfig())
    assert "[tool.pytest.ini_options]" in result


def test_toml_validity():
    """TOML-01: Output parses without error via tomlkit.loads()."""
    result = pyproject_toml.render(PlaywrightConfig())
    parsed = tomlkit.loads(result)
    assert parsed is not None


def test_addopts_array_format():
    """TOML-02: addopts is a TOML array of strings, not a single string."""
    result = pyproject_toml.render(PlaywrightConfig())
    parsed = tomlkit.loads(result)
    addopts = parsed["tool"]["pytest"]["ini_options"]["addopts"]
    assert isinstance(addopts, list), "addopts should be a list"
    assert all(isinstance(item, str) for item in addopts), "all addopts items should be strings"


def test_addopts_contains_browser():
    """TOML-02: addopts array contains --browser and chromium as separate elements."""
    result = pyproject_toml.render(PlaywrightConfig())
    parsed = tomlkit.loads(result)
    addopts = parsed["tool"]["pytest"]["ini_options"]["addopts"]
    assert "--browser" in addopts
    assert "chromium" in addopts


def test_multiple_browsers():
    """TOML-02: multiple --browser pairs emitted when more than one browser selected."""
    result = pyproject_toml.render(PlaywrightConfig(browsers=["chromium", "firefox"]))
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert addopts.count("--browser") == 2
    assert "chromium" in addopts
    assert "firefox" in addopts


def test_addopts_contains_media_flags():
    """TOML-02: addopts contains tracing, video, screenshot flags."""
    result = pyproject_toml.render(PlaywrightConfig())
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "--tracing" in addopts
    assert "off" in addopts
    assert "--video" in addopts
    assert "--screenshot" in addopts


def test_device_two_elements():
    """TOML-03: device stored as two separate array elements --device and value."""
    result = pyproject_toml.render(PlaywrightConfig(device="iPhone 13"))
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "--device" in addopts
    assert "iPhone 13" in addopts


def test_device_absent_when_none():
    """TOML-03: --device not in addopts when device=None."""
    result = pyproject_toml.render(PlaywrightConfig())
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "--device" not in addopts


def test_field_parity_headed():
    """TOML-02: headed=True adds --headed to addopts."""
    result = pyproject_toml.render(PlaywrightConfig(headed=True))
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "--headed" in addopts


def test_field_parity_base_url():
    """TOML-02: base_url adds --base-url to addopts."""
    result = pyproject_toml.render(PlaywrightConfig(base_url="https://example.com"))
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "--base-url" in addopts
    assert "https://example.com" in addopts


def test_field_parity_slowmo():
    """TOML-02: slowmo > 0 adds --slowmo to addopts."""
    result = pyproject_toml.render(PlaywrightConfig(slowmo=100))
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "--slowmo" in addopts
    assert "100" in addopts


def test_field_parity_reruns():
    """TOML-02: reruns > 0 adds --reruns to addopts."""
    result = pyproject_toml.render(PlaywrightConfig(reruns=3))
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "--reruns" in addopts
    assert "3" in addopts


def test_field_parity_workers():
    """TOML-02: workers not None adds -n to addopts."""
    result = pyproject_toml.render(PlaywrightConfig(workers=4))
    parsed = tomlkit.loads(result)
    addopts = list(parsed["tool"]["pytest"]["ini_options"]["addopts"])
    assert "-n" in addopts
    assert "4" in addopts


def test_timeout_as_ini_option():
    """TOML-02: timeout is a top-level ini option, not in addopts."""
    result = pyproject_toml.render(PlaywrightConfig(timeout=30))
    parsed = tomlkit.loads(result)
    ini_opts = parsed["tool"]["pytest"]["ini_options"]
    assert "timeout" in ini_opts
    assert ini_opts["timeout"] == 30


def test_testpaths_as_array():
    """TOML-02: testpaths is a TOML array."""
    result = pyproject_toml.render(PlaywrightConfig())
    parsed = tomlkit.loads(result)
    ini_opts = parsed["tool"]["pytest"]["ini_options"]
    assert "testpaths" in ini_opts
    assert isinstance(ini_opts["testpaths"], list)


def test_markers_as_toml_array():
    """TOML-02: markers is a TOML array when non-empty."""
    result = pyproject_toml.render(PlaywrightConfig(markers=["slow: mark slow tests"]))
    parsed = tomlkit.loads(result)
    ini_opts = parsed["tool"]["pytest"]["ini_options"]
    assert "markers" in ini_opts
    assert isinstance(ini_opts["markers"], list)
    assert "slow: mark slow tests" in ini_opts["markers"]


def test_markers_absent_when_empty():
    """TOML-02: markers not in output when empty."""
    result = pyproject_toml.render(PlaywrightConfig())
    parsed = tomlkit.loads(result)
    ini_opts = parsed["tool"]["pytest"]["ini_options"]
    assert "markers" not in ini_opts


def test_header_comment():
    """OUT-01: Generated-by header comment present in raw string."""
    result = pyproject_toml.render(PlaywrightConfig())
    assert "# Generated by pytest-pw-config-gen" in result
