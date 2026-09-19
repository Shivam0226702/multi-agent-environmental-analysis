"""Configuration settings for the Multi-Agent Environmental Analysis System.

Handles environment variable loading, API endpoints, default search parameters,
and sample Areas of Interest (AOI).
"""

import os
from dataclasses import dataclass
from typing import Tuple


def _load_env_safely() -> None:
    """Attempt to load .env using python-dotenv if available; ignore if missing."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


_load_env_safely()


# ------------------------------------------------------------------------------
# Copernicus Data Space Ecosystem (CDSE) Configuration
# ------------------------------------------------------------------------------
CDSE_STAC_BASE_URL: str = os.getenv(
    "CDSE_STAC_BASE_URL", "https://stac.dataspace.copernicus.eu/v1"
)
CDSE_COLLECTION_SENTINEL2_L2A: str = os.getenv(
    "CDSE_COLLECTION_SENTINEL2_L2A", "sentinel-2-l2a"
)
CDSE_TOKEN_URL: str = os.getenv(
    "CDSE_TOKEN_URL",
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
)

# Authentication credentials for asset downloads (Phase 1B+)
CDSE_USERNAME: str = os.getenv("CDSE_USERNAME", "")
CDSE_PASSWORD: str = os.getenv("CDSE_PASSWORD", "")
CDSE_ACCESS_TOKEN: str = os.getenv("CDSE_ACCESS_TOKEN", "")
CDSE_S3_ACCESS_KEY: str = os.getenv("CDSE_S3_ACCESS_KEY", "")
CDSE_S3_SECRET_KEY: str = os.getenv("CDSE_S3_SECRET_KEY", "")


# ------------------------------------------------------------------------------
# Areas of Interest (AOI) Configuration
# ------------------------------------------------------------------------------
# Coordinates format: (min_longitude, min_latitude, max_longitude, max_latitude) in EPSG:4326 (WGS84)

@dataclass(frozen=True)
class AOIConfig:
    """Configuration container for an Area of Interest."""
    name: str
    description: str
    bbox: Tuple[float, float, float, float]
    default_start_date: str
    default_end_date: str
    default_max_cloud_cover: float = 20.0
    mgrs_tile: str = ""


EXAMPLE_AOIS = {
    # Primary Study Area: Sanjay Gandhi National Park, Mumbai, India
    # Approx 103 sq. km tropical moist/dry deciduous forest in northern Mumbai
    "sgnp_mumbai": AOIConfig(
        name="Sanjay Gandhi National Park, Mumbai",
        description="Protected tropical forest ecosystem in northern Mumbai/Thane, India.",
        bbox=(72.85, 19.15, 73.00, 19.33),
        default_start_date="2024-01-01",
        default_end_date="2024-05-31",
        default_max_cloud_cover=10.0,
        mgrs_tile="43QBB",
    ),
    # Secondary Example: Central Europe agricultural & forest test zone
    "central_europe_test": AOIConfig(
        name="Central Europe Test Zone",
        description="Forested and agricultural region suitable for vegetation monitoring.",
        bbox=(14.25, 50.01, 14.58, 50.13),
        default_start_date="2024-06-01",
        default_end_date="2024-06-30",
        default_max_cloud_cover=20.0,
        mgrs_tile="33UVR",
    ),
    # Secondary Example: Harz National Park, Germany (forest dieback)
    "harz_forest_change": AOIConfig(
        name="Harz National Park",
        description="Region showing significant forest canopy dynamics and dieback.",
        bbox=(10.50, 51.75, 10.75, 51.90),
        default_start_date="2023-07-01",
        default_end_date="2023-08-15",
        default_max_cloud_cover=15.0,
        mgrs_tile="32UNC",
    ),
}

# Default active AOI set to Sanjay Gandhi National Park, Mumbai
DEFAULT_AOI: AOIConfig = EXAMPLE_AOIS["sgnp_mumbai"]
