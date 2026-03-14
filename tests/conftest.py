import os
import pathlib
import pytest


@pytest.fixture
def tmp_cwd(tmp_path):
    """Change working directory to a temp dir for the duration of the test."""
    original = pathlib.Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)
