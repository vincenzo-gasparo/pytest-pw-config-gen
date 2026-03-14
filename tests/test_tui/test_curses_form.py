"""Tests for tui/curses_form.py — pure functions and run_interactive TTY guard."""
import pytest
import typer

from pytest_pw_config_gen.defaults import build_defaults
from pytest_pw_config_gen.models import PlaywrightConfig
from pytest_pw_config_gen.tui.curses_form import (
    _build_conftest,
    _build_ini,
    _conftest_defaults,
    _ini_defaults,
    _navigable_indices,
    _parse_headers,
    _visible,
    run_interactive,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ini_vals(**overrides):
    vals = _ini_defaults(build_defaults())
    vals.update(overrides)
    return vals


def _conftest_vals(**overrides):
    vals = _conftest_defaults(build_defaults())
    vals.update(overrides)
    return vals


# ── run_interactive TTY guard ──────────────────────────────────────────────────

class TestTTYGuard:
    def test_non_tty_raises_exit(self, mocker):
        mocker.patch("sys.stdin.isatty", return_value=False)
        with pytest.raises(typer.Exit):
            run_interactive()

    def test_non_tty_does_not_call_curses(self, mocker):
        mocker.patch("sys.stdin.isatty", return_value=False)
        mock_wrapper = mocker.patch("curses.wrapper")
        try:
            run_interactive()
        except typer.Exit:
            pass
        mock_wrapper.assert_not_called()


# ── _parse_headers ─────────────────────────────────────────────────────────────

class TestParseHeaders:
    def test_single_header(self):
        assert _parse_headers("X-Foo: bar") == {"X-Foo": "bar"}

    def test_multiple_headers(self):
        assert _parse_headers("X-Foo: bar, X-Baz: qux") == {"X-Foo": "bar", "X-Baz": "qux"}

    def test_empty_string(self):
        assert _parse_headers("") == {}

    def test_no_colon_ignored(self):
        assert _parse_headers("invalid") == {}


# ── _visible ──────────────────────────────────────────────────────────────────

class TestVisible:
    _ROWS = [
        ("sep",   None,        "Section", None, None),
        ("bool",  "flag",      "A flag",  None, None),
        ("input", "gated_row", "Gated",   None, "flag"),
    ]

    def test_ungated_rows_always_shown(self):
        rows = _visible(self._ROWS, {"flag": False})
        assert len(rows) == 2  # sep + bool; gated input hidden

    def test_gated_row_shown_when_gate_true(self):
        rows = _visible(self._ROWS, {"flag": True})
        assert len(rows) == 3

    def test_gated_row_hidden_when_gate_false(self):
        rows = _visible(self._ROWS, {"flag": False})
        assert all(r[1] != "gated_row" for r in rows)


# ── _navigable_indices ────────────────────────────────────────────────────────

class TestNavigableIndices:
    def test_excludes_separators(self):
        rows = [
            ("sep",   None, "S", None, None),
            ("bool",  "b",  "B", None, None),
            ("sep",   None, "S", None, None),
            ("input", "i",  "I", None, None),
        ]
        assert _navigable_indices(rows) == [1, 3]

    def test_all_navigable_when_no_seps(self):
        rows = [
            ("bool",  "a", "A", None, None),
            ("input", "b", "B", None, None),
        ]
        assert _navigable_indices(rows) == [0, 1]


# ── _ini_defaults ─────────────────────────────────────────────────────────────

class TestIniDefaults:
    def test_returns_dict_with_expected_keys(self):
        vals = _ini_defaults(build_defaults())
        for key in ("browsers", "headed", "tracing", "video", "screenshot",
                    "timeout", "testpaths", "reruns", "slowmo"):
            assert key in vals

    def test_browsers_matches_defaults(self):
        d = build_defaults()
        assert _ini_defaults(d)["browsers"] == list(d.browsers)

    def test_testpaths_is_space_joined_string(self):
        vals = _ini_defaults(build_defaults())
        assert isinstance(vals["testpaths"], str)

    def test_timeout_is_string(self):
        vals = _ini_defaults(build_defaults())
        assert isinstance(vals["timeout"], str)


# ── _conftest_defaults ────────────────────────────────────────────────────────

class TestConftestDefaults:
    def test_returns_dict_with_expected_keys(self):
        vals = _conftest_defaults(build_defaults())
        for key in ("viewport_width", "viewport_height", "set_locale",
                    "set_geo", "color_scheme", "ignore_https"):
            assert key in vals

    def test_viewport_values_are_strings(self):
        vals = _conftest_defaults(build_defaults())
        assert isinstance(vals["viewport_width"], str)
        assert isinstance(vals["viewport_height"], str)

    def test_color_scheme_defaults_to_no_preference(self):
        # build_defaults() has color_scheme=None → should map to "no-preference"
        vals = _conftest_defaults(build_defaults())
        assert vals["color_scheme"] == "no-preference"


# ── _build_ini ────────────────────────────────────────────────────────────────

class TestBuildIni:
    def test_returns_playwright_config(self):
        assert isinstance(_build_ini(_ini_vals(), build_defaults()), PlaywrightConfig)

    def test_browsers_collected(self):
        config = _build_ini(_ini_vals(browsers=["firefox"]), build_defaults())
        assert config.browsers == ["firefox"]

    def test_multiple_browsers(self):
        config = _build_ini(_ini_vals(browsers=["chromium", "firefox", "webkit"]), build_defaults())
        assert config.browsers == ["chromium", "firefox", "webkit"]

    def test_headed_true(self):
        config = _build_ini(_ini_vals(headed=True), build_defaults())
        assert config.headed is True

    def test_browser_channel_none_when_not_set(self):
        config = _build_ini(_ini_vals(set_channel=False), build_defaults())
        assert config.browser_channel is None

    def test_browser_channel_set(self):
        config = _build_ini(_ini_vals(set_channel=True, browser_channel="chrome"), build_defaults())
        assert config.browser_channel == "chrome"

    def test_workers_set(self):
        config = _build_ini(_ini_vals(set_workers=True, workers="4"), build_defaults())
        assert config.workers == 4

    def test_workers_none_when_not_set(self):
        config = _build_ini(_ini_vals(set_workers=False), build_defaults())
        assert config.workers is None

    def test_timeout_parsed(self):
        config = _build_ini(_ini_vals(timeout="60"), build_defaults())
        assert config.timeout == 60

    def test_testpaths_split_on_spaces(self):
        config = _build_ini(_ini_vals(testpaths="tests e2e"), build_defaults())
        assert config.testpaths == ["tests", "e2e"]

    def test_markers_collected_when_set(self):
        config = _build_ini(_ini_vals(set_markers=True, markers="smoke, regression"), build_defaults())
        assert "smoke" in config.markers
        assert "regression" in config.markers

    def test_markers_empty_when_not_set(self):
        d = build_defaults()
        config = _build_ini(_ini_vals(set_markers=False), d)
        assert config.markers == d.markers

    def test_tracing_value_preserved(self):
        config = _build_ini(_ini_vals(tracing="retain-on-failure"), build_defaults())
        assert config.tracing == "retain-on-failure"


# ── _build_conftest ───────────────────────────────────────────────────────────

class TestBuildConftest:
    def test_returns_playwright_config(self):
        assert isinstance(_build_conftest(_conftest_vals(), build_defaults()), PlaywrightConfig)

    def test_viewport_parsed(self):
        config = _build_conftest(_conftest_vals(viewport_width="1920", viewport_height="1080"), build_defaults())
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080

    def test_locale_set(self):
        config = _build_conftest(_conftest_vals(set_locale=True, locale="fr-FR"), build_defaults())
        assert config.locale == "fr-FR"

    def test_locale_none_when_not_set(self):
        config = _build_conftest(_conftest_vals(set_locale=False), build_defaults())
        assert config.locale is None

    def test_geolocation_set(self):
        config = _build_conftest(_conftest_vals(set_geo=True, geo_lat="41.9", geo_lon="12.5"), build_defaults())
        assert config.geolocation_lat == 41.9
        assert config.geolocation_lon == 12.5

    def test_geolocation_none_when_not_set(self):
        config = _build_conftest(_conftest_vals(set_geo=False), build_defaults())
        assert config.geolocation_lat is None
        assert config.geolocation_lon is None

    def test_color_scheme_not_set_returns_none(self):
        config = _build_conftest(_conftest_vals(color_scheme="(not set)"), build_defaults())
        assert config.color_scheme is None

    def test_color_scheme_dark(self):
        config = _build_conftest(_conftest_vals(color_scheme="dark"), build_defaults())
        assert config.color_scheme == "dark"

    def test_http_credentials_set(self):
        config = _build_conftest(
            _conftest_vals(set_http_creds=True, http_user="admin", http_pass="secret"),
            build_defaults(),
        )
        assert config.http_credentials_user == "admin"
        assert config.http_credentials_pass == "secret"

    def test_http_credentials_none_when_not_set(self):
        config = _build_conftest(_conftest_vals(set_http_creds=False), build_defaults())
        assert config.http_credentials_user is None

    def test_ignore_https_errors(self):
        config = _build_conftest(_conftest_vals(ignore_https=True), build_defaults())
        assert config.ignore_https_errors is True

    def test_extra_headers_parsed(self):
        config = _build_conftest(
            _conftest_vals(set_extra_headers=True, extra_headers_str="X-Foo: bar, X-Baz: qux"),
            build_defaults(),
        )
        assert config.extra_http_headers == {"X-Foo": "bar", "X-Baz": "qux"}

    def test_extra_headers_empty_when_not_set(self):
        config = _build_conftest(_conftest_vals(set_extra_headers=False), build_defaults())
        assert config.extra_http_headers == {}

    def test_action_timeout_set(self):
        config = _build_conftest(_conftest_vals(set_action_timeout=True, action_timeout="3000"), build_defaults())
        assert config.action_timeout == 3000

    def test_action_timeout_none_when_not_set(self):
        config = _build_conftest(_conftest_vals(set_action_timeout=False), build_defaults())
        assert config.action_timeout is None

    def test_user_agent_set(self):
        config = _build_conftest(_conftest_vals(set_ua=True, user_agent="MyBot/1.0"), build_defaults())
        assert config.user_agent == "MyBot/1.0"

    def test_user_agent_none_when_not_set(self):
        config = _build_conftest(_conftest_vals(set_ua=False), build_defaults())
        assert config.user_agent is None
