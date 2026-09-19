"""Satellite data acquisition module for the Multi-Agent Environmental Analysis System.

Provides discovery and metadata querying for Sentinel-2 Level-2A imagery
via the Copernicus Data Space Ecosystem (CDSE) STAC API.

Does NOT download large imagery files; returns structured metadata and asset references.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.error
    import urllib.request
    HAS_REQUESTS = False

from config.settings import (
    CDSE_COLLECTION_SENTINEL2_L2A,
    CDSE_STAC_BASE_URL,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Custom Exceptions
# ------------------------------------------------------------------------------
class SatelliteDataError(Exception):
    """Base exception for satellite data operations."""
    pass


class ValidationError(SatelliteDataError):
    """Raised when search parameters (coordinates, dates, cloud cover) are invalid."""
    pass


class STACQueryError(SatelliteDataError):
    """Raised when the STAC API returns an HTTP or payload parsing error."""
    pass


# ------------------------------------------------------------------------------
# Data Models / Structures
# ------------------------------------------------------------------------------
@dataclass(frozen=True)
class BoundingBox:
    """Geographic Bounding Box in WGS84 (EPSG:4326).

    Coordinates: (min_longitude, min_latitude, max_longitude, max_latitude)
    """
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def __post_init__(self) -> None:
        if not (-180.0 <= self.min_lon <= 180.0 and -180.0 <= self.max_lon <= 180.0):
            raise ValidationError(
                f"Longitude values must be between -180 and 180. Got min_lon={self.min_lon}, max_lon={self.max_lon}"
            )
        if not (-90.0 <= self.min_lat <= 90.0 and -90.0 <= self.max_lat <= 90.0):
            raise ValidationError(
                f"Latitude values must be between -90 and 90. Got min_lat={self.min_lat}, max_lat={self.max_lat}"
            )
        if self.min_lon >= self.max_lon:
            raise ValidationError(
                f"min_lon ({self.min_lon}) must be strictly less than max_lon ({self.max_lon})"
            )
        if self.min_lat >= self.max_lat:
            raise ValidationError(
                f"min_lat ({self.min_lat}) must be strictly less than max_lat ({self.max_lat})"
            )

    def as_list(self) -> List[float]:
        """Return coordinates as [min_lon, min_lat, max_lon, max_lat]."""
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    @classmethod
    def from_sequence(cls, seq: Sequence[float]) -> BoundingBox:
        """Create BoundingBox from a 4-element sequence [min_lon, min_lat, max_lon, max_lat]."""
        if len(seq) != 4:
            raise ValidationError(
                f"Bounding box must contain exactly 4 numbers [min_lon, min_lat, max_lon, max_lat]. Got {len(seq)}"
            )
        return cls(min_lon=float(seq[0]), min_lat=float(seq[1]), max_lon=float(seq[2]), max_lat=float(seq[3]))


@dataclass
class Sentinel2AssetInfo:
    """Metadata for a single asset/band within a Sentinel-2 scene."""
    name: str
    title: Optional[str] = None
    href: str = ""
    alternate_https: Optional[str] = None
    asset_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    gsd_meters: Optional[float] = None
    roles: List[str] = field(default_factory=list)


@dataclass
class Sentinel2SceneMetadata:
    """Structured metadata for a single Sentinel-2 Level-2A scene item."""
    scene_id: str
    datetime_iso: str
    cloud_cover_percentage: float
    bbox: List[float]
    collection: str
    platform: Optional[str] = None
    tile_id: Optional[str] = None
    assets: Dict[str, Sentinel2AssetInfo] = field(default_factory=dict)

    def get_band_asset(self, band_name: str) -> Optional[Sentinel2AssetInfo]:
        """Retrieve asset info for a band by key (e.g. 'B04_10m', 'B04', 'SCL_20m')."""
        if band_name in self.assets:
            return self.assets[band_name]
        for key, asset in self.assets.items():
            if key.startswith(band_name):
                return asset
        return None

    def get_red_band(self) -> Optional[Sentinel2AssetInfo]:
        """Convenience method to retrieve Red (B04 10m) asset info."""
        return self.get_band_asset("B04_10m") or self.get_band_asset("B04")

    def get_nir_band(self) -> Optional[Sentinel2AssetInfo]:
        """Convenience method to retrieve NIR (B08 10m) asset info."""
        return self.get_band_asset("B08_10m") or self.get_band_asset("B08")

    def get_scl_layer(self) -> Optional[Sentinel2AssetInfo]:
        """Convenience method to retrieve Scene Classification Layer (SCL 20m) for cloud masking."""
        return self.get_band_asset("SCL_20m") or self.get_band_asset("SCL")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize scene metadata to dictionary."""
        return asdict(self)


