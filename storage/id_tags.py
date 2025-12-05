# storage/id_tags.py
"""
Sequential ID/tag generator backed by the active run directory.

Each run maintains its own counters inside id_counters.json so that friendly
IDs like A-0001 or DS-0001 never collide across runs.
"""

from __future__ import annotations

import json
import os
from typing import Dict

from storage.run_state import get_run_dir

COUNTER_FILE = "id_counters.json"


def _counter_path() -> str:
    return os.path.join(get_run_dir(), COUNTER_FILE)


def _load_counters() -> Dict[str, int]:
    path = _counter_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {k: int(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _save_counters(counters: Dict[str, int]) -> None:
    path = _counter_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(counters, f, indent=2)


def _next_id(counter_key: str, prefix: str, width: int = 4) -> str:
    counters = _load_counters()
    value = counters.get(counter_key, 0) + 1
    counters[counter_key] = value
    _save_counters(counters)
    return f"{prefix}{value:0{width}d}"


def next_asset_tag() -> str:
    return _next_id("asset", "A-", width=4)


def next_damage_id() -> str:
    return _next_id("damage", "DS-", width=4)


def next_impact_id() -> str:
    return _next_id("impact", "IM-", width=4)


def next_threat_id() -> str:
    return _next_id("threat", "TS-", width=4)


def next_attack_path_id() -> str:
    return _next_id("attack_path", "AP-", width=4)
