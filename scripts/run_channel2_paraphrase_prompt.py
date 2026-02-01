#!/usr/bin/env python3
"""Channel 2: pick a recent video, transcribe, and generate YOUTUBE_SCRIPT_PARAPHRASE_PROMPT only.

Example:
  python scripts/run_channel2_paraphrase_prompt.py @nombre_canal --days-back 7 --transcript-seconds 60
  python scripts/run_channel2_paraphrase_prompt.py @nombre_canal --full-transcript
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

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
        "--days-back",
        type=int,
        default=None,
        metavar="DAYS",
        help="Only consider videos uploaded/streamed within the last N days (best-effort).",
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
        days_back=args.days_back,
    )
    if not step1.chosen_video_url or not step1.first_minute_transcript:
        print("Step 1 did not produce a video or transcript. Stopping.")
        sys.exit(1)

    print("\n=== Channel 2 / Step 2: Build paraphrase prompt (.txt) ===")
    prompt_text = build_youtube_script_paraphrase_prompt(step1.first_minute_transcript)

    out_dir = Path(args.out_dir) if args.out_dir is not None else (PROJECT_ROOT / "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.out_name:
        filename = args.out_name
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{_slugify_filename(step1.chosen_video_title)}_paraphrase.txt"

    out_path = (out_dir / filename).resolve()
    out_path.write_text(prompt_text, encoding="utf-8")

    print("\nDone.")
    print("Chosen video:", step1.chosen_video_title)
    print("URL:", step1.chosen_video_url)
    print("Transcript length:", len(step1.first_minute_transcript), "chars.")
    print("Prompt file:", str(out_path))


if __name__ == "__main__":
    main()