# ------------------------------------------------------------------------------
# Validation Helpers
# ------------------------------------------------------------------------------
def _parse_iso_date(date_str: str) -> str:
    """Validate and format date string to ISO-8601 UTC timestamp."""
    cleaned = date_str.strip()
    # Accept YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
        return f"{cleaned}T00:00:00Z"
    # Accept standard ISO 8601
    try:
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        raise ValidationError(
            f"Invalid date format: '{date_str}'. Expected 'YYYY-MM-DD' or ISO-8601. Error: {e}"
        )


def validate_search_params(
    bbox: Union[BoundingBox, Sequence[float]],
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 20.0,
    limit: int = 10,
) -> Tuple[BoundingBox, str, str, float, int]:
    """Validate all search parameters before querying the STAC endpoint."""
    if isinstance(bbox, BoundingBox):
        bbox_obj = bbox
    else:
        bbox_obj = BoundingBox.from_sequence(bbox)

    start_iso = _parse_iso_date(start_date)
    end_iso = _parse_iso_date(end_date)
    # Ensure end date is not before start date
    if start_iso > end_iso:
        raise ValidationError(
            f"start_date ({start_date}) cannot be after end_date ({end_date})"
        )

    if not (0.0 <= max_cloud_cover <= 100.0):
        raise ValidationError(
            f"max_cloud_cover must be between 0.0 and 100.0. Got {max_cloud_cover}"
        )

    if not (1 <= limit <= 250):
        raise ValidationError(
            f"limit must be between 1 and 250 for CDSE STAC queries. Got {limit}"
        )

    return bbox_obj, start_iso, end_iso, float(max_cloud_cover), int(limit)


# ------------------------------------------------------------------------------
# STAC Payload & Feature Parsing
# ------------------------------------------------------------------------------
def build_stac_search_payload(
    bbox: BoundingBox,
    start_iso: str,
    end_iso: str,
    max_cloud_cover: float,
    limit: int,
    collection: str = CDSE_COLLECTION_SENTINEL2_L2A,
) -> Dict[str, Any]:
    """Construct standard STAC API POST search payload for CDSE."""
    return {
        "collections": [collection],
        "bbox": bbox.as_list(),
        "datetime": f"{start_iso}/{end_iso}",
        "query": {
            "eo:cloud_cover": {
                "lte": max_cloud_cover
            }
        },
        "limit": limit,
    }


