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

__all__ = [
    "BoundingBox",
    "STACQueryError",
    "SatelliteDataError",
    "Sentinel2AssetInfo",
    "Sentinel2SceneMetadata",
    "ValidationError",
    "build_stac_search_payload",
    "parse_stac_feature",
    "search_sentinel2",
    "validate_search_params",
]
