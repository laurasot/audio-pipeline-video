"""YouTube transcript helpers. Uses youtube-transcript-api (same data as transcript extensions)."""

import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi

from automation_intelligence.logging.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TRANSCRIPT_MAX_SECONDS = 60.0


def video_id_from_youtube_url(url: str) -> str | None:
    """Extract YouTube video ID from a watch URL or short link."""
    if not url or not url.strip():
        return None
    s = url.strip()
    if "youtu.be/" in s:
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", s)
        return match.group(1) if match else None
    parsed = urlparse(s)
    if "youtube.com" not in parsed.netloc:
        return None
    qs = parse_qs(parsed.query)
    v = qs.get("v", [])
    return v[0] if v and len(v[0]) == 11 else None


def get_first_minute_transcript(
    video_url: str,
    max_seconds: float = DEFAULT_TRANSCRIPT_MAX_SECONDS,
) -> str:
    """Return transcript text for the first max_seconds of the video (same source as transcript extensions).

    video_url: YouTube watch URL or youtu.be link.
    max_seconds: maximum duration in seconds to include (default 60).
    Returns empty string if no transcript, video unavailable, or on error.
    """
    vid = video_id_from_youtube_url(video_url)
    if not vid:
        logger.warning("No video ID in URL", extra={"url": video_url})
        return ""

    api = YouTubeTranscriptApi()
    fetched = None
    try:
        # Try Spanish first, then English (videos may have only es captions)
        fetched = api.fetch(vid, languages=["es", "en"])
    except NoTranscriptFound:
        # Fallback: use first available transcript (e.g. when "en" exists only as
        # translation of "es" and fetch(languages=[...]) only looks at native codes)
        try:
            transcript_list = api.list(vid)
            for transcript in transcript_list:
                try:
                    fetched = transcript.fetch()
                    break
                except Exception:
                    continue
        except Exception as e:
            logger.warning(
                "Could not fetch transcript (fallback failed): %s (video_id=%s)",
                str(e),
                vid,
                extra={"video_id": vid, "error": str(e)},
            )
            return ""
    except Exception as e:
        err_msg = str(e)
        logger.warning(
            "Could not fetch transcript: %s (video_id=%s)",
            err_msg,
            vid,
            extra={"video_id": vid, "error": err_msg},
        )
        return ""

    if fetched is None:
        logger.warning(
            "No transcript available for video_id=%s",
            vid,
            extra={"video_id": vid},
        )
        return ""

    if not fetched:
        return ""

    parts: list[str] = []
    for snippet in fetched:
        start = getattr(snippet, "start", 0) or 0
        if float(start) >= max_seconds:
            break
        text = (getattr(snippet, "text", "") or "").strip()
        if text:
            parts.append(text)

    result = " ".join(parts).replace("\n", " ").strip()
    logger.debug(
        "Transcript fetched",
        extra={"video_id": vid, "max_seconds": max_seconds, "char_count": len(result)},
    )
    return result
