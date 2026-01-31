"""Structured logger. Use logging, never print."""

import logging
import sys
from typing import Optional

_LOG_NAME = "automation_intelligence"
_root: Optional[logging.Logger] = None


def get_logger(name: str = _LOG_NAME) -> logging.Logger:
    """Return the project logger. Configured once on first call."""
    global _root
    if _root is None:
        _root = logging.getLogger(_LOG_NAME)
        _root.setLevel(logging.DEBUG)
        if not _root.handlers:
            h = logging.StreamHandler(sys.stderr)
            h.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            _root.addHandler(h)
    return _root
