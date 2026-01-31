"""Step 2: Build the narrative prompt and save it to a .txt file in output/."""

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from automation_intelligence.logging.logger import get_logger
from automation_intelligence.prompts.narrative_master_prompt import build_narrative_prompt

logger = get_logger(__name__)


def _noop_progress(_msg: str) -> None:
    pass


def _slugify_filename(text: str, *, max_len: int = 80) -> str:
    """Create a filesystem-friendly slug for filenames."""
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9 _-]+", "", t)
    t = t.replace(" ", "_").strip("_-")
    if not t:
        t = "prompt"
    return t[:max_len]


@dataclass
class ScriptPromptResult:
    """Result of building and saving the narrative prompt."""

    success: bool
    elapsed_sec: float
    output_path: str = ""
    error_message: str = ""


def run_script_pipeline_build_prompt(
    *,
    progress: Callable[[str], None] | None = None,
    topic: str,
    context: str,
    total_parts: int | None = None,
    output_dir: str | Path | None = None,
    output_filename: str | None = None,
) -> ScriptPromptResult:
    """Build narrative prompt (topic + context) and write it to output_dir/output_filename.

    By default, writes to PROJECT_ROOT/output/<timestamp>_<topic>.txt.
    total_parts defaults to settings TOTAL_PARTS (.env total_parts).
    """
    start = time.perf_counter()
    out = progress if progress is not None else _noop_progress

    topic = (topic or "").strip()
    context = (context or "").strip()
    if not topic or not context:
        msg = "Both topic and context are required to build the prompt."
        elapsed = time.perf_counter() - start
        return ScriptPromptResult(success=False, elapsed_sec=round(elapsed, 2), error_message=msg)

    from automation_intelligence.config.settings import PROJECT_ROOT, TOTAL_PARTS as DEFAULT_TOTAL_PARTS

    parts = total_parts if total_parts is not None else DEFAULT_TOTAL_PARTS
    prompt_text = build_narrative_prompt(topic, context, parts)
    out("Prompt built. Writing to output file...")

    out_dir = Path(output_dir) if output_dir is not None else (PROJECT_ROOT / "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    if output_filename:
        name = output_filename
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{ts}_{_slugify_filename(topic)}.txt"

    out_path = (out_dir / name).resolve()
    out_path.write_text(prompt_text, encoding="utf-8")

    elapsed = time.perf_counter() - start
    logger.info(
        "Prompt written",
        extra={"output_path": str(out_path), "topic_len": len(topic), "context_len": len(context), "parts": parts},
    )
    return ScriptPromptResult(success=True, elapsed_sec=round(elapsed, 2), output_path=str(out_path))
