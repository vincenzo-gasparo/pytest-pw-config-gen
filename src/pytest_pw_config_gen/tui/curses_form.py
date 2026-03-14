"""Arrow-key navigable config form using Python's built-in curses module.

  ↑ / ↓      move cursor
  SPACE       toggle bool | open submenu for select/multiselect | edit input
  ENTER       same as SPACE
  Ctrl+G      generate & exit
  ESC / q     cancel
"""
import curses
import curses.ascii
import pathlib
import sys
from dataclasses import replace
from typing import Any, Dict, List, Optional, Tuple

from pytest_pw_config_gen.defaults import build_defaults
from pytest_pw_config_gen.models import PlaywrightConfig

# ── Color pairs ────────────────────────────────────────────────────────────────
_C_CURSOR    = 1   # highlighted row
_C_SEP       = 2   # section separator
_C_VALUE     = 3   # value column
_C_DIM       = 4   # disabled / hint text
_C_EDIT      = 5   # edit bar at bottom


def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(_C_CURSOR, curses.COLOR_BLACK,   curses.COLOR_WHITE)   # selected row
    curses.init_pair(_C_SEP,    curses.COLOR_YELLOW,  -1)                   # section headers
    curses.init_pair(_C_VALUE,  curses.COLOR_CYAN,    -1)                   # value column
    curses.init_pair(_C_DIM,    curses.COLOR_WHITE,   curses.COLOR_BLACK)   # status bar
    curses.init_pair(_C_EDIT,   curses.COLOR_BLACK,   curses.COLOR_YELLOW)  # edit bar


# ── Row descriptors ────────────────────────────────────────────────────────────
# Each row: (kind, key, label, choices, gate)
#   kind    : "sep" | "bool" | "select" | "multiselect" | "input" | "int"
#   key     : key in values dict (None for separators)
#   label   : display label
#   choices : list[str] for select/multiselect, else None
#   gate    : key of a bool that must be True to show this row (None = always)

_INI_ROWS: List[Tuple] = [
    ("sep",         None,              "Browser",                      None,                                                           None),
    ("multiselect", "browsers",        "Browsers",                     ["chromium", "firefox", "webkit"],                              None),
    ("bool",        "headed",          "Headed mode",                  None,                                                           None),
    ("bool",        "set_channel",     "Use browser channel",          None,                                                           None),
    ("select",      "browser_channel", "  Channel",                    ["chrome", "chrome-beta", "chrome-dev", "msedge"],              "set_channel"),
    ("bool",        "set_device",      "Emulate device",               None,                                                           None),
    ("input",       "device",          "  Device name",                None,                                                           "set_device"),
    ("sep",         None,              "Recording",                    None,                                                           None),
    ("select",      "tracing",         "Tracing",                      ["off", "on", "retain-on-failure"],                             None),
    ("select",      "video",           "Video recording",              ["off", "on", "retain-on-failure"],                             None),
    ("select",      "screenshot",      "Screenshots",                  ["off", "on", "only-on-failure"],                               None),
    ("bool",        "set_output",      "Custom artifact output dir",   None,                                                           None),
    ("input",       "output_dir",      "  Artifact dir",               None,                                                           "set_output"),
    ("sep",         None,              "Network",                      None,                                                           None),
    ("bool",        "set_base_url",    "Set base URL",                 None,                                                           None),
    ("input",       "base_url",        "  Base URL",                   None,                                                           "set_base_url"),
    ("int",         "slowmo",          "Slow-motion delay (ms)",       None,                                                           None),
    ("sep",         None,              "Parallelism & Reliability",    None,                                                           None),
    ("bool",        "set_workers",     "Run in parallel (xdist)",      None,                                                           None),
    ("int",         "workers",         "  Number of workers",          None,                                                           "set_workers"),
    ("int",         "reruns",          "Retries for failed tests",     None,                                                           None),
    ("sep",         None,              "Reporting",                    None,                                                           None),
    ("bool",        "set_reporter",    "Enable test reporter",         None,                                                           None),
    ("select",      "reporter",        "  Reporter format",            ["html", "junit", "json"],                                      "set_reporter"),
    ("sep",         None,              "Test Organisation",            None,                                                           None),
    ("int",         "timeout",         "Default timeout (seconds)",    None,                                                           None),
    ("input",       "testpaths",       "Test paths",                   None,                                                           None),
    ("bool",        "set_markers",     "Add custom markers",           None,                                                           None),
    ("input",       "markers",         "  Markers (comma-separated)",  None,                                                           "set_markers"),
]

