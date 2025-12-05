# rag/ingestion.py
"""
Ingestion utilities for AutoTARA-RAG RAG layer.

These functions read local data dumps and insert them as Documents
into the VectorStore:

- ingest_nvd_dump :
    NVD CVE JSON (or JSON.GZ) from NVD feeds.
- ingest_cwe :
    CWE JSON export.
- ingest_capec :
    CAPEC JSON export.
- ingest_attck :
    MITRE ATT&CK Enterprise JSON/STIX export.
- ingest_atm :
    Automotive Threat Matrix mapping file (JSON).
- ingest_standards :
    Local text/markdown files for ISO/SAE 21434, UNECE R155, etc.

The exact schemas of the input files may vary slightly depending on
download source; this code is robust and uses try/except to avoid crashes.
"""

from __future__ import annotations

import gzip
import json
import os
from typing import List

from .vector_store import Document, VectorStore


# ---------------------------------------------------------------------------
# NVD CVE ingestion
# ---------------------------------------------------------------------------


def ingest_nvd_dump(vs: VectorStore, path: str) -> None:
    """
    Ingest an NVD CVE dump file (JSON or JSON.GZ).

    Expected structure (simplified typical NVD JSON):
    {
      "CVE_Items": [
        {
          "cve": {
            "CVE_data_meta": {"ID": "CVE-XXXX-YYYY"},
            "description": {"description_data": [{"value": "..."}]},
            ...
          },
          ...
        },
        ...
      ]
    }
    """
    if not os.path.exists(path):
        return

    print(f"[RAG] ingest_nvd_dump: {path}")

    # Open JSON or GZ
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    items = data.get("CVE_Items", [])
    docs: List[Document] = []

    for item in items:
        try:
            cve_obj = item.get("cve", {})
            meta = cve_obj.get("CVE_data_meta", {})
            cve_id = meta.get("ID")
            if not cve_id:
                continue

            desc_data = cve_obj.get("description", {}).get("description_data", [])
            description = ""
            if desc_data:
                description = desc_data[0].get("value", "")

            title = f"CVE {cve_id}"
            metadata = {"cve_id": cve_id, "source_feed": os.path.basename(path)}

            docs.append(
                Document(
                    id=cve_id,
                    source="NVD",
                    type="CVE",
                    title=title,
                    body=description,
                    metadata=metadata,
                )
            )
        except Exception:
            # Skip malformed entries without stopping ingestion
            continue

    if docs:
        vs.add_documents(docs)


# ---------------------------------------------------------------------------
# CWE ingestion
# ---------------------------------------------------------------------------


