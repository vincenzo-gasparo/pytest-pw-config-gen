"""Tests for cli.py — typer app with --quick, --output, --force, --interactive flags."""
import os

import pytest
from typer.testing import CliRunner

from pytest_pw_config_gen.cli import app

runner = CliRunner()


class TestHelp:
    def test_help_exits_zero(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_help_contains_quick(self):
        result = runner.invoke(app, ["--help"])
        assert "--quick" in result.output

    def test_help_contains_output(self):
        result = runner.invoke(app, ["--help"])
        assert "--output" in result.output

    def test_help_contains_force(self):
        result = runner.invoke(app, ["--help"])
        assert "--force" in result.output

    def test_help_content_describes_quick(self):
        result = runner.invoke(app, ["--help"])
        # Should mention sensible defaults or no prompts
        assert "defaults" in result.output.lower() or "prompts" in result.output.lower()


class TestNoFlags:
    def test_no_flags_exits_one_in_non_tty(self, mocker):
        """No-flags defaults to interactive; non-TTY should exit 1 with TTY error."""
        mocker.patch("sys.stdin.isatty", return_value=False)
        result = runner.invoke(app, [])
        assert result.exit_code == 1

    def test_no_flags_message(self, mocker):
        """No-flags in non-TTY shows a TTY / terminal error message."""
        mocker.patch("sys.stdin.isatty", return_value=False)
        result = runner.invoke(app, [])
        assert "terminal" in result.output.lower() or "tty" in result.output.lower()


class TestQuickMode:
    def test_quick_pytest_ini_exits_zero(self, tmp_cwd):
        result = runner.invoke(app, ["--quick", "--output", "pytest.ini"])
        assert result.exit_code == 0

    def test_quick_pyproject_toml_exits_zero(self, tmp_cwd):
        result = runner.invoke(app, ["--quick", "--output", "pyproject.toml"])
        assert result.exit_code == 0

    def test_quick_conftest_py_exits_zero(self, tmp_cwd):
        result = runner.invoke(app, ["--quick", "--output", "conftest.py"])
        assert result.exit_code == 0

    def test_quick_writes_pytest_ini(self, tmp_cwd):
        runner.invoke(app, ["--quick", "--output", "pytest.ini"])
        assert (tmp_cwd / "pytest.ini").exists()

    def test_quick_writes_pyproject_toml(self, tmp_cwd):
        runner.invoke(app, ["--quick", "--output", "pyproject.toml"])
        assert (tmp_cwd / "pyproject.toml").exists()

    def test_quick_writes_conftest_py(self, tmp_cwd):
        runner.invoke(app, ["--quick", "--output", "conftest.py"])
        assert (tmp_cwd / "conftest.py").exists()

    def test_quick_default_output_format(self, tmp_cwd):
        """Default output format is pytest.ini when --output not given."""
        result = runner.invoke(app, ["--quick"])
        assert result.exit_code == 0
        assert (tmp_cwd / "pytest.ini").exists()


class TestOutputFormatValidation:
    def test_invalid_output_exits_nonzero(self, tmp_cwd):
        result = runner.invoke(app, ["--quick", "--output", "invalid.txt"])
        assert result.exit_code != 0

    def test_all_valid_formats_exit_zero(self, tmp_cwd):
        for fmt in ("pytest.ini", "pyproject.toml", "conftest.py"):
            os.chdir(tmp_cwd)
            result = runner.invoke(app, ["--quick", "--output", fmt])
            assert result.exit_code == 0, f"Format {fmt} failed: {result.output}"


class TestForceFlag:
    def test_force_flag_passed_through(self, tmp_cwd):
        """Running twice with --force should overwrite silently (exit 0)."""
        runner.invoke(app, ["--quick", "--output", "pytest.ini"])
        result = runner.invoke(app, ["--quick", "--output", "pytest.ini", "--force"])
        assert result.exit_code == 0

    def test_without_force_on_existing_file_prompts(self, tmp_cwd):
        """Running twice without --force prompts for overwrite (stdin gets 'n')."""
        runner.invoke(app, ["--quick", "--output", "pytest.ini"])
        # Provide 'n' to decline overwrite — typer.Abort should be raised
        result = runner.invoke(app, ["--quick", "--output", "pytest.ini"], input="n\n")
        # Should exit non-zero because user declined (typer.Abort)
        assert result.exit_code != 0


class TestInteractiveMode:
    def test_non_tty_exits_one(self, mocker):
        """--interactive in a non-TTY context should exit with code 1."""
        mocker.patch("sys.stdin.isatty", return_value=False)
        result = runner.invoke(app, ["--interactive"])
        assert result.exit_code == 1

    def test_non_tty_error_message(self, mocker):
        """--interactive in a non-TTY context should print a TTY/terminal error."""
        mocker.patch("sys.stdin.isatty", return_value=False)
        result = runner.invoke(app, ["--interactive"])
        assert "terminal" in result.output.lower() or "tty" in result.output.lower()

    def test_interactive_flag_in_help(self):
        """--interactive flag should appear in help text."""
        result = runner.invoke(app, ["--help"])
        assert "--interactive" in result.output

    def test_interactive_full_flow_pytest_ini(self, tmp_cwd, mocker):
        """--interactive writes pytest.ini when run_interactive returns a pytest.ini path."""
        from pytest_pw_config_gen.defaults import build_defaults
        out_path = tmp_cwd / "pytest.ini"
        mocker.patch(
            "pytest_pw_config_gen.cli.run_interactive",
            return_value=(build_defaults(), "pytest.ini", out_path),
        )
        result = runner.invoke(app, ["--interactive"])
        assert result.exit_code == 0, result.output
        assert out_path.exists()

    def test_interactive_full_flow_conftest(self, tmp_cwd, mocker):
        """--interactive writes conftest.py when run_interactive returns a conftest.py path."""
        from pytest_pw_config_gen.defaults import build_defaults
        out_path = tmp_cwd / "conftest.py"
        mocker.patch(
            "pytest_pw_config_gen.cli.run_interactive",
            return_value=(build_defaults(), "conftest.py", out_path),
        )
        result = runner.invoke(app, ["--interactive"])
        assert result.exit_code == 0, result.output
        assert out_path.exists()
