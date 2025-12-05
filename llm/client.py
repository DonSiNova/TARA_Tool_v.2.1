# llm/client.py
"""
Low-level LLM client utilities for AutoTARA-RAG.

Responsibilities:
- Provide a single, robust _call_llm() helper to talk to OpenAI Chat.
- Provide stage-specific wrappers where helpful (e.g., generate_assets_from_sysml).
- Load prompt templates from the ./prompts directory.

This module is intentionally generic; stage-specific orchestration is done
in the services/ modules, which call _call_llm() with the correct system
and user prompts derived from your TARA prompt chains.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config.settings import settings
from rag.vector_store import VectorStore
from rag import retrieval

# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------

_client = OpenAI(api_key=settings.OPENAI_API_KEY or None)
_MODEL = settings.OPENAI_MODEL or "gpt-4o"


# ---------------------------------------------------------------------------
# Prompt loading helper
# ---------------------------------------------------------------------------


def _prompt_path(filename: str) -> str:
    """
    Resolve a prompt file name under the project-level prompts directory.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "prompts", filename)


def _load_prompt(filename: str) -> str:
    """
    Load a prompt template from the prompts directory.
    """
    path = _prompt_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Core LLM call
# ---------------------------------------------------------------------------


def _call_llm(
    system_prompt: str,
    user_prompt: str,
    extra_messages: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.2,
) -> str:
    """
    Core ChatCompletion call wrapper.

    Args:
        system_prompt: System instruction content (will be first message).
        user_prompt:   User content (the main content we pass).
        extra_messages:
            Optional list of additional messages in chat format:
            [{'role': 'user'/'assistant', 'content': '...'}, ...]
        temperature:
            Sampling temperature.

    Returns:
        String content of the assistant's reply.
    """
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    if extra_messages:
        messages.extend(extra_messages)

    response = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Stage-specific wrapper: Asset extraction from SysML
# ---------------------------------------------------------------------------


def generate_assets_from_sysml(sysml_json: Dict[str, Any], vs: VectorStore) -> str:
    """
    Use the '1.asset_register.txt' prompt plus RAG context to extract assets
    from a SysML JSON model.

    This returns the raw LLM output (expected to be JSON string with
    {"assets":[...]}), which will then be parsed by the asset_extraction service.
    """
    # We don't have an Asset yet, so we pass a dummy asset-like context query.
    # Retrieval here is generic: asset definition, examples, etc.
    from models.schemas import Asset  # imported here to avoid cycles

    dummy_asset = Asset(
        assetId="DUMMY",
        itemId="DUMMY",
        type="ECU",
        description="Dummy ECU for context retrieval only",
        location="",
        cyberProperties=[],
        interfaces=[],
        softwareStack=[],
    )
    context = retrieval.get_asset_definition_context(vs, dummy_asset)

    system_prompt = _load_prompt("1.asset_register.txt")
    user_prompt = f"""
You are given an automotive SysML model in JSON format.

Use the above system instructions and the RAG context below to extract
ALL assets and their attributes from the model.

RAG CONTEXT:
{context}

SYSML MODEL (JSON):
{json.dumps(sysml_json, indent=2, ensure_ascii=False)}
"""

    return _call_llm(system_prompt, user_prompt)
