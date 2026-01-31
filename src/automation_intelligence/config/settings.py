"""Browser and pipeline settings. No secrets or hardcoded credentials. Loads from .env when present."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Paths (project root = directory containing src/)
_PKG_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT: Path = _PKG_ROOT.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Browser
BROWSER_HEADLESS: bool = True
BROWSER_VIEWPORT_WIDTH: int = 1280
BROWSER_VIEWPORT_HEIGHT: int = 720
NAVIGATION_TIMEOUT_MS: float = 30_000.0
DEFAULT_ACTION_TIMEOUT_MS: float = 10_000.0

# Chrome user profile (for --chrome-profile). Windows default paths.
# Chrome must be closed when using this; Chrome locks the profile.
CHROME_USER_DATA_DEFAULT: Path = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
CHROME_DEV_USER_DATA_DEFAULT: Path = Path.home() / "AppData" / "Local" / "Google" / "Chrome Dev" / "User Data"

# Transcript: max duration in seconds for the chosen video transcript (from .env TRANSCRIPT_MAX_SECONDS).
TRANSCRIPT_MAX_SECONDS: float = float(os.getenv("TRANSCRIPT_MAX_SECONDS", "60"))

# Narrative prompt: total parts for the story (from .env total_parts). Used when building the ChatGPT prompt.
TOTAL_PARTS: int = int(os.getenv("total_parts", "5"))
