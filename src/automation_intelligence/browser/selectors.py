"""Centralized selectors for browser automation. No inline selectors elsewhere.

Priority: data-testid > roles > visible text > CSS as last resort.
"""

from playwright.sync_api import Locator, Page


def channel_name_heading_locator(page: Page) -> Locator:
    """Locator for the channel name on a YouTube channel page (main heading)."""
    return page.get_by_role("heading").first


def channel_about_description_locator(page: Page) -> Locator:
    """Locator for the channel About / description text when visible."""
    return page.get_by_role("paragraph").filter(
        has=page.locator("yt-formatted-string")
    ).first


def recent_videos_container_locator(page: Page) -> Locator:
    """Locator for the rich grid item container. Wait on .first before resolving video links."""
    return page.locator("ytd-rich-item-renderer")


def recent_video_title_links_locator(page: Page) -> Locator:
    """Locator for the video link (a#video-title-link) whose inner yt-formatted-string#video-title holds the title."""
    return page.locator("ytd-rich-item-renderer a#video-title-link")


def chatgpt_composer_locator(page: Page) -> Locator:
    """Locator for the ChatGPT message input (textarea or contenteditable). Visible when logged in and chat is ready."""
    return page.get_by_placeholder("Message ChatGPT").or_(page.get_by_placeholder("Message"))


def chatgpt_send_button_locator(page: Page) -> Locator:
    """Locator for the ChatGPT send button. Fallback when Enter does not submit."""
    return page.get_by_role("button", name="Send").or_(
        page.locator("button[data-testid='send-button']")
    ).first
