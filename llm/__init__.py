# llm/__init__.py
"""
LLM integration layer for AutoTARA-RAG.

Provides:
- Low-level LLM call helper (_call_llm)
- Stage-specific generator functions:
    - generate_assets_from_sysml
- Parsing helpers (via llm.parser)
- Formatting helpers (via llm.formatting)
"""

from .client import _call_llm, generate_assets_from_sysml  # noqa: F401
from . import parser  # noqa: F401
from . import formatting  # noqa: F401
