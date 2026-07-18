"""User-editable settings for CubeSlove's browser controller."""

# Leave this as None to let the program find Chrome automatically.  If that
# fails on Windows, use for example:
# CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PATH = None

# One face turn takes about this many milliseconds.  35-50 ms is a good range;
# values below one display frame (16 ms) are intentionally rejected.
MOVE_DURATION_MS = 40

# The official CRX is downloaded only as a package of ordinary web resources;
# it is no longer installed into the automated Chrome profile.  Set a local
# .crx path only when the download service is unavailable.
EXTENSION_CRX_PATH = None

# True matches the old program: Chrome remains visible after Python finishes.
KEEP_BROWSER_OPEN = True

# Maximum wait for page loading, scrambling, or an individual browser action.
PAGE_TIMEOUT_SECONDS = 30

# A fixed browser size keeps the original command.py colour-sampling geometry
# stable.  Device scaling is forced to 100% inside this automation window.
BROWSER_WINDOW_WIDTH = 1920
BROWSER_WINDOW_HEIGHT = 1080

# command.py expects four 600 x 600 JPEG files.  The controller normally finds
# the coloured cube automatically.  The offset is used only as a fallback if
# automatic detection fails after a future page redesign.
CAPTURE_SIZE = 600
CAPTURE_FALLBACK_OFFSET_Y = 100
