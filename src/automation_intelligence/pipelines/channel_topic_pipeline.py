"""Step 1: Identify the topic of the new video. Navigate to the channel (param), pick one of last 10 at random, extract title, transcript of first minute."""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from automation_intelligence.browser import actions
from automation_intelligence.browser import navigation
from automation_intelligence.browser.context import create_browser_context, new_page
from automation_intelligence.logging.logger import get_logger
from automation_intelligence.transcript import (
    DEFAULT_TRANSCRIPT_MAX_SECONDS,
    get_first_minute_transcript,
)

logger = get_logger(__name__)

RECENT_VIDEOS_POOL_SIZE = 10


def _noop_progress(_msg: str) -> None:
    pass


@dataclass
class ChannelTopicResult:
    """Result of identifying the topic from a channel: one video chosen at random from the last 10."""

    channel_name: str
    channel_url: str
    chosen_video_title: str
    chosen_video_url: str
    first_minute_transcript: str
    recent_video_titles: list[str]
    topic_summary: str


def run_channel_topic_pipeline(
    channel_param: str,
    *,
    headless: bool = True,
    recent_videos_limit: int = RECENT_VIDEOS_POOL_SIZE,
    rng: random.Random | None = None,
    progress: Callable[[str], None] | None = None,
    user_data_dir: str | Path | None = None,
    profile_directory: str | None = None,
    browser_channel: str | None = None,
    transcript_max_seconds: float = DEFAULT_TRANSCRIPT_MAX_SECONDS,
) -> ChannelTopicResult:
    """Navigate to the channel, get last N videos, pick one at random, return its title, URL and transcript.

    channel_param: URL, @handle, or path (e.g. @mychannel, /@mychannel, /channel/UC...).
    recent_videos_limit: pool size (default 10). One is chosen at random.
    rng: optional Random instance for reproducible tests.
    progress: optional callback (e.g. print) to show each step; receives one string per step.
    user_data_dir: Chrome "User Data" folder (parent of profiles).
    profile_directory: "Default", "Profile 1", "Profile 2", etc.
    browser_channel: when user_data_dir is set, "chrome" (default), "chrome-dev", "chrome-beta", "chrome-canary".
    transcript_max_seconds: max duration in seconds for the transcript (default 60).
    """
    start = time.perf_counter()
    out = progress if progress is not None else _noop_progress
    logger.info("Channel topic pipeline started", extra={"channel_param": channel_param})

    out("Paso 1: Normalizando URL del canal...")
    channel_url = navigation.normalize_channel_url(channel_param)
    out(f"  -> URL: {channel_url}")

    rnd = rng or random.Random()

    with create_browser_context(
        headless=headless,
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        channel=browser_channel,
    ) as context:
        page = new_page(context)
        out("Paso 2: Navegando al canal...")
        navigation.navigate_to_channel(page, channel_url)

        out("Paso 3: Obteniendo nombre del canal...")
        channel_name = actions.get_channel_name(page)
        out(f"  -> Nombre: {channel_name}")

        out(f"Paso 4: Buscando ultimos {recent_videos_limit} videos (#video-title)...")
        videos = actions.get_recent_videos(page, limit=recent_videos_limit)
        out(f"  -> Encontrados: {len(videos)} videos.")

    if not videos:
        chosen_title = ""
        chosen_url = ""
        first_minute_transcript = ""
        out("Paso 5: No se encontraron videos.")
        logger.warning("No recent videos found on channel", extra={"channel_url": channel_url})
    else:
        out("Paso 5: Eligiendo un video al azar...")
        chosen = rnd.choice(videos)
        chosen_title = chosen["title"]
        chosen_url = chosen["url"]
        out(f"  -> Elegido: {chosen_title}")
        out(f"  -> URL: {chosen_url}")
        logger.info(
            "Chosen video (random from last %s)",
            recent_videos_limit,
            extra={"title": chosen_title, "url": chosen_url},
        )
        out(f"Paso 6: Obteniendo transcripcion (primeros {transcript_max_seconds:.0f} s)...")
        first_minute_transcript = get_first_minute_transcript(
            chosen_url, max_seconds=transcript_max_seconds
        )
        out(f"  -> Transcripcion: {len(first_minute_transcript)} caracteres.")
        logger.info(
            "Transcription done (chars=%s). Next step: build prompt to output/*.txt.",
            len(first_minute_transcript),
        )

    recent_titles = [v["title"] for v in videos]
    topic_summary = _build_topic_summary(channel_name, chosen_title, chosen_url)
    elapsed = time.perf_counter() - start
    out(f"Paso 7: Listo. ({round(elapsed, 2)} s)")
    logger.info(
        "Channel topic pipeline finished: channel=%s chosen=%s elapsed_sec=%.2f",
        channel_name, chosen_title, round(elapsed, 2),
    )
    if user_data_dir and chosen_url:
        extra_args = " --chrome-dev" if browser_channel == "chrome-dev" else ""
        logger.info(
            "Next: python scripts/run_channel_topic_then_prompt.py <channel> --user-data-dir %s --chrome-profile %s%s",
            repr(str(user_data_dir)),
            repr(profile_directory or "Default"),
            extra_args,
        )

    return ChannelTopicResult(
        channel_name=channel_name,
        channel_url=channel_url,
        chosen_video_title=chosen_title,
        chosen_video_url=chosen_url,
        first_minute_transcript=first_minute_transcript,
        recent_video_titles=recent_titles,
        topic_summary=topic_summary,
    )


def _build_topic_summary(channel_name: str, chosen_title: str, chosen_url: str) -> str:
    """Build a short topic summary from channel name and the chosen video."""
    parts = [f"Channel: {channel_name}", f"Chosen: {chosen_title}"]
    if chosen_url:
        parts.append(chosen_url)
    return " | ".join(parts)
