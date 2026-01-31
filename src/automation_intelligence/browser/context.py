"""Single point of browser and context creation. User-Agent, viewport, timeouts, headless from config."""

from contextlib import contextmanager
from pathlib import Path
import re
from typing import Iterator

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from automation_intelligence.config.settings import (
    BROWSER_HEADLESS,
    BROWSER_VIEWPORT_HEIGHT,
    BROWSER_VIEWPORT_WIDTH,
    DEFAULT_ACTION_TIMEOUT_MS,
    NAVIGATION_TIMEOUT_MS,
)
from automation_intelligence.logging.logger import get_logger

logger = get_logger(__name__)

_PROFILE_DIR_RE = re.compile(r"^(Default|Profile \d+)$")


def _apply_context_defaults(context: BrowserContext) -> None:
    context.set_default_timeout(DEFAULT_ACTION_TIMEOUT_MS)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)


@contextmanager
def create_browser_context(
    headless: bool | None = None,
    viewport_width: int | None = None,
    viewport_height: int | None = None,
    user_data_dir: str | Path | None = None,
    profile_directory: str | None = None,
    channel: str | None = None,
) -> Iterator[BrowserContext]:
    """Create and yield a configured browser context. Use as: with create_browser_context() as ctx: ...

    When user_data_dir is set, launches Chrome with that profile; extensions and cookies are available.
    user_data_dir: Chrome's "User Data" folder (parent of profiles). For convenience, you may also pass
      a specific profile folder (e.g. ...\\User Data\\Profile 1 or ...\\User Data\\Default) and we'll
      normalize it automatically.
    profile_directory: "Default", "Profile 1", "Profile 2", etc. Uses Default if omitted.
    channel: "chrome" (default), "chrome-dev", "chrome-beta", "chrome-canary". Chrome must be closed.
    """
    headless = headless if headless is not None else BROWSER_HEADLESS
    viewport_width = viewport_width or BROWSER_VIEWPORT_WIDTH
    viewport_height = viewport_height or BROWSER_VIEWPORT_HEIGHT

    with sync_playwright() as p:
        if user_data_dir is not None:
            path = Path(user_data_dir).resolve()
            prof = (profile_directory or "Default").strip()

            # Accept passing a profile folder directly (common mistake): "...\\User Data\\Profile 1".
            # Playwright expects the *User Data* directory; profile selection is done via
            # --profile-directory=<Profile X|Default>.
            if _PROFILE_DIR_RE.match(path.name):
                inferred = path.name
                if prof and prof != inferred:
                    logger.warning(
                        "user_data_dir points to a profile folder (%s) but profile_directory=%s; "
                        "using inferred profile_directory=%s and parent user_data_dir=%s",
                        str(path),
                        prof,
                        inferred,
                        str(path.parent),
                    )
                prof = inferred
                path = path.parent

            args: list[str] = [f"--profile-directory={prof}"] if prof else []

            # Light validation to avoid silently launching a blank profile.
            prof_path = path / prof
            if not prof_path.exists():
                logger.warning(
                    "Chrome profile folder not found on disk: %s (user_data_dir=%s profile_directory=%s). "
                    "You may be using the wrong profile name; check chrome://version -> Profile Path.",
                    str(prof_path),
                    str(path),
                    prof,
                )

            context = p.chromium.launch_persistent_context(
                str(path),
                channel=channel or "chrome",
                headless=headless,
                viewport={"width": viewport_width, "height": viewport_height},
                ignore_https_errors=False,
                args=args if args else None,
            )
            _apply_context_defaults(context)
            logger.debug(
                "Persistent context created (Chrome profile)",
                extra={
                    "user_data_dir": str(path),
                    "profile_directory": prof,
                    "viewport": f"{viewport_width}x{viewport_height}",
                },
            )
            try:
                yield context
            finally:
                context.close()
        else:
            browser: Browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
                ignore_https_errors=False,
            )
            _apply_context_defaults(context)
            logger.debug(
                "Browser context created",
                extra={"headless": headless, "viewport": f"{viewport_width}x{viewport_height}"},
            )
            try:
                yield context
            finally:
                browser.close()


def new_page(context: BrowserContext) -> Page:
    """Create a new page in the given context."""
    return context.new_page()