_CONFTEST_ROWS: List[Tuple] = [
    ("sep",         None,                "Viewport",                         None,                                                   None),
    ("int",         "viewport_width",    "Viewport width (px)",              None,                                                   None),
    ("int",         "viewport_height",   "Viewport height (px)",             None,                                                   None),
    ("bool",        "set_action_timeout","Set per-action timeout",           None,                                                   None),
    ("int",         "action_timeout",    "  Action timeout (ms)",            None,                                                   "set_action_timeout"),
    ("sep",         None,                "Locale & Timezone",                None,                                                   None),
    ("bool",        "set_locale",        "Override locale",                  None,                                                   None),
    ("input",       "locale",            "  Locale",                         None,                                                   "set_locale"),
    ("bool",        "set_tz",            "Override timezone",                None,                                                   None),
    ("input",       "timezone_id",       "  Timezone ID",                    None,                                                   "set_tz"),
    ("sep",         None,                "Location & Context",               None,                                                   None),
    ("bool",        "set_geo",           "Set geolocation",                  None,                                                   None),
    ("input",       "geo_lat",           "  Latitude",                       None,                                                   "set_geo"),
    ("input",       "geo_lon",           "  Longitude",                      None,                                                   "set_geo"),
    ("bool",        "set_storage",       "Load auth storage state",          None,                                                   None),
    ("input",       "storage_state",     "  Storage state path",             None,                                                   "set_storage"),
    ("select",      "color_scheme",      "Color scheme",                     ["no-preference", "light", "dark", "(not set)"],        None),
    ("bool",        "accept_downloads",  "Accept downloads",                 None,                                                   None),
    ("bool",        "set_permissions",   "Grant browser permissions",        None,                                                   None),
    ("input",       "permissions_str",   "  Permissions (comma-sep)",        None,                                                   "set_permissions"),
    ("sep",         None,                "Network",                          None,                                                   None),
    ("bool",        "set_http_creds",    "HTTP basic auth",                  None,                                                   None),
    ("input",       "http_user",         "  Username",                       None,                                                   "set_http_creds"),
    ("input",       "http_pass",         "  Password",                       None,                                                   "set_http_creds"),
    ("bool",        "set_extra_headers", "Extra HTTP headers",               None,                                                   None),
    ("input",       "extra_headers_str", "  Headers (Key: Val, ...)",        None,                                                   "set_extra_headers"),
    ("bool",        "set_ua",            "Override User-Agent",              None,                                                   None),
    ("input",       "user_agent",        "  User-Agent",                     None,                                                   "set_ua"),
    ("bool",        "ignore_https",      "Ignore HTTPS errors",              None,                                                   None),
    ("sep",         None,                "Test Settings",                    None,                                                   None),
    ("int",         "timeout",           "Default timeout (seconds)",        None,                                                   None),
    ("input",       "testpaths",         "Test paths",                       None,                                                   None),
]


# ── Default values ─────────────────────────────────────────────────────────────

def _ini_defaults(d: PlaywrightConfig) -> Dict[str, Any]:
    return {
        "browsers":        list(d.browsers),
        "headed":          d.headed,
        "set_channel":     bool(d.browser_channel),
        "browser_channel": d.browser_channel or "chrome",
        "set_device":      bool(d.device),
        "device":          d.device or "",
        "tracing":         d.tracing,
        "video":           d.video,
        "screenshot":      d.screenshot,
        "set_output":      bool(d.output_dir),
        "output_dir":      d.output_dir or "test-results",
        "set_base_url":    bool(d.base_url),
        "base_url":        d.base_url or "",
        "slowmo":          str(d.slowmo),
        "set_workers":     bool(d.workers),
        "workers":         str(d.workers or 2),
        "reruns":          str(d.reruns),
        "set_reporter":    bool(d.reporter),
        "reporter":        d.reporter or "html",
        "timeout":         str(d.timeout),
        "testpaths":       " ".join(d.testpaths),
        "set_markers":     bool(d.markers),
        "markers":         ", ".join(d.markers),
    }


