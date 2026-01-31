#!/usr/bin/env python3
"""CLI entrypoint: Step 2 - build narrative prompt and save it to output/*.txt."""

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
        description="Step 2: Build narrative prompt (topic + context) and write it to output/*.txt"
    )
    parser.add_argument(
        "--topic",
        metavar="TEXT",
        required=True,
        help="Video title / topic for the narrative prompt.",
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

    context_text: str | None = None
    if args.context_file is not None:
        context_text = Path(args.context_file).read_text(encoding="utf-8").strip()
    elif args.context is not None:
        context_text = args.context.strip()

    if not context_text:
        parser.error("Pass --context or --context-file to build the prompt.")

    result = run_script_pipeline_build_prompt(
        progress=print,
        topic=args.topic.strip(),
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
