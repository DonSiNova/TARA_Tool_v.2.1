# storage/run_state.py
"""
Track the active timestamped output directory for TARA runs.

Each Stage 1 execution should start a fresh run directory inside the base
OUTPUT_DIR to ensure previous CSV evidence is preserved. Subsequent stages
operate on the currently active run directory.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from config.settings import settings

_current_run_dir: Optional[str] = None


def _base_dir() -> str:
    base = settings.OUTPUT_DIR
    os.makedirs(base, exist_ok=True)
    return base


def _latest_existing_run_dir() -> Optional[str]:
    base = _base_dir()
    candidates = [
        name
        for name in os.listdir(base)
        if os.path.isdir(os.path.join(base, name))
    ]
    run_dirs = sorted((c for c in candidates if c.startswith("run_")), reverse=True)
    if run_dirs:
        return os.path.join(base, run_dirs[0])

    legacy_files = any(
        os.path.isfile(os.path.join(base, entry)) for entry in os.listdir(base)
    )
    if legacy_files:
        return base
    return None


def _create_run_dir() -> str:
    base = _base_dir()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(base, f"run_{timestamp}")
    os.makedirs(path, exist_ok=True)
    return path


def _is_empty_dir(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    return not any(os.scandir(path))


def get_run_dir() -> str:
    """
    Return the active run directory. If none exists yet, use the latest
    timestamped directory, falling back to a newly created run.
    """
    global _current_run_dir
    if not _current_run_dir:
        existing = _latest_existing_run_dir()
        _current_run_dir = existing or _base_dir()
    return _current_run_dir


def start_new_run(force: bool = True) -> str:
    """
    Create and activate a new timestamped run directory. If force is False
    and the current run directory is an empty timestamped folder, reuse it.
    """
    global _current_run_dir
    if (
        not force
        and _current_run_dir
        and os.path.basename(_current_run_dir).startswith("run_")
        and _is_empty_dir(_current_run_dir)
    ):
        return _current_run_dir

    _current_run_dir = _create_run_dir()
    return _current_run_dir
