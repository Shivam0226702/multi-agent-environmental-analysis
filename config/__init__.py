"""Configuration Package.

Provides application settings, CDSE STAC endpoints, and example AOI configurations.
"""

from config.settings import (
    AOIConfig,
    CDSE_COLLECTION_SENTINEL2_L2A,
    CDSE_STAC_BASE_URL,
    CDSE_TOKEN_URL,
    DEFAULT_AOI,
    EXAMPLE_AOIS,
)

__all__ = [
    "AOIConfig",
    "CDSE_COLLECTION_SENTINEL2_L2A",
    "CDSE_STAC_BASE_URL",
    "CDSE_TOKEN_URL",
    "DEFAULT_AOI",
    "EXAMPLE_AOIS",
]
