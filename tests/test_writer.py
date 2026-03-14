"""Tests for writer.py — file writer with overwrite guard."""
import pytest
import typer

from pytest_pw_config_gen.writer import write_file


SAMPLE_CONTENT = "[pytest]\naddopts = --browser chromium\n"
UTF8_CONTENT = "# comment: café\n"


class TestWritesToCwd:
    def test_writes_to_cwd(self, tmp_cwd):
        write_file("pytest.ini", SAMPLE_CONTENT, force=False)
        assert (tmp_cwd / "pytest.ini").exists()

    def test_content_written(self, tmp_cwd):
        write_file("pytest.ini", SAMPLE_CONTENT, force=False)
        assert (tmp_cwd / "pytest.ini").read_text(encoding="utf-8") == SAMPLE_CONTENT

    def test_returns_none(self, tmp_cwd):
        result = write_file("pytest.ini", SAMPLE_CONTENT, force=False)
        assert result is None

    def test_writes_utf8(self, tmp_cwd):
        write_file("conftest.py", UTF8_CONTENT, force=False)
        assert (tmp_cwd / "conftest.py").read_text(encoding="utf-8") == UTF8_CONTENT


class TestOverwriteGuard:
    def test_overwrite_guard_prompts(self, tmp_cwd, monkeypatch):
        """write_file on existing file with force=False calls typer.confirm."""
        (tmp_cwd / "pytest.ini").write_text(SAMPLE_CONTENT, encoding="utf-8")
        calls = []

        def fake_confirm(msg, abort=False):
            calls.append(msg)

        monkeypatch.setattr(typer, "confirm", fake_confirm)
        write_file("pytest.ini", SAMPLE_CONTENT, force=False)
        assert len(calls) == 1
        assert "pytest.ini" in calls[0]

    def test_overwrite_guard_abort_on_decline(self, tmp_cwd, monkeypatch):
        """When user declines confirm (typer.confirm raises Abort), file is NOT rewritten."""
        original_content = "# original\n"
        (tmp_cwd / "pytest.ini").write_text(original_content, encoding="utf-8")
        new_content = "# new content\n"

        def fake_confirm_abort(msg, abort=False):
            raise typer.Abort()

        monkeypatch.setattr(typer, "confirm", fake_confirm_abort)
        with pytest.raises(typer.Abort):
            write_file("pytest.ini", new_content, force=False)
        # File should remain unchanged
        assert (tmp_cwd / "pytest.ini").read_text(encoding="utf-8") == original_content

    def test_force_skips_confirm(self, tmp_cwd, monkeypatch):
        """write_file on existing file with force=True does NOT call typer.confirm."""
        (tmp_cwd / "pytest.ini").write_text(SAMPLE_CONTENT, encoding="utf-8")
        calls = []

        def fake_confirm(msg, abort=False):
            calls.append(msg)

        monkeypatch.setattr(typer, "confirm", fake_confirm)
        write_file("pytest.ini", "# overwritten\n", force=True)
        assert len(calls) == 0

    def test_force_overwrites_content(self, tmp_cwd, monkeypatch):
        """force=True rewrites the file with new content."""
        (tmp_cwd / "pytest.ini").write_text(SAMPLE_CONTENT, encoding="utf-8")
        new_content = "# new content\n"
        monkeypatch.setattr(typer, "confirm", lambda msg, abort=False: None)
        write_file("pytest.ini", new_content, force=True)
        assert (tmp_cwd / "pytest.ini").read_text(encoding="utf-8") == new_content

    def test_no_prompt_on_new_file(self, tmp_cwd, monkeypatch):
        """When file does not exist, typer.confirm is never called."""
        calls = []

        def fake_confirm(msg, abort=False):
            calls.append(msg)

        monkeypatch.setattr(typer, "confirm", fake_confirm)
        write_file("new_file.ini", SAMPLE_CONTENT, force=False)
        assert len(calls) == 0
