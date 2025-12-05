# services/risk_values.py
"""
Stage 7: Risk Values & Risk Matrix

- Input:
    impact_rating.csv
    attack_feasibilities.csv
    threat_scenarios.csv
- Uses:
    Prompt: 7.Risk_values.txt
    RAG: risk & impact guidance.
- Output:
    risk_values.csv
"""

from __future__ import annotations

import uuid
from typing import Dict, List

from models.schemas import (
    ImpactRating,
    AttackFeasibility,
    ThreatScenario,
    RiskValue,
)
from rag.vector_store import VectorStore
from rag.retrieval import get_risk_context
from storage.csv_store import (
    CsvRepository,
    get_impact_csv_path,
    get_attack_feasibilities_csv_path,
    get_threat_csv_path,
    get_risk_values_csv_path,
)
from llm.client import _call_llm, _load_prompt
from llm import parser, formatting
from config.logging import configure_logging
from storage.run_state import get_run_dir
from services.normalization import normalize
from services.asset_utils import resolve_asset_tag


RISK_COLUMNS = [
    "riskId",
    "threatId",
    "assetTag",
    "stakeholder",
    "impactCategory",
    "attackPotential",
    "riskValue",
    "justification",
]


def _load_impacts() -> List[ImpactRating]:
    repo = CsvRepository(
        csv_path=get_impact_csv_path(),
        model_cls=ImpactRating,
        required_columns=[
            "impactId",
            "damageId",
            "assetTag",
            "stakeholder",
            "road_user_sfop",
            "oem_rfoip",
            "raw_llm_output",
        ],
    )
    return repo.load_all()


def _load_feasibilities() -> List[AttackFeasibility]:
    repo = CsvRepository(
        csv_path=get_attack_feasibilities_csv_path(),
        model_cls=AttackFeasibility,
        required_columns=[
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
        ],
    )
    return repo.load_all()


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


def run_risk_values_stage(
    asset_id: str | None, stakeholder: str, vs: VectorStore
) -> List[RiskValue]:
    """
    Main entrypoint for Stage 7.

    - Reads impact_rating.csv, attack_feasibilities.csv, threat_scenarios.csv.
    - For each threat (and stakeholder), invokes 7.Risk_values.txt.
    - Writes risk_values.csv.
    """
    logger = configure_logging(get_run_dir())
    logger.info(
        "Stage 7: Risk value calculation for asset=%s stakeholder=%s",
        asset_id,
        stakeholder,
    )

    impacts = _load_impacts()
    feasibilities = _load_feasibilities()
    threats = _load_threats()

    asset_tag_filter = resolve_asset_tag(asset_id)
    if asset_id and not asset_tag_filter:
        logger.warning(
            "No asset found with identifier=%s; skipping Stage 7", asset_id
        )
        return []
    if asset_tag_filter:
        threats = [t for t in threats if t.assetTag == asset_tag_filter]
        threat_ids = {t.threatId for t in threats}
        damage_ids = {t.damageId for t in threats}
        impacts = [imp for imp in impacts if imp.damageId in damage_ids]
        feasibilities = [f for f in feasibilities if f.threatId in threat_ids]
        if not threats or not impacts or not feasibilities:
            logger.warning(
                "Missing inputs for assetTag=%s; skipping Stage 7", asset_tag_filter
            )
            return []

    logger.info(
        "Loaded %d impacts, %d feasibilities, %d threats",
        len(impacts),
        len(feasibilities),
        len(threats),
    )

    system_prompt = _load_prompt("7.Risk_values.txt")
    risk_context = get_risk_context(vs)
    csv_path = get_risk_values_csv_path()
    repo = CsvRepository(
        csv_path=csv_path,
        model_cls=RiskValue,
        required_columns=RISK_COLUMNS,
    )

    out: List[RiskValue] = []

    # For simplicity we assume mapping ImpactRating ↔ AttackFeasibility via threatId
    feas_by_threat: Dict[str, AttackFeasibility] = {}
    for f in feasibilities:
        feas_by_threat[f.threatId] = f

    for imp in impacts:
        # We need threatId for this damageId; naive approach: search threats with same damageId
        relevant_threats = [t for t in threats if t.damageId == imp.damageId]
        if not relevant_threats:
            continue

        for t in relevant_threats:
            feas = feas_by_threat.get(t.threatId)
            if not feas:
                logger.warning("No feasibility found for threatId=%s", t.threatId)
                continue

            if stakeholder == "Road User":
                impact_scores = imp.road_user_sfop
            else:
                impact_scores = imp.oem_rfoip

            if impact_scores is None:
                logger.warning(
                    "No impact scores for stakeholder=%s, damageId=%s",
                    stakeholder,
                    imp.damageId,
                )
                continue

            attack_potential_value = normalize("attackPotential", feas.attackFeasibility)

            structured_input = f"""
####
threatId = {t.threatId}
stakeholder = {stakeholder}
impact_scores = {impact_scores}
attack_potential = "{attack_potential_value}"
####
"""
            user_prompt = formatting.build_prompt_with_context(
                rag_context=risk_context,
                structured_input=structured_input,
            )
            raw_output = _call_llm(system_prompt, user_prompt)

            try:
                parsed = parser.safe_parse_json(raw_output)
            except Exception as e:
                logger.error("Failed to parse risk JSON for threatId=%s: %s", t.threatId, e)
                continue

            normalized_attack_potential = normalize(
                "attackPotential", parsed["attackPotential"]
            )

            rv = RiskValue(
                riskId=str(uuid.uuid4()),
                threatId=parsed.get("threatId", t.threatId),
                assetTag=t.assetTag,
                stakeholder=parsed.get("stakeholder", stakeholder),
                impactCategory=parsed["impactCategory"],
                attackPotential=normalized_attack_potential,
                riskValue=parsed["riskValue"],
                justification=parsed["justification"],
            )
            repo.append(rv)
            out.append(rv)

    logger.info("Stage 7 complete: %d risk values written to %s", len(out), csv_path)
    return out
