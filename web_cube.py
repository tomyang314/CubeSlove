"""Direct browser-side control for the Rubik's Cube web application.

This module replaces slow desktop mouse drags with calls to the JavaScript
objects that already control the cube inside the web page.  The Chrome Web
Store package is unpacked into a local cache and served on ``127.0.0.1`` as a
normal page.  Chrome therefore does not need to install or debug an extension,
which also avoids the extension-loading restrictions in current Chrome builds.
"""

from __future__ import annotations

import functools
import hashlib
import http.server
import os
import re
import shutil
import sys
import threading
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


EXTENSION_ID = "dlabgdldanmcjlmnifgogbnffionmfki"
EXTENSION_STORE_PAGE = (
    "https://chromewebstore.google.com/detail/rubik-cube-for-google-chr/"
    + EXTENSION_ID
)
EXTENSION_DOWNLOAD_URL = (
    "https://clients2.google.com/service/update2/crx"
    "?response=redirect"
    "&prodversion=120.0.0.0"
    "&acceptformat=crx2,crx3"
    "&x=id%3D{}%26uc".format(EXTENSION_ID)
)

_MOVE_RE = re.compile(r"^([UDFBLRXYZ])([123]|')?$")
_FACE_MOVES = frozenset("UDFBLR")
_OPTIMIZED_MIDDLE_AXES = {
    # optimization.py names the three middle slices after the old Mouse
    # methods, not after standard whole-cube x/y/z notation.
    "X": "z",  # replacement for F' B
    "Y": "x",  # replacement for L R'
    "Z": "y",  # replacement for U' D
}
_LOCAL_ONLY_SCRIPT_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*['\"][^'\"]*"
    r"(?:upup(?:\.min)?\.js|rate\.js|localization\.js)"
    r"[^'\"]*['\"][^>]*>\s*</script>",
    re.IGNORECASE,
)


class CubeControlError(RuntimeError):
    """Raised when the browser page cannot accept a direct cube command."""


class MoveSyntaxError(ValueError):
    """Raised when a solver move is not supported by the web controller."""


@dataclass(frozen=True)
class ExecutionReport:
    """Summary returned after a solution has been sent to the page."""

    engine: str
    moves: int
    quarter_turns: int
    elapsed_seconds: float


def normalize_solution(solution: str) -> List[str]:
    """Convert solver output to canonical Singmaster-style tokens.

    Both notations used by common two-phase solvers are accepted:

    - numeric: ``R1 R2 R3``
    - standard: ``R R2 R'``

    ``1`` means clockwise, ``2`` means 180 degrees, and ``3`` means
    counter-clockwise.  X/Y/Z are the optimized middle-layer moves emitted by
    ``optimization.py``.
    """

    if not isinstance(solution, str):
        raise TypeError("solution must be a string")

    cleaned = re.sub(r"\([^)]*\)", " ", solution.replace("’", "'"))
    raw_moves = cleaned.split()
    result: List[str] = []

    for raw_move in raw_moves:
        match = _MOVE_RE.fullmatch(raw_move)
        if match is None:
            raise MoveSyntaxError(
                "Unsupported move {!r}. Expected U/D/L/R/F/B/X/Y/Z with "
                "suffix 1, 2, 3 or '.".format(raw_move)
            )

        base, suffix = match.groups()
        if suffix in (None, "1"):
            result.append(base)
        elif suffix == "2":
            result.append(base + "2")
        else:  # numeric 3 and the prime symbol both mean inverse rotation
            result.append(base + "'")

    return result


def expand_quarter_turns(moves: Iterable[str]) -> List[str]:
    """Expand every 180-degree move into two 90-degree page commands."""

    expanded: List[str] = []
    for move in moves:
        if move.endswith("2"):
            expanded.extend((move[0], move[0]))
        else:
            expanded.append(move)
    return expanded