def ingest_cwe(vs: VectorStore, path: str) -> None:
    """
    Ingest CWE catalog from JSON.

    Expected structure (simplified):
    {
      "Weaknesses": [
        {
          "ID": "CWE-79",
          "Name": "Improper Neutralization of Input During Web Page Generation",
          "Description": "..."
        },
        ...
      ]
    }
    """
    if not os.path.exists(path):
        return

    print(f"[RAG] ingest_cwe: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    weaknesses = data.get("Weaknesses", [])
    docs: List[Document] = []

    for w in weaknesses:
        try:
            cwe_id = w.get("ID")
            if not cwe_id:
                continue
            name = w.get("Name", "")
            desc = w.get("Description", "")

            title = f"CWE {cwe_id}: {name}"
            metadata = {"cwe_id": cwe_id}

            docs.append(
                Document(
                    id=cwe_id,
                    source="CWE",
                    type="CWE",
                    title=title,
                    body=desc,
                    metadata=metadata,
                )
            )
        except Exception:
            continue

    if docs:
        vs.add_documents(docs)


# ---------------------------------------------------------------------------
# CAPEC ingestion
# ---------------------------------------------------------------------------


def ingest_capec(vs: VectorStore, path: str) -> None:
    """
    Ingest CAPEC attack patterns from JSON.

    Expected structure (simplified):
    {
      "Attack_Patterns": [
        {
          "ID": "CAPEC-123",
          "Name": "Example Attack",
          "Description": "..."
        },
        ...
      ]
    }
    """
    if not os.path.exists(path):
        return

    print(f"[RAG] ingest_capec: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    patterns = data.get("Attack_Patterns", [])
    docs: List[Document] = []

    for p in patterns:
        try:
            capec_id = p.get("ID")
            if not capec_id:
                continue
            name = p.get("Name", "")
            desc = p.get("Description", "")

            title = f"CAPEC {capec_id}: {name}"
            metadata = {"capec_id": capec_id}

            docs.append(
                Document(
                    id=capec_id,
                    source="CAPEC",
                    type="CAPEC",
                    title=title,
                    body=desc,
                    metadata=metadata,
                )
            )
        except Exception:
            continue

    if docs:
        vs.add_documents(docs)


# ---------------------------------------------------------------------------
# MITRE ATT&CK ingestion
# ---------------------------------------------------------------------------


def ingest_attck(vs: VectorStore, path: str) -> None:
    """
    Ingest MITRE ATT&CK techniques from JSON/STIX.

    This function expects a structure with a top-level 'objects' array
    containing technique-like entries (STIX 2.x export).

    For each object where 'type' is 'attack-pattern' and external_references
    contain a 'mitre-attack' ID, it creates a Document.
    """
    if not os.path.exists(path):
        return

    print(f"[RAG] ingest_attck: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    objects = data.get("objects", [])
    docs: List[Document] = []

    for obj in objects:
        try:
            if obj.get("type") != "attack-pattern":
                continue

            name = obj.get("name", "")
            description = obj.get("description", "")

            attack_id = None
            for ref in obj.get("external_references", []):
                if "mitre-attack" in ref.get("source_name", ""):
                    attack_id = ref.get("external_id")
                    break

            if not attack_id:
                continue

            title = f"ATT&CK {attack_id}: {name}"
            metadata = {"attack_id": attack_id, "tactic": obj.get("x_mitre_tactic_type")}

            docs.append(
                Document(
                    id=attack_id,
                    source="ATTCK",
                    type="TECHNIQUE",
                    title=title,
                    body=description or "",
                    metadata=metadata,
                )
            )
        except Exception:
            continue

    if docs:
        vs.add_documents(docs)


# ---------------------------------------------------------------------------
# Automotive Threat Matrix ingestion
# ---------------------------------------------------------------------------


def ingest_atm(vs: VectorStore, path: str) -> None:
    """
    Ingest Automotive Threat Matrix entries.

    Expected structure (simplified):
    {
      "threats": [
        {
          "id": "ATM-001",
          "category": "Telematics remote exploit",
          "description": "..."
        },
        ...
      ]
    }
    """
    if not os.path.exists(path):
        return

    print(f"[RAG] ingest_atm: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    threats = data.get("threats", [])
    docs: List[Document] = []

    for t in threats:
        try:
            atm_id = t.get("id")
            if not atm_id:
                continue
            category = t.get("category", "")
            desc = t.get("description", "")

            title = f"ATM {atm_id}: {category}"
            metadata = {"atm_id": atm_id, "category": category}

            docs.append(
                Document(
                    id=atm_id,
                    source="ATM",
                    type="AUTOMOTIVE_THREAT",
                    title=title,
                    body=desc or "",
                    metadata=metadata,
                )
            )
        except Exception:
            continue

    if docs:
        vs.add_documents(docs)


# ---------------------------------------------------------------------------
# Standards ingestion (ISO/SAE 21434, UNECE R155, etc.)
# ---------------------------------------------------------------------------


def ingest_standards(vs: VectorStore, directory: str) -> None:
    """
    Ingest standards text files (markdown or text) from a directory.

    For each *.md or *.txt file, we create one Document per file.
    We treat the entire file as a single text chunk for simplicity.
    """

    if not os.path.isdir(directory):
        return

    print(f"[RAG] ingest_standards: {directory}")

    docs: List[Document] = []

    for fname in os.listdir(directory):
        if not (fname.endswith(".md") or fname.endswith(".txt")):
            continue

        path = os.path.join(directory, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        title = f"Standard: {fname}"
        metadata = {"filename": fname}

        docs.append(
            Document(
                id=fname,
                source="STANDARD",
                type="TEXT",
                title=title,
                body=content,
                metadata=metadata,
            )
        )

    if docs:
        vs.add_documents(docs)
