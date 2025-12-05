# llm/formatting.py
"""
Formatting helpers for constructing LLM prompts and handling user feedback
in AutoTARA-RAG.

These utilities are used by the services and UI layers to:
- Combine RAG context with structured input sections.
- Append user feedback (Modify flows) into the prompt in a consistent way.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def build_prompt_with_context(
    rag_context: str,
    structured_input: str,
    extra_instructions: Optional[str] = None,
) -> str:
    """
    Combine a RAG context block, a structured input block (e.g. #### asset=...),
    and optional extra instructions into a single user message string.
    """
    parts = []

    if rag_context:
        parts.append("RAG CONTEXT:\n")
        parts.append(rag_context.strip())
        parts.append("\n\n")

    if extra_instructions:
        parts.append("EXTRA INSTRUCTIONS:\n")
        parts.append(extra_instructions.strip())
        parts.append("\n\n")

    parts.append("INPUT:\n")
    parts.append(structured_input.strip())
    parts.append("\n")

    return "".join(parts)


def inject_user_feedback(
    original_structured_input: str,
    user_feedback: str,
    optional_file_content: Optional[str] = None,
) -> str:
    """
    Extend the structured input with user feedback for Modify flows.

    This is used when the user chooses "Modify" in the UI and provides:
    - Natural language feedback.
    - Optional uploaded file content to override or refine the previous
      generation.

    Returns a new structured input string, ready to pass to the LLM.
    """
    segments = [
        original_structured_input.strip(),
        "\n\n# USER FEEDBACK:\n",
        user_feedback.strip(),
        "\n",
    ]

    if optional_file_content:
        segments.append("\n# USER FILE CONTENT (for reference):\n")
        segments.append(optional_file_content.strip())
        segments.append("\n")

    return "".join(segments)


def format_dict_as_pretty_json(d: Dict[str, Any]) -> str:
    """
    Utility to pretty-print a dict as JSON for including in prompts
    or debug logs.
    """
    return json.dumps(d, indent=2, ensure_ascii=False)
