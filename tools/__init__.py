"""Tools Package.

Contains modular tools for satellite data acquisition, geospatial operations,
and environmental index calculations.
"""

from tools.satellite_data import (
    BoundingBox,
    STACQueryError,
    SatelliteDataError,
    Sentinel2AssetInfo,
    Sentinel2SceneMetadata,
    ValidationError,
    build_stac_search_payload,
    parse_stac_feature,
    search_sentinel2,
    validate_search_params,
)
from tools.satellite_download import (
    AssetDownloadPlan,
    AssetNotFoundError,
    AuthenticationRequiredError,
    DownloadError,
    download_scene_assets,
    download_single_asset,
    get_cdse_access_token,
    plan_scene_downloads,
    select_temporal_pair,
    validate_downloaded_file,
)

__all__ = [
    "AssetDownloadPlan",
    "AssetNotFoundError",
    "AuthenticationRequiredError",
    "BoundingBox",
    "DownloadError",
    "STACQueryError",
    "SatelliteDataError",
    "Sentinel2AssetInfo",
    "Sentinel2SceneMetadata",
    "ValidationError",
    "build_stac_search_payload",
    "download_scene_assets",
    "download_single_asset",
    "get_cdse_access_token",
    "parse_stac_feature",
    "plan_scene_downloads",
    "search_sentinel2",
    "select_temporal_pair",
    "validate_downloaded_file",
    "validate_search_params",
]
