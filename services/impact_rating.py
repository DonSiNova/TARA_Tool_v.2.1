# services/impact_rating.py
"""
Stage 3: Impact Rating

- Input:
    damage_scenarios.csv
- Uses:
    Prompt: 4.impact_rating.txt
    RAG: risk & impact scale context.
- Output:
    impact_rating.csv
"""

from __future__ import annotations

from typing import Dict, List

from models.schemas import DamageScenario, ImpactRating
from rag.vector_store import VectorStore
from rag.retrieval import get_risk_context
from storage.csv_store import CsvRepository, get_damage_csv_path, get_impact_csv_path
from llm.client import _call_llm, _load_prompt
from llm import parser, formatting
from config.logging import configure_logging
from storage.run_state import get_run_dir
from storage.id_tags import next_impact_id
from services.asset_utils import resolve_asset_tag


IMPACT_COLUMNS = [
    "impactId",
    "damageId",
    "assetTag",
    "stakeholder",
    "road_user_sfop",
    "oem_rfoip",
    "raw_llm_output",
]


def _load_damage_scenarios() -> List[DamageScenario]:
    csv_path = get_damage_csv_path()
    repo = CsvRepository(
        csv_path=csv_path,
        model_cls=DamageScenario,
        required_columns=[
            "damageId",
            "assetId",
            "assetTag",
            "cyber_property",
            "one_sentence",
            "raw_llm_output",
            "stakeholder",
            "created_at",
        ],
    )
    return repo.load_all()


def run_impact_stage(
    asset_id: str | None, vs: VectorStore
) -> List[ImpactRating]:
    """
    Main entrypoint for Stage 3.

    - Reads damage_scenarios.csv
    - Calls impact rating prompt for each damage scenario.
    - Writes impact_rating.csv
    """
    logger = configure_logging(get_run_dir())
    logger.info(
        "Stage 3: Impact rating for asset=%s (Road User + OEM)", asset_id
    )

    damage_scenarios = _load_damage_scenarios()
    asset_tag_filter = resolve_asset_tag(asset_id)
    if asset_id and not asset_tag_filter:
        logger.warning("No asset found with identifier=%s; skipping Stage 3", asset_id)
        return []
    if asset_tag_filter:
        damage_scenarios = [ds for ds in damage_scenarios if ds.assetTag == asset_tag_filter]
        if not damage_scenarios:
            logger.warning(
                "No damage scenarios found for assetTag=%s; skipping Stage 3",
                asset_tag_filter,
            )
            return []
    logger.info("Loaded %d damage scenarios", len(damage_scenarios))

    system_prompt = _load_prompt("4.impact_rating.txt")
    risk_context = get_risk_context(vs)
    repo = CsvRepository(csv_path=get_impact_csv_path(), model_cls=ImpactRating, required_columns=IMPACT_COLUMNS)

    out: List[ImpactRating] = []

    for ds in damage_scenarios:
        structured_input = f"""
####
damageId = {ds.damageId}
assetId = {ds.assetId}
stakeholder = Road User and OEM
damage_scenario = {ds.one_sentence}
####
"""
        user_prompt = formatting.build_prompt_with_context(
            rag_context=risk_context,
            structured_input=structured_input,
        )
        raw_output = _call_llm(system_prompt, user_prompt)

        try:
            parsed: Dict = parser.safe_parse_json(raw_output)
        except Exception as e:
            logger.error("Failed to parse impact rating JSON for damageId=%s: %s", ds.damageId, e)
            continue

        impact = ImpactRating(
            impactId=next_impact_id(),
            damageId=ds.damageId,
            assetTag=ds.assetTag,
            stakeholder=parsed.get("stakeholder", "Both"),
            road_user_sfop=parsed.get("road_user_sfop"),
            oem_rfoip=parsed.get("oem_rfoip"),
            raw_llm_output=raw_output,
        )
        repo.append(impact)
        out.append(impact)

    logger.info("Stage 3 complete: %d impact ratings written", len(out))
    return out
