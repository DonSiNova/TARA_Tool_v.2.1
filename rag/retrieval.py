# rag/retrieval.py
"""
Retrieval helpers for AutoTARA-RAG.

These functions wrap VectorStore.similarity_search for the different
TARA stages, and provide short text contexts to be included in LLM prompts.

Stages:
- Asset extraction
- Damage scenarios
- Threat scenarios
- Vulnerability & attack paths
- Attack feasibility
- Risk values
"""

from __future__ import annotations

from typing import List

from .vector_store import VectorStore
from models.schemas import Asset, AttackPath


# ---------------------------------------------------------------------------
# Asset-related retrieval
# ---------------------------------------------------------------------------


def get_asset_definition_context(vs: VectorStore, asset: Asset) -> str:
    """
    Retrieve generic asset definitions and examples for ISO/SAE 21434
    and brake/ABS/ESC-related architectures.
    """
    query = (
        f"ISO 21434 asset definitions and examples for {asset.type} "
        f"in brake-by-wire, ABS, ESC systems"
    )
    docs = vs.similarity_search(query, k=6, filters={"source": "STANDARD"})
    context_chunks = []
    for d in docs:
        context_chunks.append(f"# {d.title}\n{d.body}\n")
    return "\n".join(context_chunks)


# ---------------------------------------------------------------------------
# Damage scenarios retrieval
# ---------------------------------------------------------------------------


def get_damage_context(vs: VectorStore, asset: Asset) -> str:
    """
    Retrieve guidance and examples for damage scenarios in ISO 21434 and UNECE R155
    for the given asset type (ECU, Sensor, Network, etc.).
    """
    query = (
        f"Damage scenarios, impact and consequences for {asset.type} in ABS, ESC, "
        f"and brake-by-wire systems, ISO 21434, UNECE R155"
    )
    docs = vs.similarity_search(query, k=8, filters={"source": "STANDARD"})
    context_chunks = []
    for d in docs:
        context_chunks.append(f"# {d.title}\n{d.body}\n")
    return "\n".join(context_chunks)


# ---------------------------------------------------------------------------
# Threat scenarios retrieval
# ---------------------------------------------------------------------------


def get_threat_context(vs: VectorStore, asset: Asset) -> str:
    """
    Retrieve generic threat scenarios and STRIDE patterns for the given asset type.
    """
    query = (
        f"STRIDE-based threat scenarios for {asset.type} in automotive brake-by-wire "
        f"and ABS/ESC architectures"
    )
    docs = vs.similarity_search(query, k=8, filters={"source": "STANDARD"})
    context_chunks = []
    for d in docs:
        context_chunks.append(f"# {d.title}\n{d.body}\n")
    return "\n".join(context_chunks)


# ---------------------------------------------------------------------------
# Vulnerabilities & attack paths retrieval
# ---------------------------------------------------------------------------


def get_vuln_context(vs: VectorStore, asset: Asset, attack_vectors: List[str]) -> str:
    """
    Retrieve vulnerabilities, weaknesses and attack patterns relevant for the asset
    and the given attack vectors.

    This will search across NVD, CWE, CAPEC, ATT&CK and ATM sources.
    """
    sw_names = ", ".join(sc.name for sc in asset.softwareStack) or "embedded software"
    vec_str = ", ".join(attack_vectors) if attack_vectors else "Network, Remote, Physical"

    # We search broadly and let the LLM map relevance.
    query = (
        f"Automotive vulnerabilities and attack patterns affecting {asset.type} with software "
        f"{sw_names} using attack vectors {vec_str}"
    )

    # Pull from all relevant sources
    cve_docs = vs.similarity_search(query, k=10, filters={"source": "NVD"})
    cwe_docs = vs.similarity_search(query, k=5, filters={"source": "CWE"})
    capec_docs = vs.similarity_search(query, k=5, filters={"source": "CAPEC"})
    attck_docs = vs.similarity_search(query, k=5, filters={"source": "ATTCK"})
    atm_docs = vs.similarity_search(query, k=5, filters={"source": "ATM"})

    context_chunks = ["# Vulnerabilities (NVD)\n"]
    for d in cve_docs:
        context_chunks.append(f"## {d.title}\n{d.body}\n")

    context_chunks.append("\n# Weaknesses (CWE)\n")
    for d in cwe_docs:
        context_chunks.append(f"## {d.title}\n{d.body}\n")

    context_chunks.append("\n# Attack Patterns (CAPEC)\n")
    for d in capec_docs:
        context_chunks.append(f"## {d.title}\n{d.body}\n")

    context_chunks.append("\n# ATT&CK Techniques\n")
    for d in attck_docs:
        context_chunks.append(f"## {d.title}\n{d.body}\n")

    context_chunks.append("\n# Automotive Threat Matrix\n")
    for d in atm_docs:
        context_chunks.append(f"## {d.title}\n{d.body}\n")

    return "\n".join(context_chunks)


# ---------------------------------------------------------------------------
# Attack feasibility retrieval
# ---------------------------------------------------------------------------


def get_feasibility_context(vs: VectorStore, attack_paths: List[AttackPath], mapped_cves: List[str]) -> str:
    """
    Retrieve CVE and ATT&CK context for feasibility assessment.

    This is primarily used to reason about Elapsed Time, Specialist Expertise,
    required knowledge, etc.
    """
    cve_list = ", ".join(mapped_cves) if mapped_cves else "N/A"
    query = f"Attack complexity, requirements, and exploitation details for CVEs: {cve_list}"

    cve_docs = vs.similarity_search(query, k=10, filters={"source": "NVD"})
    attck_docs = vs.similarity_search(query, k=8, filters={"source": "ATTCK"})

    context_chunks = ["# NVD Exploitation Details\n"]
    for d in cve_docs:
        context_chunks.append(f"## {d.title}\n{d.body}\n")

    context_chunks.append("\n# ATT&CK Tactics and Techniques\n")
    for d in attck_docs:
        context_chunks.append(f"## {d.title}\n{d.body}\n")

    return "\n".join(context_chunks)


# ---------------------------------------------------------------------------
# Risk values retrieval
# ---------------------------------------------------------------------------


def get_risk_context(vs: VectorStore) -> str:
    """
    Retrieve general ISO/SAE 21434 and UNECE R155 guidance on risk
    determination, impact categories, and attack potential.

    Used when prompting the risk_values stage.
    """
    query = (
        "ISO 21434 risk determination, impact category definition, SFOP and RFOIP "
        "interpretation, and UNECE R155 risk-based CSMS requirements for braking systems"
    )
    docs = vs.similarity_search(query, k=6, filters={"source": "STANDARD"})
    context_chunks = []
    for d in docs:
        context_chunks.append(f"# {d.title}\n{d.body}\n")
    return "\n".join(context_chunks)