def to_legacy_cuber_command(moves: Iterable[str]) -> str:
    """Translate canonical moves to Cuber's one-character command format."""

    command: List[str] = []
    for move in expand_quarter_turns(moves):
        if move[0] in _OPTIMIZED_MIDDLE_AXES:
            raise MoveSyntaxError(
                "optimized X/Y/Z middle-layer moves require the modern page engine"
            )
        command.append(move[0].lower() if move.endswith("'") else move[0])
    return "".join(command)


def modern_move_payload(move: str) -> Dict[str, object]:
    """Build the tested command descriptor consumed by the modern page API."""

    if not move or move.endswith("2"):
        raise MoveSyntaxError(
            "modern_move_payload expects one canonical 90-degree move"
        )
    base = move[0]
    if base in _FACE_MOVES:
        return {"kind": "LAYER", "token": move}
    if base in _OPTIMIZED_MIDDLE_AXES:
        return {
            "kind": "MIDDLE",
            "axis": _OPTIMIZED_MIDDLE_AXES[base],
            "angle_sign": 1 if move.endswith("'") else -1,
            "token": move,
        }
    raise MoveSyntaxError("Unsupported canonical move: {!r}".format(move))


def _is_crx(path: Path) -> bool:
    try:
        with path.open("rb") as source:
            return source.read(4) == b"Cr24"
    except OSError:
        return False


