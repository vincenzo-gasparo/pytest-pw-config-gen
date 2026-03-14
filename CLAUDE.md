# pytest-pw-config-gen

CLI tool that generates pytest-playwright configuration files (`pytest.ini`, `pyproject.toml`, `conftest.py`) via a quick mode (sensible defaults) or an interactive TUI wizard.

## Project Layout

```
src/pytest_pw_config_gen/
  models.py          # PlaywrightConfig dataclass — single source of truth for all config fields
  cli.py             # Typer entry point (pytest-pw-config-gen command)
  writer.py          # File writing with overwrite confirmation
  defaults.py        # Default values
  tui/
    curses_form.py   # Curses-based full-screen interactive wizard
  renderers/
    pytest_ini.py    # Renders pytest.ini
    pyproject_toml.py # Renders [tool.pytest.ini_options]
    conftest_py.py   # Renders conftest.py (uses Jinja2 template)
  templates/
    conftest_py.j2   # Jinja2 template for conftest.py output
tests/
  test_models.py
  test_cli.py
  test_writer.py
  test_defaults.py
  test_renderers/    # test_pytest_ini.py, test_pyproject_toml.py, test_conftest_py.py
  test_tui/          # test_curses_form.py
```

## Key Design Notes

- `PlaywrightConfig` is the shared contract between all layers — changes to fields must be reflected in renderers, TUI, and tests.
- `browsers` is a `List[str]` (multi-select). Renderers emit one `--browser` flag per entry.
- `conftest_py.py` renderer uses the Jinja2 template (`conftest_py.j2`) rather than programmatic string building.
- The interactive wizard is a **curses-based full-screen form** (`tui/curses_form.py`). Do not replace it with Textual — Textual splits keyboard focus across child widgets making the form unscrollable in Ghostty.
- The wizard prompts for the output file path (with overwrite confirmation) inside curses before returning. `writer.py` accepts an `output_path` kwarg; when provided it skips the typer confirm since the user already confirmed in the TUI.

## Critical Known Issue

**`pyproject.toml` was accidentally overwritten by the tool itself** (the tool generated a `pyproject.toml` into the project root, replacing the package's own `pyproject.toml` with a pytest config). The real `pyproject.toml` must contain the full package metadata and `[project.scripts]` entry point — not just `[tool.pytest.ini_options]`. Always verify `pyproject.toml` contains `[project]` metadata before running builds.

## Commands

```bash
# Run tests
python -m pytest tests/

# Install editable
pip install -e .

# Build distribution
python -m build

# Check dist metadata
twine check dist/*

# Run the CLI
pytest-pw-config-gen           # interactive mode (full-screen curses form)
pytest-pw-config-gen --quick --output pytest.ini
```

## Interactive Wizard Keys

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move between options |
| `Space` / `Enter` | Toggle bool / open submenu / edit value |
| `Ctrl+G` | Generate — prompts for output path then exits |
| `q` / `Esc` | Cancel |

## Dependencies

- `typer` — CLI entry point
- `rich` — terminal display (written output)
- `Jinja2` — conftest.py template rendering
- `tomlkit` — TOML generation for pyproject.toml renderer
- Python 3.9+