def _conftest_defaults(d: PlaywrightConfig) -> Dict[str, Any]:
    return {
        "viewport_width":     str(d.viewport_width),
        "viewport_height":    str(d.viewport_height),
        "set_action_timeout": d.action_timeout is not None,
        "action_timeout":     str(d.action_timeout or 5000),
        "set_locale":         bool(d.locale),
        "locale":             d.locale or "",
        "set_tz":             bool(d.timezone_id),
        "timezone_id":        d.timezone_id or "",
        "set_geo":            d.geolocation_lat is not None,
        "geo_lat":            str(d.geolocation_lat or 0.0),
        "geo_lon":            str(d.geolocation_lon or 0.0),
        "set_storage":        bool(d.storage_state),
        "storage_state":      d.storage_state or "",
        "color_scheme":       d.color_scheme or "no-preference",
        "accept_downloads":   d.accept_downloads,
        "set_permissions":    bool(d.permissions),
        "permissions_str":    ", ".join(d.permissions),
        "set_http_creds":     bool(d.http_credentials_user),
        "http_user":          d.http_credentials_user or "",
        "http_pass":          d.http_credentials_pass or "",
        "set_extra_headers":  bool(d.extra_http_headers),
        "extra_headers_str":  ", ".join(f"{k}: {v}" for k, v in d.extra_http_headers.items()),
        "set_ua":             bool(d.user_agent),
        "user_agent":         d.user_agent or "",
        "ignore_https":       d.ignore_https_errors,
        "timeout":            str(d.timeout),
        "testpaths":          " ".join(d.testpaths),
    }


# ── Config builders ────────────────────────────────────────────────────────────

def _build_ini(values: dict, defaults: PlaywrightConfig) -> PlaywrightConfig:
    return replace(
        defaults,
        browsers=values["browsers"] or ["chromium"],
        headed=values["headed"],
        browser_channel=values["browser_channel"] if values["set_channel"] else None,
        device=values["device"] or None if values["set_device"] else None,
        tracing=values["tracing"],
        video=values["video"],
        screenshot=values["screenshot"],
        output_dir=values["output_dir"] or None if values["set_output"] else None,
        base_url=values["base_url"] or None if values["set_base_url"] else None,
        slowmo=int(values["slowmo"] or 0),
        workers=int(values["workers"] or 2) if values["set_workers"] else None,
        reruns=int(values["reruns"] or 0),
        reporter=values["reporter"] if values["set_reporter"] else None,
        timeout=int(values["timeout"] or 30),
        testpaths=[p for p in values["testpaths"].replace(",", " ").split() if p] or defaults.testpaths,
        markers=[m.strip() for m in values["markers"].split(",") if m.strip()] if values["set_markers"] else defaults.markers,
    )


def _parse_headers(s: str) -> Dict[str, Any]:
    """Parse 'Key: Value, Key2: Value2' into a dict."""
    result = {}
    for part in s.split(","):
        part = part.strip()
        if ":" in part:
            k, _, v = part.partition(":")
            result[k.strip()] = v.strip()
    return result


def _build_conftest(values: dict, defaults: PlaywrightConfig) -> PlaywrightConfig:
    color = values["color_scheme"]
    # Merge user permissions; geolocation permission is auto-added by the renderer
    perms = [p.strip() for p in values["permissions_str"].split(",") if p.strip()] if values["set_permissions"] else []
    return replace(
        defaults,
        viewport_width=int(values["viewport_width"] or 1280),
        viewport_height=int(values["viewport_height"] or 720),
        action_timeout=int(values["action_timeout"] or 5000) if values["set_action_timeout"] else None,
        locale=values["locale"] or None if values["set_locale"] else None,
        timezone_id=values["timezone_id"] or None if values["set_tz"] else None,
        geolocation_lat=float(values["geo_lat"]) if values["set_geo"] else None,
        geolocation_lon=float(values["geo_lon"]) if values["set_geo"] else None,
        storage_state=values["storage_state"] or None if values["set_storage"] else None,
        color_scheme=None if color == "(not set)" else color,
        accept_downloads=values["accept_downloads"],
        permissions=perms,
        http_credentials_user=values["http_user"] or None if values["set_http_creds"] else None,
        http_credentials_pass=values["http_pass"] or None if values["set_http_creds"] else None,
        extra_http_headers=_parse_headers(values["extra_headers_str"]) if values["set_extra_headers"] else {},
        user_agent=values["user_agent"] or None if values["set_ua"] else None,
        ignore_https_errors=values["ignore_https"],
        timeout=int(values["timeout"] or 30),
        testpaths=[p for p in values["testpaths"].replace(",", " ").split() if p] or defaults.testpaths,
    )


