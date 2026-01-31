"""Reusable navigation flows. No business logic, only browser navigation."""

from urllib.parse import urlparse

from playwright.sync_api import Page

from automation_intelligence.logging.logger import get_logger

logger = get_logger(__name__)

YOUTUBE_CHANNEL_BASE = "https://www.youtube.com"
CHATGPT_CHAT_URL = "https://chat.openai.com/"


def normalize_channel_url(channel_param: str) -> str:
    """Turn a channel handle, path or full URL into a full YouTube channel URL."""
    s = channel_param.strip()
    if not s:
        raise ValueError("channel_param must be non-empty")
    if s.startswith("http://") or s.startswith("https://"):
        parsed = urlparse(s)
        if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
            return s
        raise ValueError("Channel URL must be a YouTube URL")
    if s.startswith("/"):
        return f"{YOUTUBE_CHANNEL_BASE}{s}"
    if s.startswith("@"):
        return f"{YOUTUBE_CHANNEL_BASE}/{s}"
    if s.startswith("channel/") or s.startswith("c/") or s.startswith("user/"):
        return f"{YOUTUBE_CHANNEL_BASE}/{s}"
    return f"{YOUTUBE_CHANNEL_BASE}/@{s}"


def channel_videos_url(channel_url: str) -> str:
    """Return the URL of the channel's Videos tab (where #video-title elements exist)."""
    return channel_url.rstrip("/") + "/videos"


def navigate_to_channel(page: Page, channel_url: str) -> None:
    """Navigate the page to the given YouTube channel URL. Waits for load state."""
    logger.info("Navigating to channel", extra={"url": channel_url})
    page.goto(channel_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=15_000)


def navigate_to_channel_videos(page: Page, channel_url: str) -> None:
    """Navigate to the channel's Videos tab so recent uploads (#video-title) are visible."""
    videos_url = channel_videos_url(channel_url)
    logger.info("Navigating to channel videos", extra={"url": videos_url})
    page.goto(videos_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=15_000)


def navigate_to_chatgpt(page: Page) -> None:
    """Navigate to ChatGPT chat. Uses profile cookies; user must be logged in beforehand."""
    logger.info("Navigating to ChatGPT: goto %s", CHATGPT_CHAT_URL)
    page.goto(CHATGPT_CHAT_URL, wait_until="domcontentloaded")
    logger.debug("ChatGPT goto done, waiting for networkidle (15s)")
    page.wait_for_load_state("networkidle", timeout=15_000)
    logger.info("ChatGPT page loaded (networkidle), url=%s", page.url)
