# services/threat_scenarios.py
"""
Stage 4: Threat Scenarios

- Input:
    damage_scenarios.csv
- Uses:
    Prompt: 3.threat_scenario.txt
    RAG: threat & STRIDE pattern context.
- Output:
    threat_scenarios.csv
"""

from __future__ import annotations

from typing import List

from models.schemas import DamageScenario, ThreatScenario, Asset
from rag.vector_store import VectorStore
from rag import retrieval
from storage.csv_store import (
    CsvRepository,
    get_damage_csv_path,
    get_threat_csv_path,
)
from llm.client import _call_llm, _load_prompt
from llm import parser, formatting
from config.logging import configure_logging
from storage.run_state import get_run_dir
from storage.id_tags import next_threat_id
from services.asset_utils import load_assets, filter_assets_by_identifier


THREAT_COLUMNS = [
    "threatId",
    "damageId",
    "assetId",
    "assetTag",
    "cyber_property",
    "one_sentence",
    "attack_vectors",
    "raw_llm_output",
]


def _load_damage_scenarios() -> List[DamageScenario]:
    repo = CsvRepository(
        csv_path=get_damage_csv_path(),
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


def run_threat_stage(asset_id: str | None, vs: VectorStore) -> List[ThreatScenario]:
    """
    Main entrypoint for Stage 4.

    - Reads damage_scenarios.csv and assets.csv.
    - For each damage scenario, generates threat scenario(s).
    - Writes threat_scenarios.csv.
    """
    logger = configure_logging(get_run_dir())
    logger.info("Stage 4: Threat scenarios for asset=%s", asset_id)

    damage_scenarios = _load_damage_scenarios()
    assets = load_assets()

    assets, asset_tag_filter = filter_assets_by_identifier(asset_id, assets)
    if asset_id and not assets:
        logger.warning(
            "No asset found for identifier=%s; skipping Stage 4",
            asset_id,
        )
        return []
    if asset_tag_filter:
        damage_scenarios = [ds for ds in damage_scenarios if ds.assetTag == asset_tag_filter]
        if not damage_scenarios:
            logger.warning(
                "No damage scenarios found for assetTag=%s; skipping Stage 4",
                asset_tag_filter,
            )
            return []

    asset_by_id = {a.assetId: a for a in assets}

    logger.info("Loaded %d damage scenarios and %d assets", len(damage_scenarios), len(assets))

    system_prompt = _load_prompt("3.threat_scenario.txt")
    csv_path = get_threat_csv_path()
    repo = CsvRepository(
        csv_path=csv_path,
        model_cls=ThreatScenario,
        required_columns=THREAT_COLUMNS,
    )

    out: List[ThreatScenario] = []

    for ds in damage_scenarios:
        asset = asset_by_id.get(ds.assetId)
        if not asset:
            logger.warning("No asset found for damageId=%s assetId=%s", ds.damageId, ds.assetId)
            continue

        threat_context = retrieval.get_threat_context(vs, asset)

        structured_input = f"""
####
damageId = {ds.damageId}
assetId = {ds.assetId}
cyber_property = {ds.cyber_property}
damage_scenario = {ds.one_sentence}
####
"""
        user_prompt = formatting.build_prompt_with_context(
            rag_context=threat_context,
            structured_input=structured_input,
        )
        raw_output = _call_llm(system_prompt, user_prompt)

        # We expect the final JSON with threatId, one_sentence, attack_vectors etc.
        try:
            parsed = parser.safe_parse_json(raw_output)
        except Exception:
            # fallback: use simple one_sentence between markers
            one_sentence = parser.extract_between_markers(raw_output, start_marker="!!!!")
            ts = ThreatScenario(
                threatId=next_threat_id(),
                damageId=ds.damageId,
                assetId=ds.assetId,
                assetTag=ds.assetTag,
                cyber_property=ds.cyber_property,
                one_sentence=one_sentence,
                attack_vectors=[],
                raw_llm_output=raw_output,
            )
            repo.append(ts)
            out.append(ts)
            continue

        threat = ThreatScenario(
            threatId=next_threat_id(),
            damageId=ds.damageId,
            assetId=ds.assetId,
            assetTag=ds.assetTag,
            cyber_property=parsed.get("cyber_property", ds.cyber_property),
            one_sentence=parsed.get("one_sentence", parsed.get("threat_scenario", "")),
            attack_vectors=parsed.get("attack_vectors", []),
            raw_llm_output=raw_output,
        )
        repo.append(threat)
        out.append(threat)

    logger.info("Stage 4 complete: %d threat scenarios written to %s", len(out), csv_path)
    return out
