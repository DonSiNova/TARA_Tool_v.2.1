# services/vuln_attack_paths.py
"""
Stage 5: Vulnerability Analysis & Attack Paths

- Input:
    threat_scenarios.csv
- Uses:
    Prompt: 5.vulnerability_attackpath.txt
    RAG: NVD, CWE, CAPEC, ATT&CK, ATM.
- Output:
    attack_paths.csv
"""

from __future__ import annotations

from typing import Any, Dict, List

from models.schemas import (
    ThreatScenario,
    AttackPath,
    VulnerabilityRef,
)
from rag.vector_store import VectorStore
from rag import retrieval
from storage.csv_store import (
    CsvRepository,
    get_threat_csv_path,
    get_attack_paths_csv_path,
)
from llm.client import _call_llm, _load_prompt
from llm import parser, formatting
from config.logging import configure_logging
from storage.run_state import get_run_dir
from storage.id_tags import next_attack_path_id
from services.asset_utils import load_assets, filter_assets_by_identifier


ATTACK_PATH_COLUMNS = [
    "pathId",
    "threatId",
    "assetId",
    "assetTag",
    "damageId",
    "vulnerabilities",
    "entry_vector",
    "backing",
    "cve_id",
    "cwe_id",
    "attck_techniques",
    "capec_ids",
    "atm_ids",
    "steps",
    "raw_llm_output",
]


def _load_threats() -> List[ThreatScenario]:
    repo = CsvRepository(
        csv_path=get_threat_csv_path(),
        model_cls=ThreatScenario,
        required_columns=[
            "threatId",
            "damageId",
            "assetId",
            "assetTag",
            "cyber_property",
            "one_sentence",
            "attack_vectors",
            "raw_llm_output",
        ],
    )
    return repo.load_all()


def _build_vuln_refs(vuln_list: List[Dict[str, Any]]) -> List[VulnerabilityRef]:
    """
    Convert parsed vulnerability entries from LLM JSON into VulnerabilityRef models.
    """
    out: List[VulnerabilityRef] = []
    for v in vuln_list:
        try:
            ref = VulnerabilityRef(
                backing=v.get("backing", "potential_generated"),
                cve_id=v.get("cve_id"),
                cwe_id=v.get("cwe_id"),
                component=v.get("component", ""),
                cpe_candidates=v.get("cpe_candidates", []),
                weakness_family=v.get("weakness_family", ""),
                attack_vectors=v.get("attack_vectors", []),
            )
            out.append(ref)
        except Exception:
            continue
    return out


def run_vuln_attack_paths_stage(asset_id: str | None, vs: VectorStore) -> List[AttackPath]:
    """
    Main entrypoint for Stage 5.

    - Reads threat_scenarios.csv and assets.csv.
    - For each threat scenario, uses RAG to pull NVD/CWE/CAPEC/ATT&CK/ATM.
    - Calls 5.vulnerability_attackpath.txt to generate attack paths.
    - Writes attack_paths.csv.
    """
    logger = configure_logging(get_run_dir())
    logger.info("Stage 5: Vulnerability analysis & attack paths for asset=%s", asset_id)

    threats = _load_threats()
    assets = load_assets()

    assets, asset_tag_filter = filter_assets_by_identifier(asset_id, assets)
    if asset_id and not assets:
        logger.warning(
            "No asset found for identifier=%s; skipping Stage 5", asset_id
        )
        return []
    if asset_tag_filter:
        threats = [t for t in threats if t.assetTag == asset_tag_filter]
        if not threats:
            logger.warning(
                "No threats found for assetTag=%s; skipping Stage 5", asset_tag_filter
            )
            return []

    asset_by_id = {a.assetId: a for a in assets}

    logger.info("Loaded %d threats and %d assets", len(threats), len(assets))

    system_prompt = _load_prompt("5.vulnerability_attackpath.txt")
    csv_path = get_attack_paths_csv_path()
    repo = CsvRepository(
        csv_path=csv_path,
        model_cls=AttackPath,
        required_columns=ATTACK_PATH_COLUMNS,
    )

    out: List[AttackPath] = []

    for t in threats:
        asset = asset_by_id.get(t.assetId)
        if not asset:
            logger.warning("No asset found for threatId=%s assetId=%s", t.threatId, t.assetId)
            continue

        vuln_context = retrieval.get_vuln_context(vs, asset, t.attack_vectors)

        structured_input = f"""
####
threatId = {t.threatId}
assetId = {t.assetId}
damageId = {t.damageId}
threat_scenario = {t.one_sentence}
attack_vectors = {t.attack_vectors}
####
"""
        user_prompt = formatting.build_prompt_with_context(
            rag_context=vuln_context,
            structured_input=structured_input,
        )
        raw_output = _call_llm(system_prompt, user_prompt)

        try:
            parsed = parser.safe_parse_json(raw_output)
        except Exception as e:
            logger.error("Failed to parse attack path JSON for threatId=%s: %s", t.threatId, e)
            continue

        # LLM may produce single or multiple paths; support both.
        paths_data = parsed.get("attack_paths") or [parsed]

        for pd in paths_data:
            vulnerabilities = _build_vuln_refs(pd.get("vulnerabilities", []))
            path = AttackPath(
                pathId=next_attack_path_id(),
                threatId=t.threatId,
                assetId=t.assetId,
                assetTag=t.assetTag,
                damageId=t.damageId,
                vulnerabilities=vulnerabilities,
                entry_vector=pd.get("entry_vector", ""),
                backing=pd.get("backing", "potential_generated"),
                cve_id=pd.get("cve_id"),
                cwe_id=pd.get("cwe_id"),
                attck_techniques=pd.get("attck_techniques", []),
                capec_ids=pd.get("capec_ids", []),
                atm_ids=pd.get("atm_ids", []),
                steps=pd.get("steps", []),
                raw_llm_output=raw_output,
            )
            repo.append(path)
            out.append(path)

    logger.info("Stage 5 complete: %d attack paths written to %s", len(out), csv_path)
    return out
