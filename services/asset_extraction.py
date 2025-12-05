# services/asset_extraction.py
"""
Stage 1: Initial Analysis / Asset Extraction

- Input:
    SysML JSON file path (as uploaded by user).
- Uses:
    llm.generate_assets_from_sysml + RAG (asset definitions).
    Prompt: 1.asset_register.txt
- Output:
    assets.csv (via CsvRepository)
"""

from __future__ import annotations

import json
from typing import List

from models.schemas import Asset
from rag.vector_store import VectorStore
from storage.csv_store import CsvRepository, get_assets_csv_path
from storage.run_state import get_run_dir
from storage.id_tags import next_asset_tag
from llm.client import generate_assets_from_sysml
from llm import parser
from config.logging import configure_logging
from services.asset_utils import ASSET_COLUMNS


def run_asset_extraction(sysml_json_path: str, vs: VectorStore) -> List[Asset]:
    """
    Main entrypoint for Stage 1.

    - Reads SysML JSON.
    - Calls LLM with 1.asset_register.txt + RAG context.
    - Parses {"assets": [...]} from output.
    - Saves to assets.csv
    - Returns list[Asset].
    """
    logger = configure_logging(get_run_dir())

    logger.info("Stage 1: Asset extraction from SysML (%s)", sysml_json_path)

    with open(sysml_json_path, "r", encoding="utf-8") as f:
        sysml_json = json.load(f)

    raw_output = generate_assets_from_sysml(sysml_json, vs)
    logger.info("Asset extraction LLM call completed, output length=%d", len(raw_output))

    try:
        parsed = parser.safe_parse_json(raw_output)
    except Exception as e:
        logger.error("Failed to parse asset JSON from LLM output: %s", e)
        raise

    assets_data = parsed.get("assets", [])
    assets: List[Asset] = []

    for a in assets_data:
        try:
            asset = Asset(**a)
            asset.assetTag = next_asset_tag()
            assets.append(asset)
        except Exception as e:
            logger.warning("Skipping invalid asset entry from LLM: %s; error=%s", a, e)

    csv_path = get_assets_csv_path()
    repo = CsvRepository(csv_path=csv_path, model_cls=Asset, required_columns=ASSET_COLUMNS)

    for asset in assets:
        repo.append(asset)

    logger.info("Stage 1 complete: %d assets written to %s", len(assets), csv_path)
    return assets
