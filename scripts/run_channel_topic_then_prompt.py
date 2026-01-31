#!/usr/bin/env python3
"""Run step 1 (channel-topic + transcript) then build the narrative prompt into output/*.txt.

There is no ChatGPT automation here.
Step 1 uses Playwright to navigate YouTube (optionally with a Chrome profile).
Step 2 builds the narrative prompt and writes it to a .txt file in ./output (or --out-dir).
"""

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
        description="Step 1 (channel + transcript) then write narrative prompt to output/*.txt"
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
        "--transcript-seconds",
        type=float,
        default=None,
        metavar="SECS",
        help="Max duration in seconds for the video transcript (default: from .env TRANSCRIPT_MAX_SECONDS).",
    )
    parser.add_argument(
        "--total-parts",
        type=int,
        metavar="N",
        help="Number of story parts for the prompt (default: from .env total_parts).",
    )
    parser.add_argument(
        "--out-dir",
        metavar="PATH",
        default=None,
        help="Output directory for the prompt .txt (default: ./output).",
    )
    args = parser.parse_args()

    from automation_intelligence.config.settings import (
        CHROME_DEV_USER_DATA_DEFAULT,
        CHROME_USER_DATA_DEFAULT,
        TRANSCRIPT_MAX_SECONDS,
    )
    from automation_intelligence.pipelines.channel_topic_pipeline import run_channel_topic_pipeline
    from automation_intelligence.pipelines.script_pipeline import run_script_pipeline_build_prompt

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

    print("=== Step 1: Channel topic + transcript ===")
    result1 = run_channel_topic_pipeline(
        args.channel,
        headless=not args.show,
        progress=print,
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        browser_channel=browser_channel,
        transcript_max_seconds=transcript_sec,
    )
    if not result1.chosen_video_url or not result1.first_minute_transcript:
        print("Step 1 did not produce a video or transcript. Stopping.")
        sys.exit(1)

    print("\n=== Step 2: Build narrative prompt (.txt) ===")
    result2 = run_script_pipeline_build_prompt(
        progress=print,
        topic=result1.chosen_video_title,
        context=result1.first_minute_transcript,
        total_parts=args.total_parts,
        output_dir=args.out_dir,
    )
    if not result2.success:
        print("Step 2 failed.")
        if result2.error_message:
            print(f"  Error: {result2.error_message}")
        sys.exit(1)

    print(
        "\nDone. Topic:",
        result1.chosen_video_title[:60] + ("..." if len(result1.chosen_video_title) > 60 else ""),
    )
    print("Transcript length:", len(result1.first_minute_transcript), "chars.")
    print("Prompt file:", result2.output_path)


if __name__ == "__main__":
    main()

