# services/attack_feasibility.py
"""
Stage 6: Attack Feasibility

- Input:
    attack_paths.csv
- Uses:
    Prompt: 6.attack_feasibility.txt
    RAG: NVD + ATT&CK exploitation details.
- Output:
    attack_feasibilities.csv
"""

from __future__ import annotations

import uuid
from typing import List

from models.schemas import AttackPath, AttackFeasibility
from rag.vector_store import VectorStore
from rag import retrieval
from storage.csv_store import (
    CsvRepository,
    get_attack_paths_csv_path,
    get_attack_feasibilities_csv_path,
)
from llm.client import _call_llm, _load_prompt
from llm import parser, formatting
from config.logging import configure_logging
from storage.run_state import get_run_dir
from services.asset_utils import resolve_asset_tag


FEAS_COLUMNS = [
    "feasibilityId",
    "threatId",
    "pathId",
    "assetTag",
    "mappedCVE",
    "cwe",
    "elapsedTime_score",
    "specialistExpertise_score",
    "knowledgeOfItem_score",
    "windowOfOpportunity_score",
    "equipmentRequired_score",
    "totalScore",
    "attackPotential",
    "attackFeasibility",
    "raw_llm_output",
]


def _load_attack_paths() -> List[AttackPath]:
    repo = CsvRepository(
        csv_path=get_attack_paths_csv_path(),
        model_cls=AttackPath,
        required_columns=[
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
        ],
    )
    return repo.load_all()


def run_attack_feasibility_stage(
    asset_id: str | None, vs: VectorStore
) -> List[AttackFeasibility]:
    """
    Main entrypoint for Stage 6.

    - Reads attack_paths.csv.
    - For each attack path, calls 6.attack_feasibility.txt.
    - Writes attack_feasibilities.csv.
    """
    logger = configure_logging(get_run_dir())
    logger.info("Stage 6: Attack feasibility for asset=%s", asset_id)

    paths = _load_attack_paths()
    asset_tag_filter = resolve_asset_tag(asset_id)
    if asset_id and not asset_tag_filter:
        logger.warning(
            "No asset found with identifier=%s; skipping Stage 6", asset_id
        )
        return []
    if asset_tag_filter:
        paths = [p for p in paths if p.assetTag == asset_tag_filter]
        if not paths:
            logger.warning(
                "No attack paths found for assetTag=%s; skipping Stage 6",
                asset_tag_filter,
            )
            return []
    logger.info("Loaded %d attack paths", len(paths))

    system_prompt = _load_prompt("6.attack_feasibility.txt")
    csv_path = get_attack_feasibilities_csv_path()
    repo = CsvRepository(
        csv_path=csv_path,
        model_cls=AttackFeasibility,
        required_columns=FEAS_COLUMNS,
    )

    out: List[AttackFeasibility] = []

    for ap in paths:
        # Collect CVEs for feasibility context
        mapped_cves = []
        if ap.cve_id:
            mapped_cves.append(ap.cve_id)
        for vref in ap.vulnerabilities:
            if vref.cve_id:
                mapped_cves.append(vref.cve_id)

        feas_context = retrieval.get_feasibility_context(vs, [ap], mapped_cves)

        structured_input = f"""
####
threatId = {ap.threatId}
threat_scenario = (see associated threat)
attack_paths = ["{ap.pathId}"]
mappedCVE = {mapped_cves}
cwe = [{ap.cwe_id or ""}]
####
"""
        user_prompt = formatting.build_prompt_with_context(
            rag_context=feas_context,
            structured_input=structured_input,
        )
        raw_output = _call_llm(system_prompt, user_prompt)

        try:
            parsed = parser.safe_parse_json(raw_output)
        except Exception as e:
            logger.error("Failed to parse feasibility JSON for pathId=%s: %s", ap.pathId, e)
            continue

        feas = AttackFeasibility(
            feasibilityId=str(uuid.uuid4()),
            threatId=parsed.get("threatId", ap.threatId),
            pathId=ap.pathId,
            assetTag=ap.assetTag,
            mappedCVE=parsed.get("mappedCVE", mapped_cves),
            cwe=parsed.get("cwe", [ap.cwe_id] if ap.cwe_id else []),
            elapsedTime_score=parsed["feasibility"]["elapsedTime"]["score"],
            specialistExpertise_score=parsed["feasibility"]["specialistExpertise"]["score"],
            knowledgeOfItem_score=parsed["feasibility"]["knowledgeOfItem"]["score"],
            windowOfOpportunity_score=parsed["feasibility"]["windowOfOpportunity"]["score"],
            equipmentRequired_score=parsed["feasibility"]["equipmentRequired"]["score"],
            totalScore=parsed["feasibility"]["totalScore"],
            attackPotential=parsed["feasibility"]["attackPotential"],
            attackFeasibility=parsed["feasibility"]["attackFeasibility"],
            raw_llm_output=raw_output,
        )
        repo.append(feas)
        out.append(feas)

    logger.info("Stage 6 complete: %d feasibility records written to %s", len(out), csv_path)
    return out
