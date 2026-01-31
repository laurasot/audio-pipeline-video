"""Atomic browser actions: click, type, extract. One action per function."""

import re
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page

from automation_intelligence.browser.navigation import YOUTUBE_CHANNEL_BASE
from automation_intelligence.browser.selectors import (
    channel_name_heading_locator,
    chatgpt_composer_locator,
    recent_video_title_links_locator,
    recent_videos_container_locator,
)
from automation_intelligence.logging.logger import get_logger

logger = get_logger(__name__)

DEFAULT_RECENT_VIDEOS_LIMIT = 10


def parse_relative_age_days(text: str) -> float | None:
    """Parse YouTube aria-label relative age into days (best-effort).

    Supports common English and Spanish formats, e.g.:
      - "3 days ago"
      - "hace 3 días"
      - "Streamed 2 hours ago"
      - "hace 2 semanas"

    Returns:
      - float days (approx for weeks/months/years)
      - 0.0 for minutes/hours
      - None if not detected
    """
    if not text:
        return None

    t = " ".join(text.strip().lower().split())

    # Spanish: "hace 3 días", "hace 2 semanas", "hace 1 año"
    m = re.search(
        r"\bhace\s+(\d+)\s+(minuto|minutos|hora|horas|día|días|semana|semanas|mes|meses|año|años)\b",
        t,
    )
    if m:
        n = float(m.group(1))
        unit = m.group(2)
        if unit.startswith("minut") or unit.startswith("hora"):
            return 0.0
        if unit.startswith("día") or unit.startswith("días"):
            return n
        if unit.startswith("seman"):
            return n * 7.0
        if unit.startswith("mes"):
            return n * 30.0
        if unit.startswith("año") or unit.startswith("años"):
            return n * 365.0

    # English: "3 days ago", "2 weeks ago"
    m = re.search(
        r"\b(\d+)\s+(minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\s+ago\b",
        t,
    )
    if m:
        n = float(m.group(1))
        unit = m.group(2)
        if unit.startswith("minute") or unit.startswith("hour"):
            return 0.0
        if unit.startswith("day"):
            return n
        if unit.startswith("week"):
            return n * 7.0
        if unit.startswith("month"):
            return n * 30.0
        if unit.startswith("year"):
            return n * 365.0

    return None


def get_channel_name(page: Page) -> str:
    """Extract the channel name (main heading) from the current channel page."""
    loc = channel_name_heading_locator(page)
    loc.wait_for(state="visible", timeout=10_000)
    text = loc.inner_text()
    return (text or "").strip()


def get_recent_video_titles(page: Page, limit: int = DEFAULT_RECENT_VIDEOS_LIMIT) -> list[str]:
    """Extract recent video titles from the channel Home tab."""
    videos = get_recent_videos(page, limit=limit)
    return [v["title"] for v in videos]


def get_recent_videos(page: Page, limit: int = DEFAULT_RECENT_VIDEOS_LIMIT) -> list[dict[str, str]]:
    """Extract up to limit recent videos (title + url) from the channel Videos tab."""
    container = recent_videos_container_locator(page)
    container.first.wait_for(state="visible", timeout=10_000)
    links = recent_video_title_links_locator(page).all()
    result: list[dict[str, str]] = []
    for node in links[:limit]:
        title_raw = node.get_attribute("title") or node.inner_text()
        href = node.get_attribute("href") or ""
        if not title_raw:
            continue
        title = title_raw.strip()
        url = _normalize_video_url(href)
        if url:
            result.append({"title": title, "url": url})
    return result


def get_recent_videos_with_age(
    page: Page, limit: int = DEFAULT_RECENT_VIDEOS_LIMIT
) -> list[dict[str, object]]:
    """Extract up to limit recent videos (title + url + age_days) from the channel page.

    age_days is parsed from the link aria-label (best-effort); None if missing/unknown.
    """
    container = recent_videos_container_locator(page)
    container.first.wait_for(state="visible", timeout=10_000)
    links = recent_video_title_links_locator(page).all()

    result: list[dict[str, object]] = []
    for node in links[:limit]:
        title_raw = node.get_attribute("title") or node.inner_text()
        href = node.get_attribute("href") or ""
        aria = node.get_attribute("aria-label") or ""
        if not title_raw:
            continue
        title = title_raw.strip()
        url = _normalize_video_url(href)
        if not url:
            continue
        age_days = parse_relative_age_days(aria)
        result.append({"title": title, "url": url, "age_days": age_days})
    return result


def wait_for_chatgpt_composer(page: Page, timeout_ms: int = 15_000) -> None:
    """Wait until the ChatGPT message input is visible. Indicates user is logged in and chat is ready."""
    logger.info("Waiting for ChatGPT composer (message input), timeout_ms=%s", timeout_ms)
    loc = chatgpt_composer_locator(page)
    loc.wait_for(state="visible", timeout=timeout_ms)
    logger.info("ChatGPT composer visible")


def type_in_chatgpt_and_send(page: Page, text: str) -> None:
    """Type the given text into the ChatGPT composer and send (Enter)."""
    loc = chatgpt_composer_locator(page)
    loc.wait_for(state="visible", timeout=10_000)
    logger.info("Typing prompt into ChatGPT composer (%s chars)", len(text))
    loc.fill(text)
    logger.debug("Prompt filled, sending via Enter")
    loc.press("Enter")
    logger.info("ChatGPT prompt sent")


def _normalize_video_url(href: str) -> str:
    """Turn a video href (relative or absolute) into a full YouTube URL."""
    if not href:
        return ""
    if href.startswith("http://") or href.startswith("https://"):
        parsed = urlparse(href)
        if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
            return href
        return ""
    return urljoin(YOUTUBE_CHANNEL_BASE, href)
