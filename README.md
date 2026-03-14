# pytest-pw-config-gen

Generate pytest-playwright configuration files (pytest.ini, pyproject.toml, conftest.py) via CLI.

## Installation

```bash
pip install pytest-pw-config-gen
```

## Quick Mode

Generate a configuration file immediately with sensible defaults — no prompts required.

```bash
pytest-pw-config-gen --quick --output pytest.ini
pytest-pw-config-gen --quick --output pyproject.toml
pytest-pw-config-gen --quick --output conftest.py
```

Pass `--force` to overwrite an existing file without confirmation:

```bash
pytest-pw-config-gen --quick --output pytest.ini --force
```

## Interactive Mode

The full-screen terminal wizard is the default when no flags are provided. Pass `--interactive` explicitly if needed:

```bash
pytest-pw-config-gen
# or
pytest-pw-config-gen --interactive
```

It opens a keyboard-driven form:

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move between options |
| `Space` / `Enter` | Toggle a boolean / open a selection menu / edit a value |
| `Ctrl+G` | Confirm and proceed to save |
| `q` / `Esc` | Cancel |

After pressing `Ctrl+G` you are prompted for an output path (defaulting to the current directory). If the file already exists you are asked to confirm the overwrite before anything is written.

In CI environments without a TTY the tool prints a clear error message and exits non-zero rather than hanging.

## Supported Options

### pytest.ini / pyproject.toml options

| Option | Description | Default |
|--------|-------------|---------|
| browsers | One or more browsers: `chromium`, `firefox`, `webkit` (multi-select) | `chromium` |
| headed | Run browser in headed mode (visible window) | `false` |
| browser channel | Chromium channel: `chrome`, `chrome-beta`, `chrome-dev`, `msedge` | _(none)_ |
| device preset | Emulate a named device (e.g. `iPhone 13`) | _(none)_ |
| tracing | Playwright tracing mode: `off`, `on`, `retain-on-failure` | `off` |
| video | Video capture mode: `off`, `on`, `retain-on-failure` | `off` |
| screenshot | Screenshot capture mode: `off`, `on`, `only-on-failure` | `off` |
| artifact output dir | Directory where traces, videos, and screenshots are saved | _(none)_ |
| base-url | Base URL for `page.goto()` relative URLs | _(none)_ |
| slow-motion | Delay between Playwright actions in milliseconds | `0` |
| workers | Parallel worker count via `-n` flag (requires pytest-xdist) | _(none)_ |
| retries | Number of test reruns on failure (requires pytest-rerunfailures) | `0` |
| reporter | Test report format: `html`, `junit`, `json` | _(none)_ |
| timeout | Per-test timeout in seconds (requires pytest-timeout) | `30` |
| testpaths | Directories pytest searches for tests | `tests` |
| markers | Custom pytest marker definitions | _(none)_ |

### conftest.py options

| Option | Description | Default |
|--------|-------------|---------|
| viewport | Browser window size as width × height | `1280 × 720` |
| action timeout | Per-action timeout in milliseconds | _(none)_ |
| locale | Browser locale (e.g. `en-US`, `fr-FR`) | _(none)_ |
| timezone_id | IANA timezone for the browser context (e.g. `America/New_York`) | _(none)_ |
| geolocation | Latitude and longitude for the browser context | _(none)_ |
| storage_state | Path to a previously saved browser storage state file | _(none)_ |
| color_scheme | Preferred color scheme: `light`, `dark`, or `no-preference` | _(none)_ |
| accept_downloads | Automatically accept file downloads | `false` |
| permissions | Browser permissions to grant (e.g. `geolocation`, `notifications`) | _(none)_ |
| http_credentials | Username and password for HTTP Basic/Digest authentication | _(none)_ |
| extra_http_headers | Additional HTTP headers sent with every request | _(none)_ |
| user_agent | Custom User-Agent string | _(none)_ |
| ignore_https_errors | Ignore HTTPS certificate errors | `false` |

## Output Files

All generated files include a comment header identifying them as auto-generated and inline comments explaining non-obvious options so you know what to adjust after generation.

### pytest.ini

Sets `[pytest]` addopts flags (browser, tracing, video, etc.) and common ini options (testpaths, timeout, markers).

### pyproject.toml

Sets `[tool.pytest.ini_options]` with the same options — suitable when you prefer a single `pyproject.toml` for all project tooling.

### conftest.py

Creates a `browser_context_args` fixture with Playwright context options (viewport, locale, geolocation, storage state, etc.). Drop this file in your test root alongside the chosen `pytest.ini` or `pyproject.toml`.

## Requirements

- Python 3.9+
- [pytest-playwright](https://playwright.dev/python/docs/test-runners) (installed separately in your test project)

## License

MIT
