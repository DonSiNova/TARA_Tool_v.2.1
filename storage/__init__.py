# storage/__init__.py
"""
CSV storage layer for AutoTARA-RAG.

Provides:
- CsvRepository : generic CSV read/write/append wrapper.
- Helper functions for generating file paths for each TARA stage.

All CSV interactions in the services layer go through this module.
"""

from .csv_store import (
    CsvRepository,
    get_assets_csv_path,
    get_damage_csv_path,
    get_impact_csv_path,
    get_threat_csv_path,
    get_attack_paths_csv_path,
    get_attack_feasibilities_csv_path,
    get_risk_values_csv_path,
)
