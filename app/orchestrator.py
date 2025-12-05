# app/orchestrator.py
"""
AutoTARA-RAG Orchestrator

This module coordinates the complete 7-stage TARA pipeline.

It exposes a single class: TARAOrchestrator

Usage (by UI layer):
    orchestrator = TARAOrchestrator()
    orchestrator.run_stage_1(sysml_json_path)
    orchestrator.run_stage_2(asset_id, stakeholder)
    ...
"""

from __future__ import annotations

import os
from typing import List, Optional

from config.settings import settings
from config.logging import configure_logging
from rag.vector_store import VectorStore
from storage.run_state import get_run_dir, start_new_run

from services.asset_extraction import run_asset_extraction
from services.damage_scenarios import run_damage_stage
from services.impact_rating import run_impact_stage
from services.threat_scenarios import run_threat_stage
from services.vuln_attack_paths import run_vuln_attack_paths_stage
from services.attack_feasibility import run_attack_feasibility_stage
from services.risk_values import run_risk_values_stage


class TARAOrchestrator:
    """
    High-level orchestrator for all 7 pipeline stages.
    Ensures consistent access to the VectorStore and output folder.
    """

    def __init__(self, vector_store_path: Optional[str] = None):
        base_output_dir = settings.OUTPUT_DIR
        os.makedirs(base_output_dir, exist_ok=True)
        self.output_dir = get_run_dir()
        self.logger = configure_logging(self.output_dir)

        self.vector_store_path = vector_store_path or settings.VECTOR_DB_PATH
        self.vs = VectorStore(self.vector_store_path)

    # ----------------------------------------------------------------------
    # STAGE 1 — ASSET EXTRACTION
    # ----------------------------------------------------------------------

    def _switch_run_dir(self, directory: str):
        self.output_dir = directory
        self.logger = configure_logging(self.output_dir)

    def run_stage_1(self, sysml_json_path: str, force_new_run: bool = True):
        new_run_dir = start_new_run(force=force_new_run)
        self._switch_run_dir(new_run_dir)
        self.logger.info("=== Stage 1: Asset Extraction ===")
        assets = run_asset_extraction(sysml_json_path, self.vs)
        self.logger.info("Stage 1 finished.")
        return assets

    # ----------------------------------------------------------------------
    # STAGE 2 — DAMAGE SCENARIOS
    # ----------------------------------------------------------------------

    def run_stage_2(self, asset_id: str, stakeholder: str = "Road User"):
        self.logger.info("=== Stage 2: Damage Scenarios ===")
        if not asset_id:
            self.logger.error("Asset ID is required for Stage 2")
            return []
        d = run_damage_stage(asset_id, stakeholder, self.vs)
        self.logger.info("Stage 2 finished.")
        return d

    # ----------------------------------------------------------------------
    # STAGE 3 — IMPACT RATING
    # ----------------------------------------------------------------------

    def run_stage_3(self, asset_id: str):
        self.logger.info("=== Stage 3: Impact Rating ===")
        if not asset_id:
            self.logger.error("Asset ID is required for Stage 3")
            return []
        i = run_impact_stage(asset_id, self.vs)
        self.logger.info("Stage 3 finished.")
        return i

    # ----------------------------------------------------------------------
    # STAGE 4 — THREAT SCENARIOS
    # ----------------------------------------------------------------------

    def run_stage_4(self, asset_id: str):
        self.logger.info("=== Stage 4: Threat Scenarios ===")
        if not asset_id:
            self.logger.error("Asset ID is required for Stage 4")
            return []
        t = run_threat_stage(asset_id, self.vs)
        self.logger.info("Stage 4 finished.")
        return t

    # ----------------------------------------------------------------------
    # STAGE 5 — ATTACK PATHS
    # ----------------------------------------------------------------------

    def run_stage_5(self, asset_id: str):
        self.logger.info("=== Stage 5: Vulnerabilities & Attack Paths ===")
        if not asset_id:
            self.logger.error("Asset ID is required for Stage 5")
            return []
        p = run_vuln_attack_paths_stage(asset_id, self.vs)
        self.logger.info("Stage 5 finished.")
        return p

    # ----------------------------------------------------------------------
    # STAGE 6 — ATTACK FEASIBILITY
    # ----------------------------------------------------------------------

    def run_stage_6(self, asset_id: str):
        self.logger.info("=== Stage 6: Attack Feasibility ===")
        if not asset_id:
            self.logger.error("Asset ID is required for Stage 6")
            return []
        f = run_attack_feasibility_stage(asset_id, self.vs)
        self.logger.info("Stage 6 finished.")
        return f

    # ----------------------------------------------------------------------
    # STAGE 7 — RISK VALUES
    # ----------------------------------------------------------------------

    def run_stage_7(self, asset_id: str, stakeholder: str = "Road User"):
        self.logger.info("=== Stage 7: Risk Values ===")
        if not asset_id:
            self.logger.error("Asset ID is required for Stage 7")
            return []
        r = run_risk_values_stage(asset_id, stakeholder, self.vs)
        self.logger.info("Stage 7 finished.")
        return r
