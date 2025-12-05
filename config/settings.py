# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    NVD_API_KEY: str = os.getenv("NVD_API_KEY", "")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "data/vector_store.index")

    OUTPUT_DIR: str = os.getenv("TARA_OUTPUT_DIR", "output")

    # Paths for RAG ingestion
    NVD_DATA_DIR: str = os.getenv("NVD_DATA_DIR", "data/nvd")
    CWE_DATA_PATH: str = os.getenv("CWE_DATA_PATH", "data/cwe/cwe.json")
    CAPEC_DATA_PATH: str = os.getenv("CAPEC_DATA_PATH", "data/capec/capec.json")
    ATTCK_DATA_PATH: str = os.getenv("ATTCK_DATA_PATH", "data/attck/enterprise-attack.json")
    ATM_DATA_PATH: str = os.getenv("ATM_DATA_PATH", "data/atm/automotive-threat-matrix.json")
    STANDARDS_DIR: str = os.getenv("STANDARDS_DIR", "data/standards")


settings = Settings()
