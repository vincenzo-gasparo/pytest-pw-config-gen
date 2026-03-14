"""Renderer for conftest.py output format using Jinja2 template."""
import ast
import importlib.resources

from jinja2 import BaseLoader, Environment

from pytest_pw_config_gen.models import PlaywrightConfig


def _python_bool(value: bool) -> str:
    """Jinja2 filter: render Python True/False (not JSON true/false)."""
    return "True" if value else "False"


def render(config: PlaywrightConfig) -> str:
    """Render a conftest.py string from a PlaywrightConfig using the Jinja2 template.

    Args:
        config: PlaywrightConfig instance with all settings.

    Returns:
        A string suitable for writing to conftest.py (passes ast.parse()).

    Raises:
        RuntimeError: If the rendered output is not valid Python syntax.
    """
    template_text = (
        importlib.resources.files("pytest_pw_config_gen.templates")
        .joinpath("conftest_py.j2")
        .read_text(encoding="utf-8")
    )

    env = Environment(loader=BaseLoader())
    env.filters["python_bool"] = _python_bool
    template = env.from_string(template_text)

    # Ensure geolocation permission is present when geolocation is configured
    effective_permissions = list(config.permissions)
    if config.geolocation_lat is not None and "geolocation" not in effective_permissions:
        effective_permissions.insert(0, "geolocation")

    result = template.render(**vars(config), effective_permissions=effective_permissions)

    try:
        ast.parse(result)
    except SyntaxError as exc:
        raise RuntimeError(
            f"Rendered conftest.py has invalid syntax:\n{result}"
        ) from exc

    return result
