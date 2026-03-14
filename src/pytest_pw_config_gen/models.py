"""PlaywrightConfig dataclass — shared contract between all layers."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PlaywrightConfig:
    # pytest-playwright addopts flags
    browsers: List[str] = field(default_factory=lambda: ["chromium"])
    headed: bool = False
    browser_channel: Optional[str] = None  # e.g. "chrome", "msedge"
    base_url: Optional[str] = None
    slowmo: int = 0
    tracing: str = "off"
    video: str = "off"
    screenshot: str = "off"
    output_dir: Optional[str] = None  # --output; where artifacts are stored
    device: Optional[str] = None
    reruns: int = 0  # via pytest-rerunfailures --reruns
    reporter: Optional[str] = None  # "html" | "junit" | "json"
    # pytest ini options
    timeout: int = 30  # seconds; requires pytest-timeout plugin
    testpaths: List[str] = field(default_factory=lambda: ["tests"])
    workers: Optional[int] = None  # via -n flag with pytest-xdist
    markers: List[str] = field(default_factory=list)
    # conftest.py browser_context_args
    viewport_width: int = 1280
    viewport_height: int = 720
    action_timeout: Optional[int] = None  # ms; default_timeout for all actions
    locale: Optional[str] = None
    timezone_id: Optional[str] = None
    geolocation_lat: Optional[float] = None
    geolocation_lon: Optional[float] = None
    storage_state: Optional[str] = None
    color_scheme: Optional[str] = None
    accept_downloads: bool = False
    permissions: List[str] = field(default_factory=list)
    http_credentials_user: Optional[str] = None
    http_credentials_pass: Optional[str] = None
    extra_http_headers: Dict[str, str] = field(default_factory=dict)
    user_agent: Optional[str] = None
    ignore_https_errors: bool = False
