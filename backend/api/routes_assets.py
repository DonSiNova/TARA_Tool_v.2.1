# api/routes_assets.py
from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, HTTPException

from models.schemas import Asset
from storage.csv_store import CsvRepository, get_assets_csv_path
from services.asset_utils import ASSET_COLUMNS

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("", response_model=List[Asset])
def list_assets() -> List[Asset]:
    """
    Return all assets extracted in Stage 1 so that the UI can
    offer an accurate asset selector.
    """
    csv_path = get_assets_csv_path()
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="assets.csv not found. Run Stage 1 first.")

    repo = CsvRepository(csv_path=csv_path, model_cls=Asset, required_columns=ASSET_COLUMNS)
    return repo.load_all()
