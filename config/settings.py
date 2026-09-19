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

# Optional credentials for future Phase 1B/Phase 2 download access
CDSE_USERNAME: str = os.getenv("CDSE_USERNAME", "")
CDSE_PASSWORD: str = os.getenv("CDSE_PASSWORD", "")
CDSE_S3_ACCESS_KEY: str = os.getenv("CDSE_S3_ACCESS_KEY", "")
CDSE_S3_SECRET_KEY: str = os.getenv("CDSE_S3_SECRET_KEY", "")


# ------------------------------------------------------------------------------
# Example Areas of Interest (AOI) - FOR TESTING & PROTOTYPING ONLY
# ------------------------------------------------------------------------------
# Format: (min_longitude, min_latitude, max_longitude, max_latitude) in WGS84 (EPSG:4326)

@dataclass(frozen=True)
class AOIConfig:
    """Configuration container for an Area of Interest."""
    name: str
    description: str
    bbox: Tuple[float, float, float, float]
    default_start_date: str
    default_end_date: str
    default_max_cloud_cover: float = 20.0


# Clearly marked example AOIs for prototype experimentation:
EXAMPLE_AOIS = {
    # Example 1: Central Europe agricultural & forest test zone (near Prague / Elbe River)
    "central_europe_test": AOIConfig(
        name="Central Europe Test Zone",
        description="Forested and agricultural region suitable for vegetation and temporal monitoring.",
        bbox=(14.25, 50.01, 14.58, 50.13),
        default_start_date="2024-06-01",
        default_end_date="2024-06-30",
        default_max_cloud_cover=20.0,
    ),
    # Example 2: Harz National Park, Germany (known for bark beetle forest change)
    "harz_forest_change": AOIConfig(
        name="Harz National Park",
        description="Region showing significant forest canopy dynamics and dieback.",
        bbox=(10.50, 51.75, 10.75, 51.90),
        default_start_date="2023-07-01",
        default_end_date="2023-08-15",
        default_max_cloud_cover=15.0,
    ),
}

# Default active AOI for baseline discovery tests
DEFAULT_AOI: AOIConfig = EXAMPLE_AOIS["central_europe_test"]
