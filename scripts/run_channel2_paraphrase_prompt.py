#!/usr/bin/env python3
"""Channel 2: pick a recent video, transcribe, and generate YOUTUBE_SCRIPT_PARAPHRASE_PROMPT only.

Example:
  python scripts/run_channel2_paraphrase_prompt.py @nombre_canal --recent-videos-limit 10 --transcript-seconds 60
  python scripts/run_channel2_paraphrase_prompt.py @nombre_canal --full-transcript
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Allow running without install: add src to path when executed as script
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    _src = _root / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))


def _slugify_filename(text: str, *, max_len: int = 80) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9 _-]+", "", t)
    t = t.replace(" ", "_").strip("_-")
    return (t or "prompt")[:max_len]


def _extract_youtube_video_id(url: str) -> str | None:
    """Extract a YouTube video id from common URL shapes."""
    if not url:
        return None
    u = url.strip()
    try:
        parsed = urlparse(u)
    except Exception:
        return None

    host = (parsed.netloc or "").lower()
    path = parsed.path or ""

    # https://youtu.be/<id>
    if "youtu.be" in host:
        vid = path.strip("/").split("/", 1)[0]
        return vid or None

    # https://www.youtube.com/watch?v=<id>
    if "youtube.com" in host:
        qs = parse_qs(parsed.query or "")
        if "v" in qs and qs["v"]:
            return qs["v"][0]

        # https://www.youtube.com/shorts/<id>
        m = re.search(r"/shorts/([A-Za-z0-9_-]{6,})", path)
        if m:
            return m.group(1)

        # https://www.youtube.com/embed/<id>
        m = re.search(r"/embed/([A-Za-z0-9_-]{6,})", path)
        if m:
            return m.group(1)

    return None


def _require_thumbnail_ocr_deps():
    """Import deps only when thumbnail/OCR is used."""
    try:
        import requests  # type: ignore
        import easyocr  # type: ignore
        from PIL import Image  # type: ignore
    except ModuleNotFoundError as e:
        missing = getattr(e, "name", None) or "a required dependency"
        print(
            "Missing dependency for thumbnail OCR.\n"
            f"  Missing: {missing}\n"
            '  Install: pip install -e ".[images]"  (or: pip install requests easyocr Pillow)',
            file=sys.stderr,
        )
        raise SystemExit(2) from e
    return requests, easyocr, Image


def _download_youtube_thumbnail(video_url: str, out_path: Path) -> Path | None:
    """Download the best available YouTube thumbnail for a video URL."""
    vid = _extract_youtube_video_id(video_url)
    if not vid:
        return None

    requests, _, _ = _require_thumbnail_ocr_deps()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Try best-to-worst thumbnail variants
    candidates = [
        f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{vid}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",
        f"https://i.ytimg.com/vi/{vid}/default.jpg",
    ]

    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )

    for thumb_url in candidates:
        try:
            resp = sess.get(thumb_url, timeout=12)
            if resp.status_code != 200:
                continue
            ct = (resp.headers.get("content-type") or "").lower()
            if ct and "image/" not in ct:
                continue
            out_path.write_bytes(resp.content)
            return out_path
        except Exception:
            continue

    return None


def _ocr_image(image_path: Path) -> str:
    """Run OCR on an image file and return the detected text."""
    _, easyocr, Image = _require_thumbnail_ocr_deps()

    # CPU mode for compatibility.
    reader = easyocr.Reader(["en", "es"], gpu=False, verbose=False)
    img = Image.open(image_path)
    results = reader.readtext(img, detail=0, paragraph=True)
    text = "\n".join([r.strip() for r in results if isinstance(r, str) and r.strip()])
    return text.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Channel 2: From a YouTube channel, pick a video, transcribe, and write the paraphrase prompt to output/*.txt"
    )
    parser.add_argument(
        "channel",
        help="Channel URL, @handle, or path (e.g. @mychannel, https://youtube.com/@foo)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the browser window (default: headless / no UI)",
    )
    parser.add_argument(
        "--chrome-profile",
        nargs="?",
        const="",
        default=None,
        metavar="NAME",
        help="Use Chrome user profile. Omit NAME for Default; or 'Profile 1', etc. Chrome must be closed.",
    )
    parser.add_argument(
        "--chrome-dev",
        action="store_true",
        help="Use Chrome Dev base path (with --chrome-profile). Default is stable Chrome.",
    )
    parser.add_argument(
        "--user-data-dir",
        metavar="PATH",
        help="Full path to Chrome 'User Data' folder. E.g. ...\\Chrome\\User Data",
    )
    parser.add_argument(
        "--recent-videos-limit",
        type=int,
        default=10,
        metavar="N",
        help="How many recent videos to consider (default: 10). One is chosen at random.",
    )
    parser.add_argument(
        "--transcript-seconds",
        type=float,
        default=None,
        metavar="SECS",
        help="Max duration in seconds for transcript (default: TRANSCRIPT_MAX_SECONDS from .env).",
    )
    parser.add_argument(
        "--full-transcript",
        action="store_true",
        help="Transcribe the full video (ignores --transcript-seconds).",
    )
    parser.add_argument(
        "--out-dir",
        metavar="PATH",
        default=None,
        help="Output directory for the prompt .txt (default: ./output).",
    )
    parser.add_argument(
        "--out-name",
        metavar="FILENAME",
        default=None,
        help="Output filename (default: auto timestamp + chosen video title + _paraphrase).",
    )
    parser.add_argument(
        "--thumbnail-ocr",
        action="store_true",
        help="Also download the chosen video's YouTube thumbnail and run OCR (writes a *_thumbnail_ocr.txt file).",
    )
    args = parser.parse_args()

    from automation_intelligence.config.settings import (
        CHROME_DEV_USER_DATA_DEFAULT,
        CHROME_USER_DATA_DEFAULT,
        PROJECT_ROOT,
        TRANSCRIPT_MAX_SECONDS,
    )
    from automation_intelligence.pipelines.channel_topic_pipeline import run_channel_topic_pipeline
    from automation_intelligence.prompts.youtube_script_paraphrase_prompt import (
        build_youtube_script_paraphrase_prompt,
    )

    if args.user_data_dir is not None:
        user_data_dir = args.user_data_dir
        profile_directory = args.chrome_profile if args.chrome_profile else "Default"
        browser_channel = "chrome-dev" if args.chrome_dev else None
    elif args.chrome_profile is not None:
        base = CHROME_DEV_USER_DATA_DEFAULT if args.chrome_dev else CHROME_USER_DATA_DEFAULT
        user_data_dir = str(base)
        profile_directory = args.chrome_profile if args.chrome_profile else "Default"
        browser_channel = "chrome-dev" if args.chrome_dev else "chrome"
    else:
        user_data_dir = None
        profile_directory = None
        browser_channel = None

    transcript_sec = args.transcript_seconds if args.transcript_seconds is not None else TRANSCRIPT_MAX_SECONDS
    transcript_max_seconds = None if args.full_transcript else float(transcript_sec)

    print("=== Channel 2 / Step 1: Choose video + transcript ===")
    step1 = run_channel_topic_pipeline(
        args.channel,
        headless=not args.show,
        progress=print,
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        browser_channel=browser_channel,
        transcript_max_seconds=transcript_max_seconds,
        recent_videos_limit=args.recent_videos_limit,
    )
    if not step1.chosen_video_url or not step1.first_minute_transcript:
        print("Step 1 did not produce a video or transcript. Stopping.")
        sys.exit(1)

    print("\n=== Channel 2 / Step 2: Build paraphrase prompt (.txt) ===")
    prompt_text = build_youtube_script_paraphrase_prompt(
        step1.chosen_video_title, step1.first_minute_transcript
    )

    out_dir = Path(args.out_dir) if args.out_dir is not None else (PROJECT_ROOT / "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.out_name:
        filename = args.out_name
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{_slugify_filename(step1.chosen_video_title)}_paraphrase.txt"

    out_path = (out_dir / filename).resolve()
    out_path.write_text(prompt_text, encoding="utf-8")

    if args.thumbnail_ocr:
        thumbs_dir = out_dir / "thumbnails"
        base = out_path.stem.replace("_paraphrase", "")
        thumb_path = (thumbs_dir / f"{base}_thumbnail.jpg").resolve()
        downloaded = _download_youtube_thumbnail(step1.chosen_video_url, thumb_path)
        if downloaded is None:
            print("\nThumbnail: could not download (unsupported URL or not available).")
        else:
            try:
                ocr_text = _ocr_image(downloaded)
            except SystemExit:
                raise
            except Exception as e:
                print(f"\nThumbnail OCR failed: {type(e).__name__}: {e}")
            else:
                ocr_out = (out_dir / f"{base}_thumbnail_ocr.txt").resolve()
                ocr_out.write_text(ocr_text, encoding="utf-8")
                print("\nThumbnail:", str(downloaded))
                print("Thumbnail OCR file:", str(ocr_out))

    print("\nDone.")
    print("Chosen video:", step1.chosen_video_title)
    print("URL:", step1.chosen_video_url)
    print("Transcript length:", len(step1.first_minute_transcript), "chars.")
    print("Prompt file:", str(out_path))


if __name__ == "__main__":
    main()

