# llm/parser.py
"""
Parsing helpers for LLM outputs in AutoTARA-RAG.

These utilities help:
- Extract JSON blocks from mixed text.
- Extract sections between custom markers (e.g., !!!!).
- Provide robust fallbacks against minor formatting deviations.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional


JSON_BLOCK_PATTERN = re.compile(
    r"```json\s*(?P<json>{.*?})\s*```",
    re.DOTALL | re.IGNORECASE,
)

GENERIC_JSON_PATTERN = re.compile(
    r"({.*})",
    re.DOTALL,
)


def extract_between_markers(
    text: str,
    start_marker: str = "!!!!",
    end_marker: Optional[str] = None,
) -> str:
    """
    Extract text between two identical or two different markers.

    Default: between the first and second '!!!!'.

    If end_marker is None, the same marker is used for start and end.
    """
    if end_marker is None:
        end_marker = start_marker

    start_idx = text.find(start_marker)
    if start_idx == -1:
        return text.strip()

    start_idx += len(start_marker)
    end_idx = text.find(end_marker, start_idx)
    if end_idx == -1:
        # no closing marker → take until end
        return text[start_idx:].strip()

    return text[start_idx:end_idx].strip()


def extract_json_block(text: str) -> Dict[str, Any]:
    """
    Attempt to extract a JSON object from the given text.

    Strategy:
    1. Look for ```json ... ``` fenced code block.
    2. Look for the first {...} using a generic regex.
    3. If text itself parses as JSON, use it.
    4. If still failing, raise ValueError.
    """
    # 1. JSON fenced block
    match = JSON_BLOCK_PATTERN.search(text)
    if match:
        raw_json = match.group("json")
        try:
            return json.loads(raw_json)
        except Exception:
            pass

    # 2. Generic { ... } block
    match2 = GENERIC_JSON_PATTERN.search(text)
    if match2:
        raw_json = match2.group(1)
        try:
            return json.loads(raw_json)
        except Exception:
            pass

    # 3. Entire text as JSON
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except Exception:
        pass

    raise ValueError("Could not extract a valid JSON block from LLM output.")


def safe_parse_json(
    text: str,
    default: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Safely parse JSON using extract_json_block. On failure, return default
    (or raise if default is None).
    """
    try:
        return extract_json_block(text)
    except Exception:
        if default is not None:
            return default
        raise
