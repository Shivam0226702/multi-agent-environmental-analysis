"""Satellite data download module for the Multi-Agent Environmental Analysis System.

Provides authenticated and streamed asset retrieval for Sentinel-2 Level-2A imagery
via the Copernicus Data Space Ecosystem (CDSE) OData endpoints.

Downloads only required spectral bands (e.g. B04, B08, SCL) to minimize bandwidth and storage.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from config.settings import (
    CDSE_TOKEN_URL,
    CDSE_USERNAME,
    CDSE_PASSWORD,
)
from tools.satellite_data import Sentinel2AssetInfo, Sentinel2SceneMetadata

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------------
class DownloadError(Exception):
    """Base exception for satellite imagery download failures."""
    pass


class AuthenticationRequiredError(DownloadError):
    """Raised when asset access requires CDSE credentials that are missing or invalid."""
    pass


class AssetNotFoundError(DownloadError):
    """Raised when a requested band or asset is missing from the scene."""
    pass


# ------------------------------------------------------------------------------
# Download Plan / Summary Model
# ------------------------------------------------------------------------------
@dataclass(frozen=True)
class AssetDownloadPlan:
    """Summary of an asset planned for download."""
    band_name: str
    asset_name: str
    download_url: str
    estimated_size_bytes: Optional[int]
    estimated_size_mb: Optional[float]
    target_filename: str


# ------------------------------------------------------------------------------
# Authentication Helpers
# ------------------------------------------------------------------------------
def get_cdse_access_token(
    username: Optional[str] = None,
    password: Optional[str] = None,
    token_url: Optional[str] = None,
    timeout: int = 15,
) -> str:
    """Fetch an OpenID Connect (OIDC) Bearer token from the CDSE identity provider.

    Args:
        username: CDSE registered username or email. Defaults to CDSE_USERNAME from env.
        password: CDSE account password. Defaults to CDSE_PASSWORD from env.
        token_url: Token endpoint URL. Defaults to CDSE_TOKEN_URL.
        timeout: HTTP request timeout in seconds.

    Returns:
        String access token (JWT).

    Raises:
        AuthenticationRequiredError: If credentials are missing or rejected by CDSE.
    """
    user = username or os.getenv("CDSE_USERNAME") or CDSE_USERNAME
    pwd = password or os.getenv("CDSE_PASSWORD") or CDSE_PASSWORD
    endpoint = token_url or os.getenv("CDSE_TOKEN_URL") or CDSE_TOKEN_URL

    # Check for direct access token in environment first
    direct_token = os.getenv("CDSE_ACCESS_TOKEN", "").strip()
    if direct_token:
        return direct_token

    if not user or not pwd:
        raise AuthenticationRequiredError(
            "CDSE credentials not found. Asset download requires authentication.\n"
            "Please provide credentials in '.env' or environment variables:\n"
            "  CDSE_USERNAME=your_username_or_email\n"
            "  CDSE_PASSWORD=your_password\n"
            "Or provide a direct token via CDSE_ACCESS_TOKEN.\n"
            "Register for a free account at: https://dataspace.copernicus.eu"
        )

    if not HAS_REQUESTS:
        raise DownloadError("The 'requests' package is required for CDSE authentication.")

    payload = {
        "client_id": "cdse-public",
        "grant_type": "password",
        "username": user,
        "password": pwd,
    }

    try:
        resp = requests.post(endpoint, data=payload, timeout=timeout)
        if resp.status_code == 200:
            token_data = resp.json()
            token = token_data.get("access_token")
            if not token:
                raise AuthenticationRequiredError("CDSE token endpoint returned 200 but no 'access_token' was found.")
            return str(token)
        elif resp.status_code in (400, 401):
            err_msg = resp.text
            try:
                err_json = resp.json()
                err_msg = err_json.get("error_description") or err_json.get("error") or err_msg
            except Exception:
                pass
            raise AuthenticationRequiredError(f"CDSE authentication failed ({resp.status_code}): {err_msg}")
        else:
            raise AuthenticationRequiredError(
                f"CDSE identity provider returned unexpected HTTP {resp.status_code}: {resp.text[:200]}"
            )
    except AuthenticationRequiredError:
        raise
    except Exception as exc:
        raise AuthenticationRequiredError(f"Failed to connect to CDSE identity endpoint: {exc}") from exc


# ------------------------------------------------------------------------------
# Asset URL Extraction & Planning
# ------------------------------------------------------------------------------
def plan_scene_downloads(
    scene: Sentinel2SceneMetadata,
    bands: Sequence[str] = ("B04", "B08", "SCL"),
) -> List[AssetDownloadPlan]:
    """Inspect scene metadata and generate an explicit download plan for requested bands.

    Resolves HTTPS OData URLs and estimated file sizes before downloading.

    Args:
        scene: Parsed Sentinel-2 scene metadata.
        bands: Iterable of band identifiers to download (e.g. ['B04', 'B08', 'SCL']).

    Returns:
        List of AssetDownloadPlan objects.

    Raises:
        AssetNotFoundError: If a requested band is missing from the scene metadata.
    """
    plans: List[AssetDownloadPlan] = []

    for band in bands:
        asset = scene.get_band_asset(band)
        if not asset:
            raise AssetNotFoundError(
                f"Scene '{scene.scene_id}' does not contain required band '{band}'."
            )

        # Prefer HTTPS OData URL for direct HTTP download
        download_url = asset.alternate_https or asset.href
        if not download_url.startswith("http"):
            raise DownloadError(
                f"No HTTPS download URL available for asset '{asset.name}' in scene '{scene.scene_id}'. "
                f"Only URI found was: '{download_url}'"
            )

        size_bytes = asset.file_size_bytes
        size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes else None

        # Standardize target filename: e.g. T43QBB_20240102_B04_10m.jp2 or <scene_id>_<asset_name>.jp2
        ext = ".jp2"
        if asset.asset_type == "image/tiff" or download_url.endswith(".tif") or download_url.endswith(".tiff"):
            ext = ".tif"
        elif download_url.endswith(".jp2"):
            ext = ".jp2"

        target_name = f"{scene.scene_id}_{asset.name}{ext}"

        plans.append(
            AssetDownloadPlan(
                band_name=band,
                asset_name=asset.name,
                download_url=download_url,
                estimated_size_bytes=size_bytes,
                estimated_size_mb=size_mb,
                target_filename=target_name,
            )
        )

    return plans


# ------------------------------------------------------------------------------
# File Download & Validation
# ------------------------------------------------------------------------------
def validate_downloaded_file(file_path: Union[str, Path], min_bytes: int = 100) -> int:
    """Validate that a downloaded file exists, is non-empty, and does not contain an API error JSON.

    Returns:
        File size in bytes.

    Raises:
        DownloadError: If the file is missing, empty, or an error response.
    """
    p = Path(file_path)
    if not p.exists():
        raise DownloadError(f"Validation failed: File '{p}' does not exist.")

    size = p.stat().st_size
    if size == 0:
        raise DownloadError(f"Validation failed: File '{p}' is empty (0 bytes).")

    # Check for small JSON error payloads (e.g. CDSE error responses saved as binary)
    if size < 4096:
        try:
            with open(p, "rb") as f:
                header = f.read(200).decode("utf-8", errors="ignore").strip()
                if header.startswith("{") and ("error" in header or "code" in header or "trace-id" in header or "message" in header):
                    raise DownloadError(
                        f"Validation failed: File '{p}' contains an API error message instead of image data: {header}"
                    )
        except UnicodeDecodeError:
            pass

    if size < min_bytes:
        raise DownloadError(
            f"Validation failed: File '{p}' is suspiciously small ({size} bytes, minimum is {min_bytes} bytes)."
        )

    return size


def download_single_asset(
    plan: AssetDownloadPlan,
    destination_dir: Union[str, Path],
    access_token: Optional[str] = None,
    overwrite: bool = False,
    timeout: int = 60,
    chunk_size: int = 65536,
) -> Path:
    """Download an individual satellite band asset with authentication and streaming.

    Args:
        plan: AssetDownloadPlan describing the asset, URL, and target filename.
        destination_dir: Directory where the file should be saved.
        access_token: Optional OIDC Bearer token. If omitted, attempts to obtain one.
        overwrite: Whether to overwrite existing destination file if present.
        timeout: Network timeout in seconds per chunk.
        chunk_size: Streaming chunk size in bytes (default 64 KB).

    Returns:
        Path to the successfully downloaded and validated file.

    Raises:
        AuthenticationRequiredError: If access is unauthorized.
        DownloadError: If download fails or fails validation.
    """
    if not HAS_REQUESTS:
        raise DownloadError("The 'requests' package is required for downloading satellite imagery.")

    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    target_path = dest_dir / plan.target_filename

    # If file already exists and is valid, reuse it unless overwrite=True
    if target_path.exists() and not overwrite:
        try:
            validate_downloaded_file(target_path)
            logger.info("Reusing existing valid asset: %s", target_path)
            return target_path
        except DownloadError:
            logger.warning("Existing file '%s' was invalid; re-downloading.", target_path)

    # Resolve token if not explicitly passed
    token = access_token
    if not token:
        token = get_cdse_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "MultiAgentEnvAnalysis/0.1",
    }

    temp_path = dest_dir / f"{plan.target_filename}.tmp"

    try:
        with requests.get(plan.download_url, headers=headers, stream=True, timeout=timeout, allow_redirects=True) as resp:
            if resp.status_code == 401:
                raise AuthenticationRequiredError(
                    f"CDSE returned 401 Unauthorized for URL '{plan.download_url}'. "
                    f"Token may be expired or invalid: {resp.text[:200]}"
                )
            if resp.status_code == 403:
                raise AuthenticationRequiredError(
                    f"CDSE returned 403 Forbidden for URL '{plan.download_url}'. "
                    f"Account may lack permissions: {resp.text[:200]}"
                )
            if resp.status_code != 200:
                raise DownloadError(
                    f"Failed to download asset '{plan.asset_name}'. HTTP {resp.status_code}: {resp.text[:300]}"
                )

            with open(temp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

        # Atomic move to final target path
        if temp_path.exists():
            shutil.move(str(temp_path), str(target_path))

        # Validate resulting file
        validate_downloaded_file(target_path)
        return target_path

    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def download_scene_assets(
    scene: Sentinel2SceneMetadata,
    output_dir: Union[str, Path],
    bands: Sequence[str] = ("B04", "B08", "SCL"),
    access_token: Optional[str] = None,
    overwrite: bool = False,
) -> Dict[str, Path]:
    """Download all requested bands for a Sentinel-2 scene.

    Args:
        scene: Parsed Sentinel2SceneMetadata.
        output_dir: Parent directory where scene folder will be created.
        bands: Tuple of band names to download (default B04, B08, SCL).
        access_token: Optional Bearer token.
        overwrite: Whether to overwrite existing files.

    Returns:
        Dictionary mapping band names (e.g. 'B04', 'B08', 'SCL') to downloaded local Path objects.
    """
    scene_dir = Path(output_dir) / scene.scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)

    plans = plan_scene_downloads(scene=scene, bands=bands)
    downloaded: Dict[str, Path] = {}

    for plan in plans:
        logger.info("Downloading %s for scene %s...", plan.band_name, scene.scene_id)
        path = download_single_asset(
            plan=plan,
            destination_dir=scene_dir,
            access_token=access_token,
            overwrite=overwrite,
        )
        downloaded[plan.band_name] = path

    return downloaded


# ------------------------------------------------------------------------------
# Scene Pair Selection Helper
# ------------------------------------------------------------------------------
def select_temporal_pair(
    scenes: List[Sentinel2SceneMetadata],
    min_days_apart: int = 30,
    max_days_apart: int = 180,
    preferred_tile: Optional[str] = None,
) -> Optional[Tuple[Sentinel2SceneMetadata, Sentinel2SceneMetadata]]:
    """Select two high-quality Sentinel-2 scenes covering the same tile with temporal separation.

    Args:
        scenes: List of discovered scenes.
        min_days_apart: Minimum separation in days between date 1 and date 2.
        max_days_apart: Maximum separation in days.
        preferred_tile: Optional MGRS tile filter (e.g. '43QBB').

    Returns:
        Tuple of (earlier_scene, later_scene), or None if no valid pair found.
    """
    from datetime import datetime

    filtered = scenes
    if preferred_tile:
        filtered = [s for s in scenes if s.tile_id and preferred_tile in s.tile_id]

    if len(filtered) < 2:
        return None

    # Group scenes by tile_id
    by_tile: Dict[str, List[Sentinel2SceneMetadata]] = {}
    for s in filtered:
        t_id = s.tile_id or "default"
        by_tile.setdefault(t_id, []).append(s)

    best_pair: Optional[Tuple[Sentinel2SceneMetadata, Sentinel2SceneMetadata]] = None
    lowest_combined_cloud = float("inf")

    for t_id, tile_scenes in by_tile.items():
        if len(tile_scenes) < 2:
            continue
        # Sort chronologically
        sorted_scenes = sorted(tile_scenes, key=lambda s: s.datetime_iso)
        for i in range(len(sorted_scenes)):
            for j in range(i + 1, len(sorted_scenes)):
                s1 = sorted_scenes[i]
                s2 = sorted_scenes[j]
                try:
                    dt1 = datetime.fromisoformat(s1.datetime_iso.replace("Z", "+00:00"))
                    dt2 = datetime.fromisoformat(s2.datetime_iso.replace("Z", "+00:00"))
                    days_diff = abs((dt2 - dt1).days)
                except Exception:
                    continue

                if min_days_apart <= days_diff <= max_days_apart:
                    combined_cloud = s1.cloud_cover_percentage + s2.cloud_cover_percentage
                    if combined_cloud < lowest_combined_cloud:
                        lowest_combined_cloud = combined_cloud
                        best_pair = (s1, s2)

    return best_pair
