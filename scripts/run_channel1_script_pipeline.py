#!/usr/bin/env python3
"""Channel 1 CLI entrypoint:

- Step 2 (default): build narrative prompt from --topic + --context and save to output/*.txt
- All-in-one: pass --channel to run Step 1 (Playwright -> pick video -> transcript) and then Step 2.
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
        description="Channel 1: Build narrative prompt to output/*.txt (from topic+context) or run all-in-one from a YouTube channel."
    )
    parser.add_argument(
        "--channel",
        metavar="CHANNEL",
        default=None,
        help="All-in-one mode: Channel URL or @handle. If set, the script will pick a recent video, fetch transcript, then write the prompt.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="All-in-one mode: Show the browser window (default: headless).",
    )
    parser.add_argument(
        "--chrome-profile",
        nargs="?",
        const="",
        default=None,
        metavar="NAME",
        help="All-in-one mode: Use Chrome user profile. Omit NAME for Default; or pass 'Profile 1', etc. Chrome must be closed.",
    )
    parser.add_argument(
        "--chrome-dev",
        action="store_true",
        help="All-in-one mode: Use Chrome Dev base path (with --chrome-profile). Default is stable Chrome.",
    )
    parser.add_argument(
        "--user-data-dir",
        metavar="PATH",
        help="All-in-one mode: Full path to Chrome 'User Data' folder (overrides base). E.g. ...\\Chrome\\User Data",
    )
    parser.add_argument(
        "--recent-videos-limit",
        type=int,
        default=10,
        metavar="N",
        help="All-in-one mode: How many recent videos to consider (default: 10). One is chosen at random.",
    )
    parser.add_argument(
        "--transcript-seconds",
        type=float,
        default=None,
        metavar="SECS",
        help="All-in-one mode: Max duration in seconds for transcript (default: TRANSCRIPT_MAX_SECONDS from .env).",
    )
    parser.add_argument(
        "--full-transcript",
        action="store_true",
        help="All-in-one mode: Transcribe the full video (ignores --transcript-seconds).",
    )
    parser.add_argument(
        "--topic",
        metavar="TEXT",
        required=False,
        help="Step 2 mode: Video title / topic for the narrative prompt (required unless --channel is used).",
    )
    parser.add_argument(
        "--context",
        metavar="TEXT",
        help="Transcript text for the narrative prompt. Ignored if --context-file is set.",
    )
    parser.add_argument(
        "--context-file",
        metavar="PATH",
        help="Read context (transcript) from file. Overrides --context.",
    )
    parser.add_argument(
        "--total-parts",
        type=int,
        metavar="N",
        help="Number of story parts (default: value from .env total_parts, or 5).",
    )
    parser.add_argument(
        "--out-dir",
        metavar="PATH",
        default=None,
        help="Output directory (default: ./output).",
    )
    parser.add_argument(
        "--out-name",
        metavar="FILENAME",
        default=None,
        help="Output filename (default: auto timestamp + topic).",
    )
    args = parser.parse_args()

    from automation_intelligence.pipelines.script_pipeline import run_script_pipeline_build_prompt

    topic_text: str | None = (args.topic or "").strip() if args.topic is not None else None
    context_text: str | None = None

    if args.channel:
        from automation_intelligence.config.settings import (
            CHROME_DEV_USER_DATA_DEFAULT,
            CHROME_USER_DATA_DEFAULT,
            TRANSCRIPT_MAX_SECONDS,
        )
        from automation_intelligence.pipelines.channel_topic_pipeline import run_channel_topic_pipeline

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

        transcript_sec = (
            args.transcript_seconds
            if args.transcript_seconds is not None
            else TRANSCRIPT_MAX_SECONDS
        )
        transcript_max_seconds = None if args.full_transcript else float(transcript_sec)

        print("=== Step 1: Channel topic + transcript ===")
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

        topic_text = (step1.chosen_video_title or "").strip()
        context_text = (step1.first_minute_transcript or "").strip()
    else:
        if args.context_file is not None:
            context_text = Path(args.context_file).read_text(encoding="utf-8").strip()
        elif args.context is not None:
            context_text = args.context.strip()

    if not topic_text:
        parser.error("Pass --topic (or use --channel to auto-fill topic).")
    if not context_text:
        parser.error("Pass --context or --context-file (or use --channel to auto-fill context).")

    print("\n=== Step 2: Build narrative prompt (.txt) ===")
    result = run_script_pipeline_build_prompt(
        progress=print,
        topic=topic_text,
        context=context_text or "",
        total_parts=args.total_parts,
        output_dir=args.out_dir,
        output_filename=args.out_name,
    )
    if result.success:
        print(f"Prompt written: {result.output_path} ({result.elapsed_sec:.2f} s)")
    else:
        print("Failed to build/write prompt.")
        if result.error_message:
            print(f"  Error: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()

