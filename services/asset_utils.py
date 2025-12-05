# services/asset_utils.py
"""
Shared helpers for working with Asset records stored in assets.csv.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from models.schemas import Asset
from storage.csv_store import CsvRepository, get_assets_csv_path

ASSET_COLUMNS = [
    "assetTag",
    "assetId",
    "itemId",
    "type",
    "description",
    "location",
    "cyberProperties",
    "interfaces",
    "softwareStack",
]


def load_assets() -> List[Asset]:
    repo = CsvRepository(
        csv_path=get_assets_csv_path(),
        model_cls=Asset,
        required_columns=ASSET_COLUMNS,
    )
    return repo.load_all()


def filter_assets_by_identifier(
    asset_identifier: str | None, assets: List[Asset]
) -> Tuple[List[Asset], Optional[str]]:
    """
    Filter assets by either their original assetId or generated assetTag.
    Returns the filtered list and the resolved assetTag (if exactly one matched).
    """
    if not asset_identifier:
        return assets, None

    filtered = [
        asset
        for asset in assets
        if asset.assetId == asset_identifier or asset.assetTag == asset_identifier
    ]
    if filtered:
        return filtered, filtered[0].assetTag
    return [], None


def resolve_asset_tag(asset_identifier: str | None) -> Optional[str]:
    assets = load_assets()
    _, tag = filter_assets_by_identifier(asset_identifier, assets)
    return tag
