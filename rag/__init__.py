# rag/__init__.py
"""
RAG layer for AutoTARA-RAG.

This package provides:
- A FAISS-based VectorStore abstraction (local only).
- Ingestion functions for:
    - NVD (CVE JSON/JSON.GZ)
    - CWE
    - CAPEC
    - MITRE ATT&CK
    - Automotive Threat Matrix (ATM)
    - Standards text
- Retrieval helpers tailored for the TARA stages:
    - Asset extraction
    - Damage scenarios
    - Threat scenarios
    - Vulnerability & attack paths
    - Attack feasibility
    - Risk values
"""

from .vector_store import VectorStore, Document  # noqa: F401
from .ingestion import (  # noqa: F401
    ingest_nvd_dump,
    ingest_cwe,
    ingest_capec,
    ingest_attck,
    ingest_atm,
    ingest_standards,
)
from . import retrieval  # noqa: F401
