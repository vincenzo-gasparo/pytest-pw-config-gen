"""Renderer dispatch — maps output format strings to renderer modules."""
import importlib
from typing import Any


_RENDERER_MAP = {
    "pytest.ini": "pytest_pw_config_gen.renderers.pytest_ini",
    "pyproject.toml": "pytest_pw_config_gen.renderers.pyproject_toml",
    "conftest.py": "pytest_pw_config_gen.renderers.conftest_py",
}


def get_renderer(output_format: str) -> Any:
    """Return the renderer module for the given output format string.

    Args:
        output_format: One of "pytest.ini", "pyproject.toml", "conftest.py"

    Returns:
        Module with a render(config: PlaywrightConfig) -> str function.

    Raises:
        ValueError: If output_format is not recognized.
    """
    module_path = _RENDERER_MAP.get(output_format)
    if module_path is None:
        raise ValueError(
            f"Unknown output format: {output_format!r}. "
            f"Expected one of: {', '.join(_RENDERER_MAP)}"
        )
    return importlib.import_module(module_path)