# ── Rendering ──────────────────────────────────────────────────────────────────

_LABEL_W = 34


def _render_row(row: Tuple, values: dict, w: int) -> Tuple[str, int, int]:
    """Return (text, label_attr, value_attr) for a row."""
    kind, key, label, choices, gate = row

    if kind == "sep":
        sep = f"  {label}  "
        line = "─" * 2 + sep + "─" * max(0, w - len(sep) - 3)
        return line, curses.color_pair(_C_SEP) | curses.A_BOLD, 0

    value = values.get(key, "")

    if kind == "bool":
        check = "[x]" if value else "[ ]"
        text = f"  {check} {label}"
        return text.ljust(w - 1), curses.A_NORMAL, 0

    lbl = label.ljust(_LABEL_W)

    if kind == "multiselect":
        val_str = ", ".join(value) if value else "(none)"
        text = f"  {lbl}  {val_str} >"
    elif kind == "select":
        text = f"  {lbl}  {value} >"
    else:  # input / int
        text = f"  {lbl}  {value}"

    return text.ljust(w - 1), curses.A_NORMAL, curses.color_pair(_C_VALUE)


# ── Popup helpers ──────────────────────────────────────────────────────────────

def _waddstr(win, y: int, x: int, text: str, attr: int = curses.A_NORMAL) -> None:
    """addstr that silently truncates to window bounds."""
    try:
        mh, mw = win.getmaxyx()
        available = mw - x - 1
        if available <= 0:
            return
        win.addstr(y, x, text[:available], attr)
    except curses.error:
        pass


