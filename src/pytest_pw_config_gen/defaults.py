"""build_defaults() — returns a PlaywrightConfig populated with sensible defaults."""
from pytest_pw_config_gen.models import PlaywrightConfig


def build_defaults() -> PlaywrightConfig:
    """Return a PlaywrightConfig populated with opinionated sensible defaults."""
    return PlaywrightConfig()