def ensure_extension_crx(
    cache_directory: Path, supplied_path: Optional[str] = None
) -> Path:
    """Return a usable CRX, downloading the official store package if needed."""

    if supplied_path:
        supplied = Path(os.path.expandvars(os.path.expanduser(supplied_path)))
        if not _is_crx(supplied):
            raise CubeControlError(
                "EXTENSION_CRX_PATH does not point to a valid Chrome CRX: {}".format(
                    supplied
                )
            )
        return supplied.resolve()

    cache_directory.mkdir(parents=True, exist_ok=True)
    target = cache_directory / "rubik-cube-extension.crx"
    if _is_crx(target):
        return target

    temporary = target.with_suffix(".download")
    request = urllib.request.Request(
        EXTENSION_DOWNLOAD_URL,
        headers={"User-Agent": "Mozilla/5.0 Chrome CubeSlove direct controller"},
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
        if not payload.startswith(b"Cr24"):
            raise CubeControlError("the downloaded file is not a valid CRX package")
        temporary.write_bytes(payload)
        temporary.replace(target)
    except Exception as exc:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise CubeControlError(
            "Could not download the Rubik's Cube web resources from {}. Set "
            "EXTENSION_CRX_PATH in config.py to a local CRX file if necessary. "
            "Original error: {}".format(EXTENSION_STORE_PAGE, exc)
        ) from exc

    return target


def _safe_extract_crx(crx_path: Path, destination: Path) -> None:
    """Extract the ZIP payload in a CRX without permitting path traversal."""

    destination_root = os.path.realpath(str(destination))
    try:
        with zipfile.ZipFile(str(crx_path)) as archive:
            for member in archive.infolist():
                member_path = os.path.realpath(
                    os.path.join(destination_root, member.filename)
                )
                try:
                    inside_destination = (
                        os.path.commonpath([destination_root, member_path])
                        == destination_root
                    )
                except ValueError:
                    inside_destination = False
                if not inside_destination:
                    raise CubeControlError(
                        "The downloaded CRX contains an unsafe path: {}".format(
                            member.filename
                        )
                    )
            archive.extractall(str(destination))
    except (OSError, zipfile.BadZipFile) as exc:
        raise CubeControlError(
            "The Rubik's Cube CRX could not be unpacked: {}".format(exc)
        ) from exc


def _make_page_standalone(index_path: Path) -> None:
    """Remove extension-only helpers while preserving the cube application."""

    try:
        html = index_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CubeControlError(
            "The Rubik's Cube index.html could not be read: {}".format(exc)
        ) from exc

    # These optional helpers call chrome.runtime/chrome.i18n or register a
    # service worker.  The cube engine itself does not need them.  A harmless
    # UpUp stub also covers an inline UpUp.start(...) call used by some releases.
    html = _LOCAL_ONLY_SCRIPT_RE.sub("", html)
    compatibility = (
        "\n<script data-cubeslove-local-runtime>"
        "window.UpUp=window.UpUp||{start:function(){}};"
        "</script>\n"
    )
    if "</head>" in html.lower():
        closing_head = re.search(r"</head>", html, re.IGNORECASE)
        assert closing_head is not None
        html = (
            html[: closing_head.start()]
            + compatibility
            + html[closing_head.start() :]
        )
    else:
        html = compatibility + html

    try:
        index_path.write_text(html, encoding="utf-8")
    except OSError as exc:
        raise CubeControlError(
            "The local Rubik's Cube page could not be prepared: {}".format(exc)
        ) from exc


def prepare_web_runtime(crx_path: Path, cache_directory: Path) -> Path:
    """Build or reuse a standalone local-web copy of the CRX resources."""

    try:
        source_hash = hashlib.sha256(crx_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise CubeControlError("Could not read the CRX file: {}".format(exc)) from exc

    runtime = cache_directory / "web-runtime"
    marker = runtime / ".cubeslove-source-sha256"
    index_path = runtime / "index.html"
    try:
        if index_path.is_file() and marker.read_text(encoding="ascii") == source_hash:
            return runtime
    except (OSError, UnicodeError):
        pass

    building = cache_directory / "web-runtime-building"
    shutil.rmtree(str(building), ignore_errors=True)
    building.mkdir(parents=True, exist_ok=True)

    try:
        _safe_extract_crx(crx_path, building)
        building_index = building / "index.html"
        if not building_index.is_file():
            raise CubeControlError(
                "The downloaded Rubik's Cube package has no index.html"
            )
        _make_page_standalone(building_index)
        (building / ".cubeslove-source-sha256").write_text(
            source_hash, encoding="ascii"
        )
        shutil.rmtree(str(runtime), ignore_errors=True)
        building.replace(runtime)
    except Exception:
        shutil.rmtree(str(building), ignore_errors=True)
        raise

    return runtime


class _QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serve only local static files without printing one line per asset."""

    def log_message(self, format_string: str, *args: object) -> None:
        return


def _find_cube_center(rgb_image) -> Optional[Tuple[float, float]]:
    """Locate the large coloured/dark cube component in a browser screenshot."""

    try:
        import numpy as np
    except ImportError as exc:
        raise CubeControlError(
            "NumPy is required for browser screenshot alignment"
        ) from exc

    image = np.asarray(rgb_image)
    if image.ndim != 3 or image.shape[2] < 3:
        return None

    rgb = image[:, :, :3]
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    mask = (((maximum - minimum) > 20) | (maximum < 120)).astype("uint8")

    height, width = mask.shape
    # Ignore sidebars and buttons.  The game itself is always around the
    # horizontal centre, while its vertical location varies by Chrome version.
    left_limit = int(width * 0.10)
    right_limit = int(width * 0.90)
    mask[:, :left_limit] = 0
    mask[:, right_limit:] = 0

    # Find connected components on a 1/4-size mask.  This avoids adding a new
    # OpenCV dependency to the browser layer and keeps four captures fast.
    sample_step = 4
    sampled = mask[::sample_step, ::sample_step].astype(bool)
    visited = np.zeros(sampled.shape, dtype=bool)
    candidates = []
    sampled_height, sampled_width = sampled.shape
    for start_y, start_x in np.argwhere(sampled):
        start_y = int(start_y)
        start_x = int(start_x)
        if visited[start_y, start_x]:
            continue

        stack = [(start_y, start_x)]
        visited[start_y, start_x] = True
        area = 0
        minimum_x = maximum_x = start_x
        minimum_y = maximum_y = start_y
        while stack:
            current_y, current_x = stack.pop()
            area += 1
            minimum_x = min(minimum_x, current_x)
            maximum_x = max(maximum_x, current_x)
            minimum_y = min(minimum_y, current_y)
            maximum_y = max(maximum_y, current_y)
            for neighbour_y in range(max(0, current_y - 1), min(sampled_height, current_y + 2)):
                for neighbour_x in range(max(0, current_x - 1), min(sampled_width, current_x + 2)):
                    if (
                        not visited[neighbour_y, neighbour_x]
                        and sampled[neighbour_y, neighbour_x]
                    ):
                        visited[neighbour_y, neighbour_x] = True
                        stack.append((neighbour_y, neighbour_x))

        component_width = (maximum_x - minimum_x + 1) * sample_step
        component_height = (maximum_y - minimum_y + 1) * sample_step
        if area < 500 or component_width < 200 or component_height < 200:
            continue
        if component_width > width * 0.85 or component_height > height * 0.95:
            continue
        centre_x = (minimum_x + maximum_x) * sample_step / 2.0
        centre_y = (minimum_y + maximum_y) * sample_step / 2.0
        distance_x = abs(centre_x - width / 2.0)
        candidates.append(
            (area * sample_step * sample_step - distance_x * 20.0, centre_x, centre_y)
        )

    if not candidates:
        return None
    _score, centre_x, centre_y = max(candidates, key=lambda item: item[0])
    return centre_x, centre_y


def find_chrome(explicit_path: Optional[str] = None) -> str:
    """Find Chrome on Windows, macOS or Linux."""

    candidates: List[Optional[str]] = [explicit_path, os.environ.get("CHROME_PATH")]

    if sys.platform.startswith("win"):
        candidates.extend(
            [
                os.path.join(
                    os.environ.get("PROGRAMFILES", r"C:\Program Files"),
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                ),
                os.path.join(
                    os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                ),
                os.path.join(
                    os.environ.get("LOCALAPPDATA", ""),
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                ),
            ]
        )
    elif sys.platform == "darwin":
        candidates.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

    for executable_name in ("google-chrome", "google-chrome-stable", "chromium"):
        candidates.append(shutil.which(executable_name))

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(os.path.expandvars(os.path.expanduser(candidate)))
        if path.is_file():
            return str(path.resolve())

    raise CubeControlError(
        "Google Chrome was not found. Set CHROME_PATH in config.py to the full "
        "path of chrome.exe."
    )


class ChromeCubeController:
    """Open the local cube page and use its in-page JavaScript API."""

    def __init__(
        self,
        chrome_path: Optional[str] = None,
        extension_crx_path: Optional[str] = None,
        move_duration_ms: int = 40,
        keep_browser_open: bool = True,
        page_timeout_seconds: float = 30.0,
        window_width: int = 1920,
        window_height: int = 1080,
    ) -> None:
        if not 16 <= int(move_duration_ms) <= 1000:
            raise ValueError("move_duration_ms must be between 16 and 1000")
        if int(window_width) < 800 or int(window_height) < 700:
            raise ValueError("the browser window must be at least 800 x 700")

        self.chrome_path = chrome_path
        self.extension_crx_path = extension_crx_path
        self.move_duration_ms = int(move_duration_ms)
        self.keep_browser_open = bool(keep_browser_open)
        self.page_timeout_seconds = float(page_timeout_seconds)
        self.window_width = int(window_width)
        self.window_height = int(window_height)
        self.driver = None
        self.engine: Optional[str] = None
        self._http_server = None
        self._server_thread = None
        self._page_url = None

    def open(self) -> str:
        """Launch Chrome on the loopback page and detect its cube engine."""

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError as exc:
            raise CubeControlError(
                "Selenium is not installed. Run: "
                "pip install -r requirements-web-control.txt"
            ) from exc

        project_directory = Path(__file__).resolve().parent
        cache_directory = project_directory / ".cache"
        chrome_binary = find_chrome(self.chrome_path)
        crx_path = ensure_extension_crx(cache_directory, self.extension_crx_path)
        runtime_directory = prepare_web_runtime(crx_path, cache_directory)
        self._start_local_server(runtime_directory)

        options = Options()
        options.binary_location = chrome_binary
        options.add_argument(
            "--window-size={},{}".format(self.window_width, self.window_height)
        )
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--high-dpi-support=1")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-search-engine-choice-screen")
        options.add_experimental_option("detach", self.keep_browser_open)

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_script_timeout(self.page_timeout_seconds)
            self.driver.set_window_rect(
                x=0,
                y=0,
                width=self.window_width,
                height=self.window_height,
            )
            self.driver.get(self._page_url)
            self.engine = self._wait_for_engine(self.page_timeout_seconds)
        except Exception as exc:
            if self.driver is not None:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
            self._stop_local_server()
            raise CubeControlError(
                "Chrome started, but the local Rubik's Cube page could not be "
                "controlled. Selenium Manager may need network access on the "
                "first run. Original error: {}".format(exc)
            ) from exc

        return self.engine

    def _start_local_server(self, runtime_directory: Path) -> None:
        """Serve the prepared page on an OS-assigned loopback port."""

        if self._http_server is not None:
            return
        handler = functools.partial(
            _QuietHTTPRequestHandler, directory=str(runtime_directory)
        )
        try:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        except OSError as exc:
            raise CubeControlError(
                "Could not start the local Rubik's Cube page server: {}".format(exc)
            ) from exc
        server.daemon_threads = True
        thread = threading.Thread(
            target=server.serve_forever,
            name="CubeSlove-local-web",
            daemon=True,
        )
        thread.start()
        self._http_server = server
        self._server_thread = thread
        self._page_url = "http://127.0.0.1:{}/index.html".format(
            server.server_address[1]
        )

    def _stop_local_server(self) -> None:
        server = self._http_server
        if server is not None:
            server.shutdown()
            server.server_close()
        thread = self._server_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self._http_server = None
        self._server_thread = None
        self._page_url = None

    def start_game(self) -> None:
        """Start and finish the page's own scramble without a desktop click."""

        self._require_open()
        if self.engine == "modern":
            self._wait_js(
                "return window.game && game.transition && "
                "game.transition.tweens && game.transition.tweens.cube && "
                "game.transition.tweens.cube.progress >= 1 && "
                "game.transition.activeTransitions === 0;",
                self.page_timeout_seconds,
                "the page's opening animation did not finish",
            )
            result = self.driver.execute_script(
                """
                if (!window.game || typeof game.game !== 'function') {
                    return {ok: false, reason: 'window.game.game is unavailable'};
                }
                if (game.controls.enabled && game.controls.scramble === null) {
                    return {ok: true, alreadyStarted: true};
                }
                game.game(true);
                return {ok: true, alreadyStarted: false};
                """
            )
            if not result or not result.get("ok"):
                raise CubeControlError(
                    "The modern cube page refused to start: {}".format(result)
                )
            self._wait_js(
                "return window.game && game.controls && "
                "game.controls.scramble === null && game.controls.enabled === true;",
                self.page_timeout_seconds,
                "the cube scramble did not finish",
            )
            return

        # Legacy Cuber builds expose shuffle() directly.  Keep this branch
        # mouse-free as well; do not synthesize click or double-click events.
        result = self.driver.execute_script(
            """
            if (!window.cube) {
                return {ok: false, reason: 'window.cube is unavailable'};
            }
            if (typeof cube.shuffle === 'function') {
                cube.shuffle();
                return {ok: true, method: 'cube.shuffle'};
            }
            if (typeof cube.scramble === 'function') {
                cube.scramble();
                return {ok: true, method: 'cube.scramble'};
            }
            return {ok: false, reason: 'no direct legacy start method'};
            """
        )
        if not result or not result.get("ok"):
            raise CubeControlError(
                "The legacy cube page cannot start directly: {}".format(result)
            )
        self._wait_js(
            "return window.cube && cube.isTweening() === 0 && "
            "cube.twistQueue && cube.twistQueue.future.length === 0;",
            self.page_timeout_seconds,
            "the legacy cube scramble did not finish",
        )

    def execute_solution(self, solution: str) -> ExecutionReport:
        """Execute a solver string directly in the web page."""

        self._require_open()
        moves = normalize_solution(solution)
        quarter_turns = expand_quarter_turns(moves)
        if not moves:
            return ExecutionReport(self.engine or "unknown", 0, 0, 0.0)

        started_at = time.perf_counter()
        if self.engine == "modern":
            self._execute_modern(quarter_turns)
        elif self.engine == "legacy":
            self._execute_legacy(moves)
        else:
            raise CubeControlError("No supported cube engine is active")

        return ExecutionReport(
            engine=self.engine,
            moves=len(moves),
            quarter_turns=len(quarter_turns),
            elapsed_seconds=time.perf_counter() - started_at,
        )

    def rotate_view(self, axis: str, quarter_turns: int = 1) -> None:
        """Rotate the whole cube visually without dragging the desktop mouse.

        Turns use the page engine's right-handed axis angles.  Consequently the
        old ``Mouse.up_turning()`` gesture is X=-1, while the old
        ``Mouse.right_turning()`` gesture is Y=+1.  The method waits for the page
        animation and two rendered frames before returning.
        """

        self._require_open()
        axis = str(axis).lower()
        if axis not in ("x", "y", "z"):
            raise ValueError("axis must be x, y or z")
        if isinstance(quarter_turns, bool) or not isinstance(quarter_turns, int):
            raise TypeError("quarter_turns must be an integer")
        if quarter_turns == 0:
            return

        direction = 1 if quarter_turns > 0 else -1
        if self.engine == "legacy":
            canonical = axis.upper() + ("'" if direction > 0 else "")
            for _ in range(abs(quarter_turns)):
                self._execute_legacy([canonical])
            self._wait_for_render()
            return

        self._wait_js(
            "return window.game && game.controls && "
            "game.controls.enabled === true && game.controls.state === 0 && "
            "game.controls.scramble === null;",
            self.page_timeout_seconds,
            "the cube is not ready for a view rotation",
        )
        self.driver.execute_script(
            """
            window.__cubeSolveViewBackup = {
                flipConfig: game.controls.flipConfig,
                speed: game.controls.flipSpeeds[0]
            };
            game.controls.flipConfig = 0;
            game.controls.flipSpeeds[0] = arguments[0];
            """,
            self.move_duration_ms,
        )
        try:
            for turn_index in range(abs(quarter_turns)):
                self._wait_js(
                    "return window.game && game.controls && "
                    "game.controls.state === 0 && game.controls.scramble === null;",
                    self.page_timeout_seconds,
                    "the previous view rotation did not finish",
                )
                result = self.driver.execute_script(
                    """
                    const controls = game.controls;
                    if (!controls.enabled || controls.state !== 0 ||
                            controls.scramble !== null) {
                        return {ok: false, reason: 'controls are busy'};
                    }
                    controls.keyboardMove('CUBE', {
                        axis: arguments[0],
                        angle: arguments[1] * Math.PI / 2,
                        name: 'CubeSlove view rotation'
                    });
                    return {ok: controls.state === 2, reason: null};
                    """,
                    axis,
                    direction,
                )
                if not result or not result.get("ok"):
                    raise CubeControlError(
                        "The page rejected view rotation {} ({}/{}): {}".format(
                            axis,
                            turn_index + 1,
                            abs(quarter_turns),
                            result,
                        )
                    )
                self._wait_js(
                    "return window.game && game.controls && "
                    "game.controls.state === 0;",
                    self.page_timeout_seconds,
                    "view rotation {} did not finish".format(turn_index + 1),
                )
        finally:
            self.driver.execute_script(
                """
                if (window.game && window.__cubeSolveViewBackup) {
                    game.controls.flipConfig =
                        window.__cubeSolveViewBackup.flipConfig;
                    game.controls.flipSpeeds[0] =
                        window.__cubeSolveViewBackup.speed;
                    delete window.__cubeSolveViewBackup;
                }
                """
            )
        self._wait_for_render()

    def capture_cube_image(
        self,
        output_path,
        cube_side: int = 600,
        fallback_offset_y: int = 100,
    ) -> Path:
        """Save a centred cube crop from Chrome, never from the desktop."""

        self._require_open()
        if int(cube_side) < 300:
            raise ValueError("cube_side must be at least 300 pixels")
        cube_side = int(cube_side)
        self._wait_for_render()

        try:
            from PIL import Image
        except ImportError as exc:
            raise CubeControlError(
                "Pillow is required for browser screenshots"
            ) from exc

        try:
            screenshot = Image.open(
                BytesIO(self.driver.get_screenshot_as_png())
            ).convert("RGB")
        except Exception as exc:
            raise CubeControlError(
                "Chrome could not capture the cube image: {}".format(exc)
            ) from exc

        width, height = screenshot.size
        if width < cube_side or height < cube_side:
            raise CubeControlError(
                "The Chrome viewport is only {}x{}; at least {}x{} is needed. "
                "Keep BROWSER_WINDOW_WIDTH/HEIGHT at their defaults.".format(
                    width, height, cube_side, cube_side
                )
            )

        centre = _find_cube_center(screenshot)
        if centre is None:
            centre_x = width / 2.0
            centre_y = height / 2.0 + int(fallback_offset_y)
        else:
            centre_x, centre_y = centre

        left = int(round(centre_x - cube_side / 2.0))
        top = int(round(centre_y - cube_side / 2.0))
        left = max(0, min(width - cube_side, left))
        top = max(0, min(height - cube_side, top))
        crop = screenshot.crop((left, top, left + cube_side, top + cube_side))

        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            crop.save(str(target), format="JPEG", quality=95)
        except OSError as exc:
            raise CubeControlError(
                "Could not save browser screenshot {}: {}".format(target, exc)
            ) from exc
        return target

    def close(self) -> None:
        """Close the controlled browser and its loopback page server."""

        if self.driver is not None:
            try:
                self.driver.quit()
            finally:
                self.driver = None
                self.engine = None
        self._stop_local_server()

    def _execute_modern(self, quarter_turns: Iterable[str]) -> None:
        moves = list(quarter_turns)
        self._wait_js(
            "return window.game && game.controls && "
            "game.controls.enabled === true && game.controls.state === 0 && "
            "game.controls.scramble === null;",
            self.page_timeout_seconds,
            "the cube is not ready to receive the solution",
        )

        self.driver.execute_script(
            """
            window.__cubeSolveControlBackup = {
                flipConfig: game.controls.flipConfig,
                speed: game.controls.flipSpeeds[0]
            };
            game.controls.flipConfig = 0;
            game.controls.flipSpeeds[0] = arguments[0];
            """,
            self.move_duration_ms,
        )

        try:
            for index, move in enumerate(moves, start=1):
                payload = modern_move_payload(move)
                self._wait_js(
                    "return window.game && game.controls && "
                    "game.controls.state === 0 && "
                    "game.controls.scramble === null;",
                    max(5.0, self.page_timeout_seconds),
                    "move {} of {} waited too long for the previous move".format(
                        index, len(moves)
                    ),
                )

                result = self.driver.execute_script(
                    """
                    const move = arguments[0];
                    const controls = game.controls;
                    if (!controls.enabled) {
                        return {ok: false, reason: 'controls are disabled'};
                    }
                    if (controls.state !== 0 || controls.scramble !== null) {
                        return {ok: false, reason: 'controls are busy'};
                    }

                    if (move.kind === 'LAYER') {
                        const converted = game.scrambler.convertMove(move.token);
                        controls.keyboardMove('LAYER', converted);
                    } else if (move.kind === 'MIDDLE') {
                        const middlePosition = {};
                        middlePosition[move.axis] = 0;
                        controls.keyboardMove('LAYER', {
                            position: middlePosition,
                            axis: move.axis,
                            angle: move.angle_sign * Math.PI / 2,
                            name: move.token
                        });
                    } else {
                        return {ok: false, reason: 'unsupported move descriptor'};
                    }
                    return {ok: controls.state === 2, reason: null};
                    """,
                    payload,
                )
                if not result or not result.get("ok"):
                    raise CubeControlError(
                        "The page rejected move {} ({}/{}): {}".format(
                            move, index, len(moves), result
                        )
                    )

                self._wait_js(
                    "return window.game && game.controls && game.controls.state === 0;",
                    max(5.0, self.page_timeout_seconds),
                    "move {} of {} did not finish".format(index, len(moves)),
                )
        finally:
            self.driver.execute_script(
                """
                if (window.game && window.__cubeSolveControlBackup) {
                    game.controls.flipConfig =
                        window.__cubeSolveControlBackup.flipConfig;
                    game.controls.flipSpeeds[0] =
                        window.__cubeSolveControlBackup.speed;
                    delete window.__cubeSolveControlBackup;
                }
                """
            )

    def _execute_legacy(self, moves: Iterable[str]) -> None:
        command = to_legacy_cuber_command(moves)
        self.driver.execute_script(
            """
            window.__cubeSolveTwistDuration = cube.twistDuration;
            cube.twistDuration = arguments[1];
            cube.twist(arguments[0]);
            """,
            command,
            self.move_duration_ms,
        )
        try:
            self._wait_js(
                "return window.cube && cube.isTweening() === 0 && "
                "cube.twistQueue && cube.twistQueue.future.length === 0;",
                max(self.page_timeout_seconds, len(command) * 1.5),
                "the legacy cube did not finish the solution queue",
            )
        finally:
            self.driver.execute_script(
                """
                if (window.cube && window.__cubeSolveTwistDuration !== undefined) {
                    cube.twistDuration = window.__cubeSolveTwistDuration;
                    delete window.__cubeSolveTwistDuration;
                }
                """
            )

    def _wait_for_engine(self, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            engine = self.driver.execute_script(
                """
                if (window.game && game.controls && game.scrambler) return 'modern';
                if (window.cube && typeof cube.twist === 'function') return 'legacy';
                return null;
                """
            )
            if engine in ("modern", "legacy"):
                return engine
            time.sleep(0.05)

        raise CubeControlError(
            "No supported JavaScript cube API was found at {}".format(
                getattr(self.driver, "current_url", self._page_url or "local page")
            )
        )

    def _wait_for_render(self) -> None:
        """Wait until two animation frames have been painted by Chrome."""

        execute_async = getattr(self.driver, "execute_async_script", None)
        if execute_async is None:
            time.sleep(0.05)
            return
        try:
            execute_async(
                """
                const done = arguments[arguments.length - 1];
                requestAnimationFrame(() => requestAnimationFrame(() => done(true)));
                """
            )
        except Exception as exc:
            raise CubeControlError(
                "Chrome did not render the updated cube view: {}".format(exc)
            ) from exc

    def _wait_js(self, script: str, timeout: float, error_message: str) -> None:
        deadline = time.monotonic() + timeout
        last_error = None
        while time.monotonic() < deadline:
            try:
                if self.driver.execute_script(script):
                    return
            except Exception as exc:
                last_error = exc
            time.sleep(0.01)

        if last_error is None:
            raise CubeControlError(error_message)
        raise CubeControlError("{}: {}".format(error_message, last_error))

    def _require_open(self) -> None:
        if self.driver is None or self.engine not in ("modern", "legacy"):
            raise CubeControlError("Call ChromeCubeController.open() first")
