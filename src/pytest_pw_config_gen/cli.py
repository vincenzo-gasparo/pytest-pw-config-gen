"""CLI entry point for pytest-pw-config-gen."""
from enum import Enum

import typer

from pytest_pw_config_gen.defaults import build_defaults
from pytest_pw_config_gen.renderers import get_renderer
from pytest_pw_config_gen.tui.curses_form import run_interactive
from pytest_pw_config_gen.writer import write_file

app = typer.Typer(help="Generate pytest-playwright configuration files.")


class OutputFormat(str, Enum):
    pytest_ini = "pytest.ini"
    pyproject_toml = "pyproject.toml"
    conftest_py = "conftest.py"


@app.command()
def main(
    quick: bool = typer.Option(False, "--quick", help="Generate with sensible defaults — no prompts"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Run interactive TUI wizard — step-by-step prompts for all options"),
    output: OutputFormat = typer.Option(OutputFormat.pytest_ini, "--output", "-o", help="Output file type to generate"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing file without confirmation"),
) -> None:
    """Generate pytest-playwright configuration files."""
    if quick:
        config = build_defaults()
        renderer = get_renderer(output.value)
        content = renderer.render(config)
        write_file(output.value, content, force=force)
    else:
        # interactive is True OR no flags were given — both run the wizard
        config, file_type, output_path = run_interactive()
        renderer = get_renderer(file_type)
        content = renderer.render(config)
        write_file(file_type, content, force=force, output_path=output_path)
