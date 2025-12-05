# scripts/init_rag_data.py
"""
Initializes RAG ingestion:
- NVD CVE dumps
- CWE
- CAPEC
- MITRE ATT&CK
- Automotive Threat Matrix
- Standards text
"""

import os
import json
from tqdm import tqdm
from rag.vector_store import VectorStore, Document
from config.settings import settings
from rag.ingestion import (
    ingest_nvd_dump,
    ingest_cwe,
    ingest_capec,
    ingest_attck,
    ingest_atm,
    ingest_standards,
)

def main():
    print("Initializing vector store...")
    vs = VectorStore(settings.VECTOR_DB_PATH)

    # NVD
    nvd_dir = settings.NVD_DATA_DIR
    if os.path.exists(nvd_dir):
        print("\n[+] Ingesting NVD CVE database...")
        for fname in tqdm(os.listdir(nvd_dir)):
            if fname.endswith(".json") or fname.endswith(".json.gz"):
                ingest_nvd_dump(vs, os.path.join(nvd_dir, fname))

    # CWE
    if os.path.exists(settings.CWE_DATA_PATH):
        print("\n[+] Ingesting CWE catalog...")
        ingest_cwe(vs, settings.CWE_DATA_PATH)

    # CAPEC
    if os.path.exists(settings.CAPEC_DATA_PATH):
        print("\n[+] Ingesting CAPEC attack patterns...")
        ingest_capec(vs, settings.CAPEC_DATA_PATH)

    # MITRE ATT&CK
    if os.path.exists(settings.ATTCK_DATA_PATH):
        print("\n[+] Ingesting MITRE ATT&CK...")
        ingest_attck(vs, settings.ATTCK_DATA_PATH)

    # Automotive Threat Matrix
    if os.path.exists(settings.ATM_DATA_PATH):
        print("\n[+] Ingesting Automotive Threat Matrix...")
        ingest_atm(vs, settings.ATM_DATA_PATH)

    # Standards
    if os.path.exists(settings.STANDARDS_DIR):
        print("\n[+] Ingesting Standards text...")
        ingest_standards(vs, settings.STANDARDS_DIR)

    print("\n[✓] RAG ingestion completed successfully.")

if __name__ == "__main__":
    main()
