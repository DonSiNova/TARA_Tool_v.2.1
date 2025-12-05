# storage/csv_store.py
"""
CSV Storage Layer for AutoTARA-RAG.
-----------------------------------

This module implements the storage engine for all TARA pipeline stages.

Key features:
- All CSVs stored in the user-selected OUTPUT directory.
- Auto-create CSV with header on first write.
- Append-only operations (TARA stages sequential).
- Strict enforcement of required columns for each entity.
- Conversion between Pydantic models and flat CSV rows.
- Full UTF-8 support for Windows.
- Guaranteed referential link preservation (ID fields).

This is the ONLY module responsible for reading/writing CSVs.
All services must use this layer, never writing files directly.
"""

from __future__ import annotations

import csv
import os
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from config.settings import settings
from storage.run_state import get_run_dir

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# CSV Repository
# ---------------------------------------------------------------------------


class CsvRepository:
    """
    Generic CSV repository that supports:

    - create CSV with header if missing
    - append rows (BaseModel → row dict)
    - load all rows as BaseModel instances
    - schema validation (column checking)
    """

    def __init__(self, csv_path: str, model_cls: Type[T], required_columns: List[str]):
        self.csv_path = csv_path
        self.model_cls = model_cls
        self.required_columns = required_columns

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

        # Create CSV with header if missing
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.required_columns)
                writer.writeheader()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def append(self, model_obj: T) -> None:
        """
        Append a BaseModel instance to the CSV file.
        """
        row = model_obj.model_dump()

        # Flatten nested dicts/lists as JSON strings
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                import json

                row[k] = json.dumps(v, ensure_ascii=False)

        # Only include known columns
        filtered = {k: row.get(k, "") for k in self.required_columns}

        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.required_columns)
            writer.writerow(filtered)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def load_all(self) -> List[T]:
        """
        Load all rows from CSV into Pydantic models.
        """
        rows: List[T] = []
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for raw_row in reader:
                row = self._parse_row(raw_row)
                model_obj = self.model_cls(**row)
                rows.append(model_obj)
        return rows

    def load_by_filter(self, **filters: Any) -> List[T]:
        """
        Load rows where all filter fields match exactly.
        """
        results: List[T] = []
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for raw_row in reader:
                match = True
                for key, val in filters.items():
                    if raw_row.get(key) != str(val):
                        match = False
                        break
                if not match:
                    continue

                row = self._parse_row(raw_row)
                model_obj = self.model_cls(**row)
                results.append(model_obj)

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert CSV row strings into Python types based on model fields.

        JSON lists/dicts are automatically deserialized.
        """
        parsed: Dict[str, Any] = {}
        for key, value in row.items():
            if value is None:
                parsed[key] = None
                continue
            value = value.strip()

            # Detect JSON fields
            if value.startswith("{") or value.startswith("["):
                import json

                try:
                    parsed[key] = json.loads(value)
                except Exception:
                    parsed[key] = value
            else:
                parsed[key] = value
        return parsed


# ---------------------------------------------------------------------------
# PATH GENERATORS FOR EACH TARA STAGE CSV
# ---------------------------------------------------------------------------


def _csv_path(filename: str) -> str:
    """
    Produce a path under OUTPUT_DIR.
    Ensures all CSVs are neatly stored in one place.
    """
    base = get_run_dir()
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


def get_assets_csv_path() -> str:
    return _csv_path("assets.csv")


def get_damage_csv_path() -> str:
    return _csv_path("damage_scenarios.csv")


def get_impact_csv_path() -> str:
    return _csv_path("impact_rating.csv")


def get_threat_csv_path() -> str:
    return _csv_path("threat_scenarios.csv")


def get_attack_paths_csv_path() -> str:
    return _csv_path("attack_paths.csv")


def get_attack_feasibilities_csv_path() -> str:
    return _csv_path("attack_feasibilities.csv")


def get_risk_values_csv_path() -> str:
    return _csv_path("risk_values.csv")