def _popup_select(stdscr, title: str, choices: List[str], current: str) -> Optional[str]:
    """Single-choice popup. Returns chosen value or None (cancelled)."""
    h, w = stdscr.getmaxyx()
    cursor = choices.index(current) if current in choices else 0
    pw = min(max(len(title), max(len(c) for c in choices)) + 8, w - 4)
    ph = len(choices) + 4
    py = max(0, (h - ph) // 2)
    px = max(0, (w - pw) // 2)

    stdscr.clear()
    stdscr.refresh()

    win = curses.newwin(ph, pw, py, px)
    win.keypad(True)

    while True:
        win.clear()
        win.box()
        _waddstr(win, 0, 2, f" {title} ", curses.A_BOLD)
        for i, choice in enumerate(choices):
            attr = curses.color_pair(_C_CURSOR) if i == cursor else curses.A_NORMAL
            _waddstr(win, i + 2, 2, f"  {choice}  ".ljust(pw - 4), attr)
        _waddstr(win, ph - 1, 2, " ^/v ENTER confirm  ESC cancel ", curses.color_pair(_C_DIM))
        win.refresh()

        key = win.getch()
        if key == curses.KEY_UP:
            cursor = max(0, cursor - 1)
        elif key == curses.KEY_DOWN:
            cursor = min(len(choices) - 1, cursor + 1)
        elif key in (ord('\n'), ord('\r'), ord(' ')):
            return choices[cursor]
        elif key in (27, ord('q')):
            return None


def _popup_multiselect(stdscr, title: str, choices: List[str], selected: List[str]) -> Optional[List[str]]:
    """Multi-choice popup with checkboxes. Returns new list or None (cancelled)."""
    h, w = stdscr.getmaxyx()
    cursor = 0
    current = set(selected)
    pw = min(max(len(title), max(len(c) for c in choices)) + 12, w - 4)
    ph = len(choices) + 4
    py = max(0, (h - ph) // 2)
    px = max(0, (w - pw) // 2)

    stdscr.clear()
    stdscr.refresh()

    win = curses.newwin(ph, pw, py, px)
    win.keypad(True)

    while True:
        win.clear()
        win.box()
        _waddstr(win, 0, 2, f" {title} ", curses.A_BOLD)
        for i, choice in enumerate(choices):
            check = "[x]" if choice in current else "[ ]"
            line = f"  {check} {choice}".ljust(pw - 4)
            attr = curses.color_pair(_C_CURSOR) if i == cursor else curses.A_NORMAL
            _waddstr(win, i + 2, 2, line, attr)
        _waddstr(win, ph - 1, 2, " SPACE toggle  ENTER confirm  ESC cancel ", curses.color_pair(_C_DIM))
        win.refresh()

        key = win.getch()
        if key == curses.KEY_UP:
            cursor = max(0, cursor - 1)
        elif key == curses.KEY_DOWN:
            cursor = min(len(choices) - 1, cursor + 1)
        elif key == ord(' '):
            choice = choices[cursor]
            if choice in current:
                current.discard(choice)
            else:
                current.add(choice)
        elif key in (ord('\n'), ord('\r')):
            result = [c for c in choices if c in current]
            return result if result else list(selected)
        elif key in (27, ord('q')):
            return None


def _edit_string(stdscr, prompt: str, current: str) -> Optional[str]:
    """Inline bottom-bar string editor. Returns new value or None (cancelled)."""
    h, w = stdscr.getmaxyx()
    text = list(current)
    pos = len(text)

    while True:
        # Draw edit bar on the last line
        val = "".join(text)
        bar = f" {prompt}: {val} "
        stdscr.attron(curses.color_pair(_C_EDIT))
        stdscr.addstr(h - 1, 0, bar.ljust(w - 1)[:w - 1])
        # Cursor indicator
        cursor_x = min(len(f" {prompt}: ") + pos, w - 2)
        stdscr.move(h - 1, cursor_x)
        stdscr.attroff(curses.color_pair(_C_EDIT))
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('\n'), ord('\r')):
            return "".join(text)
        elif key == 27:  # ESC
            return None
        elif key in (curses.KEY_BACKSPACE, curses.ascii.BS, 127):
            if pos > 0:
                text.pop(pos - 1)
                pos -= 1
        elif key == curses.KEY_LEFT:
            pos = max(0, pos - 1)
        elif key == curses.KEY_RIGHT:
            pos = min(len(text), pos + 1)
        elif key == curses.KEY_HOME:
            pos = 0
        elif key == curses.KEY_END:
            pos = len(text)
        elif 32 <= key < 127:
            text.insert(pos, chr(key))
            pos += 1


# ── Main form loop ─────────────────────────────────────────────────────────────

def _visible(all_rows: List[Tuple], values: dict) -> List[Tuple]:
    """Filter rows by gate conditions."""
    out = []
    for row in all_rows:
        _, _, _, _, gate = row
        if gate and not values.get(gate, False):
            continue
        out.append(row)
    return out


def _navigable_indices(rows: List[Tuple]) -> List[int]:
    """Indices of rows that the cursor can land on (non-separators)."""
    return [i for i, r in enumerate(rows) if r[0] != "sep"]


def _run_form(stdscr, title: str, all_rows: List[Tuple], values: dict) -> Optional[dict]:
    """Main form loop. Returns updated values or None if cancelled."""
    curses.curs_set(0)
    stdscr.keypad(True)

    nav = _navigable_indices(_visible(all_rows, values))
    nav_pos = 0          # index into nav[]
    scroll = 0           # top visible row index in the rendered list
    status = ""

    while True:
        h, w = stdscr.getmaxyx()
        rows = _visible(all_rows, values)
        nav = _navigable_indices(rows)
        if not nav:
            break
        nav_pos = min(nav_pos, len(nav) - 1)
        cursor_row = nav[nav_pos]

        # Adjust scroll so cursor is always visible (leave 2 rows for header + status)
        body_h = h - 3
        if cursor_row < scroll:
            scroll = cursor_row
        elif cursor_row >= scroll + body_h:
            scroll = cursor_row - body_h + 1

        stdscr.erase()

        def _saddstr(y, x, text, attr=curses.A_NORMAL):
            try:
                stdscr.addstr(y, x, text[:w - x - 1], attr)
            except curses.error:
                pass

        # Header
        header = f" pytest-pw-config-gen  |  {title}  |  Ctrl+G generate  q cancel "
        _saddstr(0, 0, header.ljust(w - 1), curses.color_pair(_C_CURSOR))

        # Rows
        for screen_y, row_idx in enumerate(range(scroll, min(scroll + body_h, len(rows)))):
            row = rows[row_idx]
            text, lattr, _ = _render_row(row, values, w)
            is_cursor = row_idx == cursor_row
            y = screen_y + 1

            if row[0] == "sep":
                _saddstr(y, 0, text, lattr)
            elif is_cursor:
                _saddstr(y, 0, text, curses.color_pair(_C_CURSOR))
            else:
                _saddstr(y, 0, text)

        # Status bar
        hint = "SPACE/ENTER act on field"
        bar = (f" {status}" if status else f" {hint}").ljust(w - 1)
        _saddstr(h - 1, 0, bar, curses.color_pair(_C_DIM))

        stdscr.refresh()
        status = ""

        key = stdscr.getch()

        # Navigation
        if key == curses.KEY_UP:
            nav_pos = max(0, nav_pos - 1)
            continue
        elif key == curses.KEY_DOWN:
            nav_pos = min(len(nav) - 1, nav_pos + 1)
            continue

        # Cancel
        elif key in (27, ord('q')):
            return None

        # Generate
        elif key == 7:  # Ctrl+G
            return values

        # Act on current row
        elif key in (ord(' '), ord('\n'), ord('\r')):
            row = rows[cursor_row]
            kind, key_name, label, choices, gate = row

            if kind == "bool":
                values[key_name] = not values.get(key_name, False)
                # Re-build nav in case gated rows appear/disappear
                rows = _visible(all_rows, values)
                nav = _navigable_indices(rows)
                nav_pos = min(nav_pos, len(nav) - 1)

            elif kind == "select":
                result = _popup_select(stdscr, label.strip(), choices, values.get(key_name, choices[0]))
                if result is not None:
                    values[key_name] = result
                stdscr.clear()  # force full repaint to erase popup remnants

            elif kind == "multiselect":
                result = _popup_multiselect(stdscr, label.strip(), choices, values.get(key_name, []))
                if result is not None:
                    values[key_name] = result
                stdscr.clear()  # force full repaint to erase popup remnants

            elif kind in ("input", "int"):
                current = str(values.get(key_name, ""))
                result = _edit_string(stdscr, label.strip(), current)
                if result is not None:
                    if kind == "int":
                        if result.lstrip("-").isdigit():
                            values[key_name] = result
                        else:
                            status = f"Must be a number"
                    else:
                        values[key_name] = result

    return values


# ── File type selector ─────────────────────────────────────────────────────────

def _select_file_type(stdscr) -> Optional[str]:
    choices = ["pytest.ini", "pyproject.toml", "conftest.py"]
    return _popup_select(stdscr, "Config file to generate", choices, "pytest.ini")


def _prompt_output_path(stdscr, file_type: str) -> Optional[pathlib.Path]:
    """Ask for output path, confirm overwrite if file exists. Returns Path or None."""
    default = str(pathlib.Path.cwd() / file_type)
    raw = _edit_string(stdscr, "Output path", default)
    if raw is None:
        return None

    path = pathlib.Path(raw).expanduser()

    if path.exists():
        confirmed = _popup_select(
            stdscr,
            f"{path.name} already exists. Overwrite?",
            ["Yes", "No"],
            "No",
        )
        if confirmed != "Yes":
            return None

    return path


# ── Entry point ────────────────────────────────────────────────────────────────

def _curses_main(stdscr) -> Optional[Tuple[PlaywrightConfig, str, pathlib.Path]]:
    _init_colors()
    defaults = build_defaults()

    # Step 1: pick file type
    file_type = _select_file_type(stdscr)
    if file_type is None:
        return None

    stdscr.clear()
    stdscr.refresh()

    # Step 2: run config form
    if file_type == "conftest.py":
        values = _conftest_defaults(defaults)
        result = _run_form(stdscr, "conftest.py", _CONFTEST_ROWS, values)
        if result is None:
            return None
        config = _build_conftest(result, defaults)
    else:
        values = _ini_defaults(defaults)
        result = _run_form(stdscr, file_type, _INI_ROWS, values)
        if result is None:
            return None
        config = _build_ini(result, defaults)

    # Step 3: output path + overwrite confirmation
    path = _prompt_output_path(stdscr, file_type)
    if path is None:
        return None

    return config, file_type, path


def run_interactive() -> Tuple[PlaywrightConfig, str, pathlib.Path]:
    """Drop-in replacement for prompter.run_interactive()."""
    import typer
    from rich.console import Console

    if not sys.stdin.isatty():
        Console(stderr=True).print(
            "[bold red]Error:[/bold red] Interactive mode requires a TTY. "
            "Use --quick to generate with defaults.",
        )
        raise typer.Exit(1)

    result: list = [None]

    def _main(stdscr):
        result[0] = _curses_main(stdscr)

    curses.wrapper(_main)

    if result[0] is None:
        raise typer.Abort()

    return result[0]
