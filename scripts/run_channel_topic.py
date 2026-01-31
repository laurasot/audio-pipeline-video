#!/usr/bin/env python3
"""CLI entrypoint: run channel-topic pipeline. Orchestrates only; no business logic here."""

import argparse
import sys
from pathlib import Path

# Allow running without install: add src to path when executed as script
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    _src = _root / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 1: Identify video topic from a YouTube channel. Navigates to the channel and extracts theme."
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
        help="Use Chrome user profile (extensions, cookies). Omit NAME for Default; or pass 'Profile 1', 'Profile 2', etc. Chrome must be closed.",
    )
    parser.add_argument(
        "--chrome-dev",
        action="store_true",
        help="Use Chrome Dev base path (with --chrome-profile). Default is stable Chrome.",
    )
    parser.add_argument(
        "--user-data-dir",
        metavar="PATH",
        help="Full path to Chrome 'User Data' folder (overrides --chrome-profile base). E.g. ...\\Chrome\\User Data",
    )
    from automation_intelligence.config.settings import (
        CHROME_DEV_USER_DATA_DEFAULT,
        CHROME_USER_DATA_DEFAULT,
        TRANSCRIPT_MAX_SECONDS,
    )

    parser.add_argument(
        "--transcript-seconds",
        type=float,
        default=TRANSCRIPT_MAX_SECONDS,
        metavar="SECS",
        help="Max duration in seconds for the video transcript (default: TRANSCRIPT_MAX_SECONDS from .env or 60).",
    )
    args = parser.parse_args()
    channel_param = args.channel
    from automation_intelligence.pipelines.channel_topic_pipeline import (
        run_channel_topic_pipeline,
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
    result = run_channel_topic_pipeline(
        channel_param,
        headless=not args.show,
        progress=print,
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        browser_channel=browser_channel,
        transcript_max_seconds=args.transcript_seconds,
    )
    print(result.topic_summary)
    if result.chosen_video_url:
        print(result.chosen_video_url)
    if result.first_minute_transcript:
        print(f"--- Transcripcion (primeros {args.transcript_seconds:.0f} s) ---")
        print(result.first_minute_transcript)


if __name__ == "__main__":
    main()
