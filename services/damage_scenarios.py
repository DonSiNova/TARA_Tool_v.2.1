# services/damage_scenarios.py
"""
Stage 2: Damage Scenarios

- Input:
    assets.csv
- Uses:
    Prompt: 2.damage_scenario.txt
    RAG: damage scenario pattern retrieval.
- Output:
    damage_scenarios.csv
    One record per (asset, cyber_property) combination.
"""

from __future__ import annotations

from typing import List

from models.schemas import Asset, DamageScenario, CyberProperty
from rag.vector_store import VectorStore
from rag import retrieval
from storage.csv_store import CsvRepository, get_damage_csv_path
from llm.client import _call_llm, _load_prompt
from llm import parser, formatting
from config.logging import configure_logging
from storage.run_state import get_run_dir
from storage.id_tags import next_damage_id
from services.asset_utils import load_assets, filter_assets_by_identifier

DAMAGE_COLUMNS = [
    "damageId",
    "assetId",
    "assetTag",
    "cyber_property",
    "one_sentence",
    "raw_llm_output",
    "stakeholder",
    "created_at",
]


def generate_damage_for_asset(
    asset: Asset,
    stakeholder: str,
    vs: VectorStore,
    system_prompt: str,
) -> List[DamageScenario]:
    """
    Generate damage scenarios for all cyber properties of a given asset.
    """
    context = retrieval.get_damage_context(vs, asset)

    # If the asset has no explicit cyber properties, use all 6 extended CIA as default.
    cy_props: List[CyberProperty] = asset.cyberProperties or [
        "Confidentiality",
        "Integrity",
        "Availability",
        "Non-Repudiation",
        "Authenticity",
        "Authorization",
    ]

    scenarios: List[DamageScenario] = []

    for prop in cy_props:
        structured_input = f"""
####
asset = {asset.assetId}
asset_type = {asset.type}
cyber_property = {prop}
stakeholder = {stakeholder}
####
"""
        user_message = formatting.build_prompt_with_context(
            rag_context=context,
            structured_input=structured_input,
        )

        raw_output = _call_llm(system_prompt=system_prompt, user_prompt=user_message)
        one_sentence = parser.extract_between_markers(raw_output, start_marker="!!!!")

        ds = DamageScenario(
            damageId=next_damage_id(),
            assetId=asset.assetId,
            assetTag=asset.assetTag,
            cyber_property=prop,  # type: ignore[arg-type]
            one_sentence=one_sentence,
            raw_llm_output=raw_output,
            stakeholder=stakeholder,  # type: ignore[arg-type]
        )
        scenarios.append(ds)

    return scenarios


def run_damage_stage(asset_id: str | None, stakeholder: str, vs: VectorStore) -> List[DamageScenario]:
    """
    Main entrypoint for Stage 2.

    - Reads assets.csv
    - For each asset (+ each cyber property), calls 2.damage_scenario.txt.
    - Writes damage_scenarios.csv.
    """
    logger = configure_logging(get_run_dir())  # type: ignore[name-defined]

    logger.info(
        "Stage 2: Damage scenarios for asset=%s stakeholder=%s", asset_id, stakeholder
    )
    assets = load_assets()

    asset_tag_filter = None
    if asset_id:
        assets, asset_tag_filter = filter_assets_by_identifier(asset_id, assets)
        if not assets:
            logger.warning("No asset found with identifier=%s; skipping Stage 2", asset_id)
            return []

    logger.info(
        "Loaded %d assets for damage scenario generation (asset_tag=%s)",
        len(assets),
        asset_tag_filter or "ALL",
    )

    system_prompt = _load_prompt("2.damage_scenario.txt")
    all_scenarios: List[DamageScenario] = []

    for asset in assets:
        ds_list = generate_damage_for_asset(asset, stakeholder, vs, system_prompt)
        all_scenarios.extend(ds_list)

    csv_path = get_damage_csv_path()
    repo = CsvRepository(csv_path=csv_path, model_cls=DamageScenario, required_columns=DAMAGE_COLUMNS)

    for ds in all_scenarios:
        repo.append(ds)

    logger.info(
        "Stage 2 complete: %d damage scenarios written to %s",
        len(all_scenarios),
        csv_path,
    )
    return all_scenarios
