"""Unit tests for the satellite data download module (tools/satellite_download.py).

Tests:
1. AOI validation (Sanjay Gandhi National Park coordinates)
2. Temporal scene pair selection logic
3. Asset URL extraction and download planning (B04, B08, SCL)
4. Authentication handling (missing credentials, 401 response, token retrieval)
5. Download logic using mocked HTTP responses (streamed file writing, atomic rename)
6. File validation (empty files, error JSON responses, non-existent files)
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from config.settings import DEFAULT_AOI, EXAMPLE_AOIS
from tools.satellite_data import (
    BoundingBox,
    Sentinel2AssetInfo,
    Sentinel2SceneMetadata,
)
from tools.satellite_download import (
    AssetDownloadPlan,
    AssetNotFoundError,
    AuthenticationRequiredError,
    DownloadError,
    download_single_asset,
    get_cdse_access_token,
    plan_scene_downloads,
    select_temporal_pair,
    validate_downloaded_file,
)


class TestAOIValidation(unittest.TestCase):
    """Test AOI configuration and bounds validation for Sanjay Gandhi National Park."""

    def test_sgnp_aoi_in_config(self) -> None:
        self.assertIn("sgnp_mumbai", EXAMPLE_AOIS)
        aoi = EXAMPLE_AOIS["sgnp_mumbai"]
        self.assertEqual(aoi.name, "Sanjay Gandhi National Park, Mumbai")
        self.assertEqual(DEFAULT_AOI.name, aoi.name)

        bbox = BoundingBox.from_sequence(aoi.bbox)
        self.assertEqual(bbox.as_list(), [72.85, 19.15, 73.00, 19.33])
        self.assertLess(bbox.min_lon, bbox.max_lon)
        self.assertLess(bbox.min_lat, bbox.max_lat)


class TestTemporalPairSelection(unittest.TestCase):
    """Test logic that selects two scenes with temporal separation on the same tile."""

    def setUp(self) -> None:
        self.scene1 = Sentinel2SceneMetadata(
            scene_id="S2B_20240102",
            datetime_iso="2024-01-02T05:42:29Z",
            cloud_cover_percentage=0.0,
            bbox=[72.85, 19.15, 73.0, 19.33],
            collection="sentinel-2-l2a",
            tile_id="43QBB",
        )
        self.scene2 = Sentinel2SceneMetadata(
            scene_id="S2A_20240107",
            datetime_iso="2024-01-07T05:42:21Z",
            cloud_cover_percentage=8.0,
            bbox=[72.85, 19.15, 73.0, 19.33],
            collection="sentinel-2-l2a",
            tile_id="43QBB",
        )
        self.scene3 = Sentinel2SceneMetadata(
            scene_id="S2A_20240416",
            datetime_iso="2024-04-16T05:36:41Z",
            cloud_cover_percentage=1.48,
            bbox=[72.85, 19.15, 73.0, 19.33],
            collection="sentinel-2-l2a",
            tile_id="43QBB",
        )

    def test_select_temporal_pair_sufficient_separation(self) -> None:
        scenes = [self.scene1, self.scene2, self.scene3]
        # Request at least 30 days separation
        pair = select_temporal_pair(scenes, min_days_apart=30, max_days_apart=180)
        self.assertIsNotNone(pair)
        s_early, s_late = pair
        self.assertEqual(s_early.scene_id, "S2B_20240102")
        self.assertEqual(s_late.scene_id, "S2A_20240416")

    def test_select_temporal_pair_insufficient_separation(self) -> None:
        # Only scenes 5 days apart
        scenes = [self.scene1, self.scene2]
        pair = select_temporal_pair(scenes, min_days_apart=30)
        self.assertIsNone(pair)


class TestAssetURLExtractionAndPlanning(unittest.TestCase):
    """Test extracting B04, B08, and SCL URLs from scene metadata."""

    def setUp(self) -> None:
        self.sample_scene = Sentinel2SceneMetadata(
            scene_id="S2B_SAMPLE",
            datetime_iso="2024-01-02T05:42:29Z",
            cloud_cover_percentage=0.0,
            bbox=[72.85, 19.15, 73.0, 19.33],
            collection="sentinel-2-l2a",
            tile_id="43QBB",
            assets={
                "B04_10m": Sentinel2AssetInfo(
                    name="B04_10m",
                    title="Red (band 4)",
                    href="s3://eodata/B04_10m.jp2",
                    alternate_https="https://download.dataspace.copernicus.eu/odata/v1/Products(1)/Nodes(B04)/$value",
                    file_size_bytes=107794096,
                ),
                "B08_10m": Sentinel2AssetInfo(
                    name="B08_10m",
                    title="NIR (band 8)",
                    href="s3://eodata/B08_10m.jp2",
                    alternate_https="https://download.dataspace.copernicus.eu/odata/v1/Products(1)/Nodes(B08)/$value",
                    file_size_bytes=112126242,
                ),
                "SCL_20m": Sentinel2AssetInfo(
                    name="SCL_20m",
                    title="Scene Classification Layer",
                    href="s3://eodata/SCL_20m.jp2",
                    alternate_https="https://download.dataspace.copernicus.eu/odata/v1/Products(1)/Nodes(SCL)/$value",
                    file_size_bytes=888788,
                ),
            },
        )

    def test_plan_scene_downloads_success(self) -> None:
        plans = plan_scene_downloads(self.sample_scene, bands=["B04", "B08", "SCL"])
        self.assertEqual(len(plans), 3)

        b04_plan = next(p for p in plans if p.band_name == "B04")
        self.assertTrue(b04_plan.download_url.startswith("https://"))
        self.assertEqual(b04_plan.asset_name, "B04_10m")
        self.assertEqual(b04_plan.estimated_size_mb, 102.8)
        self.assertEqual(b04_plan.target_filename, "S2B_SAMPLE_B04_10m.jp2")

        scl_plan = next(p for p in plans if p.band_name == "SCL")
        self.assertEqual(scl_plan.estimated_size_mb, 0.85)

    def test_plan_scene_downloads_missing_band(self) -> None:
        with self.assertRaises(AssetNotFoundError):
            plan_scene_downloads(self.sample_scene, bands=["B11"])


class TestAuthenticationHandling(unittest.TestCase):
    """Test CDSE token handling and credential validation."""

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_credentials_raises_error(self) -> None:
        with self.assertRaises(AuthenticationRequiredError) as ctx:
            get_cdse_access_token(username="", password="")
        self.assertIn("CDSE credentials not found", str(ctx.exception))

    @patch("tools.satellite_download.requests.post")
    def test_valid_credentials_returns_token(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "mock_jwt_token_12345"}
        mock_post.return_value = mock_resp

        token = get_cdse_access_token(username="user@test.com", password="secret_password")
        self.assertEqual(token, "mock_jwt_token_12345")

    @patch("tools.satellite_download.requests.post")
    def test_invalid_credentials_raises_error(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": "invalid_grant", "error_description": "Invalid user credentials"}
        mock_post.return_value = mock_resp

        with self.assertRaises(AuthenticationRequiredError) as ctx:
            get_cdse_access_token(username="user@test.com", password="wrong_password")
        self.assertIn("CDSE authentication failed (401)", str(ctx.exception))


class TestFileValidation(unittest.TestCase):
    """Test local file validation routines."""

    def test_validate_nonexistent_file(self) -> None:
        with self.assertRaises(DownloadError):
            validate_downloaded_file(Path("non_existent_file_12345.jp2"))

    def test_validate_empty_file(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"")
            tf_path = Path(tf.name)
        try:
            with self.assertRaises(DownloadError):
                validate_downloaded_file(tf_path, min_bytes=100)
        finally:
            if tf_path.exists():
                tf_path.unlink()

    def test_validate_error_json_payload(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b'{"code":"DAT-ZIP-604","message":"Token not found"}')
            tf_path = Path(tf.name)
        try:
            with self.assertRaises(DownloadError) as ctx:
                validate_downloaded_file(tf_path)
            self.assertIn("API error message", str(ctx.exception))
        finally:
            if tf_path.exists():
                tf_path.unlink()

    def test_validate_valid_binary_file(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            # 500 bytes of dummy binary data
            tf.write(b"\x00\x01\x02\x03" * 125)
            tf_path = Path(tf.name)
        try:
            size = validate_downloaded_file(tf_path, min_bytes=100)
            self.assertEqual(size, 500)
        finally:
            if tf_path.exists():
                tf_path.unlink()


class TestMockedAssetDownload(unittest.TestCase):
    """Test streamed download logic using mocked HTTP responses."""

    @patch("tools.satellite_download.requests.get")
    def test_download_single_asset_success(self, mock_get: MagicMock) -> None:
        # Mock streaming HTTP response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_content.return_value = [b"\x00" * 256, b"\xff" * 256]
        mock_resp.__enter__.return_value = mock_resp
        mock_get.return_value = mock_resp

        plan = AssetDownloadPlan(
            band_name="B04",
            asset_name="B04_10m",
            download_url="https://mock.copernicus.eu/band4/$value",
            estimated_size_bytes=512,
            estimated_size_mb=0.001,
            target_filename="test_scene_B04_10m.jp2",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            result_path = download_single_asset(
                plan=plan,
                destination_dir=tmp_dir,
                access_token="mock_valid_token",
            )
            self.assertTrue(result_path.exists())
            self.assertEqual(result_path.name, "test_scene_B04_10m.jp2")
            self.assertEqual(result_path.stat().st_size, 512)

    @patch("tools.satellite_download.requests.get")
    def test_download_single_asset_401_error(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = '{"code":"DAT-ZIP-604","message":"Token not found"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_get.return_value = mock_resp

        plan = AssetDownloadPlan(
            band_name="B04",
            asset_name="B04_10m",
            download_url="https://mock.copernicus.eu/band4/$value",
            estimated_size_bytes=512,
            estimated_size_mb=0.001,
            target_filename="test_scene_B04_10m.jp2",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(AuthenticationRequiredError):
                download_single_asset(
                    plan=plan,
                    destination_dir=tmp_dir,
                    access_token="mock_token",
                )


if __name__ == "__main__":
    unittest.main()