def parse_stac_feature(feature: Dict[str, Any]) -> Sentinel2SceneMetadata:
    """Parse a single STAC GeoJSON feature from CDSE into structured Sentinel2SceneMetadata."""
    scene_id = feature.get("id", "unknown_scene")
    properties = feature.get("properties", {})
    raw_assets = feature.get("assets", {})

    # Extract datetime and cloud cover
    dt_iso = properties.get("datetime") or properties.get("start_datetime") or "unknown"
    cloud_cover = float(properties.get("eo:cloud_cover", 100.0))
    platform = properties.get("platform") or properties.get("constellation")
    tile_id = properties.get("s2:mgrs_tile") or properties.get("grid:code")

    parsed_assets: Dict[str, Sentinel2AssetInfo] = {}
    for asset_key, asset_val in raw_assets.items():
        href = asset_val.get("href", "")
        # Extract alternate HTTPS link if primary is S3
        alternate_https = None
        alternates = asset_val.get("alternate", {})
        if "https" in alternates:
            alternate_https = alternates["https"].get("href")

        parsed_assets[asset_key] = Sentinel2AssetInfo(
            name=asset_key,
            title=asset_val.get("title"),
            href=href,
            alternate_https=alternate_https,
            asset_type=asset_val.get("type"),
            file_size_bytes=asset_val.get("file:size"),
            gsd_meters=asset_val.get("gsd"),
            roles=asset_val.get("roles", []),
        )

    return Sentinel2SceneMetadata(
        scene_id=scene_id,
        datetime_iso=dt_iso,
        cloud_cover_percentage=round(cloud_cover, 2),
        bbox=feature.get("bbox", []),
        collection=feature.get("collection", CDSE_COLLECTION_SENTINEL2_L2A),
        platform=platform,
        tile_id=tile_id,
        assets=parsed_assets,
    )


# ------------------------------------------------------------------------------
# Core Search Function
# ------------------------------------------------------------------------------
def search_sentinel2(
    bbox: Union[BoundingBox, Sequence[float]],
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 20.0,
    limit: int = 10,
    stac_url: Optional[str] = None,
    timeout_seconds: int = 25,
) -> List[Sentinel2SceneMetadata]:
    """Search the Copernicus Data Space Ecosystem (CDSE) STAC API for Sentinel-2 L2A scenes.

    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat] in EPSG:4326.
        start_date: Start date string (YYYY-MM-DD or ISO-8601).
        end_date: End date string (YYYY-MM-DD or ISO-8601).
        max_cloud_cover: Maximum allowable cloud cover percentage (0.0 - 100.0).
        limit: Maximum number of scenes to retrieve (1 - 250).
        stac_url: Custom STAC endpoint; defaults to CDSE_STAC_BASE_URL.
        timeout_seconds: HTTP request timeout in seconds.

    Returns:
        List of Sentinel2SceneMetadata objects sorted chronologically.

    Raises:
        ValidationError: If input parameters fail sanity checks.
        STACQueryError: If the remote STAC API returns an error or unparseable response.
    """
    bbox_obj, start_iso, end_iso, cloud_threshold, search_limit = validate_search_params(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        limit=limit,
    )

    base_endpoint = stac_url or CDSE_STAC_BASE_URL
    search_endpoint = f"{base_endpoint.rstrip('/')}/search"
    payload = build_stac_search_payload(
        bbox=bbox_obj,
        start_iso=start_iso,
        end_iso=end_iso,
        max_cloud_cover=cloud_threshold,
        limit=search_limit,
    )

    logger.debug("Executing CDSE STAC search: %s, payload: %s", search_endpoint, payload)

    try:
        if HAS_REQUESTS:
            headers = {"Content-Type": "application/json", "User-Agent": "MultiAgentEnvAnalysis/0.1"}
            resp = requests.post(search_endpoint, json=payload, headers=headers, timeout=timeout_seconds)
            if resp.status_code != 200:
                raise STACQueryError(
                    f"CDSE STAC query failed with HTTP {resp.status_code}: {resp.text[:300]}"
                )
            data = resp.json()
        else:
            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                search_endpoint,
                data=json_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "MultiAgentEnvAnalysis/0.1"},
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as raw_resp:
                data = json.loads(raw_resp.read().decode("utf-8"))
    except (ValidationError, STACQueryError):
        raise
    except Exception as exc:
        raise STACQueryError(f"Failed to query CDSE STAC API at '{search_endpoint}': {exc}") from exc

    features = data.get("features", [])
    parsed_scenes = [parse_stac_feature(feat) for feat in features]

    # Sort scenes chronologically
    parsed_scenes.sort(key=lambda s: s.datetime_iso)
    return parsed_scenes
