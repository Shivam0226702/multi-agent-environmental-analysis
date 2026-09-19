"""Unit tests for the satellite data acquisition module and CDSE configuration.

Verifies module imports, parameter validation, payload construction,
and STAC feature parsing without downloading any imagery.
"""

import unittest
from unittest.mock import MagicMock, patch

from config.settings import (
    CDSE_COLLECTION_SENTINEL2_L2A,
    CDSE_STAC_BASE_URL,
    DEFAULT_AOI,
    EXAMPLE_AOIS,
)
from tools.satellite_data import (
    BoundingBox,
    Sentinel2AssetInfo,
    Sentinel2SceneMetadata,
    ValidationError,
    build_stac_search_payload,
    parse_stac_feature,
    search_sentinel2,
    validate_search_params,
)


class TestSatelliteDataConfiguration(unittest.TestCase):
    """Test configuration values and example AOI containers."""

    def test_cdse_configuration_constants(self) -> None:
        self.assertTrue(CDSE_STAC_BASE_URL.startswith("https://"))
        self.assertEqual(CDSE_COLLECTION_SENTINEL2_L2A, "sentinel-2-l2a")

    def test_example_aois_validity(self) -> None:
        self.assertIn("central_europe_test", EXAMPLE_AOIS)
        aoi = EXAMPLE_AOIS["central_europe_test"]
        bbox = BoundingBox.from_sequence(aoi.bbox)
        self.assertIsInstance(bbox, BoundingBox)
        self.assertLess(bbox.min_lon, bbox.max_lon)
        self.assertLess(bbox.min_lat, bbox.max_lat)


class TestParameterValidation(unittest.TestCase):
    """Test bounding box, date, and cloud cover validation."""

    def test_valid_bbox(self) -> None:
        bbox = BoundingBox(min_lon=10.0, min_lat=45.0, max_lon=11.0, max_lat=46.0)
        self.assertEqual(bbox.as_list(), [10.0, 45.0, 11.0, 46.0])

    def test_invalid_bbox_coords_order(self) -> None:
        with self.assertRaises(ValidationError):
            BoundingBox(min_lon=11.0, min_lat=45.0, max_lon=10.0, max_lat=46.0)

        with self.assertRaises(ValidationError):
            BoundingBox(min_lon=10.0, min_lat=46.0, max_lon=11.0, max_lat=45.0)

    def test_invalid_bbox_bounds_range(self) -> None:
        with self.assertRaises(ValidationError):
            BoundingBox(min_lon=-190.0, min_lat=0.0, max_lon=10.0, max_lat=10.0)

        with self.assertRaises(ValidationError):
            BoundingBox(min_lon=0.0, min_lat=-95.0, max_lon=10.0, max_lat=10.0)

    def test_bbox_from_sequence_wrong_length(self) -> None:
        with self.assertRaises(ValidationError):
            BoundingBox.from_sequence([10.0, 45.0, 11.0])

    def test_invalid_date_chronology(self) -> None:
        with self.assertRaises(ValidationError):
            validate_search_params(
                bbox=[10.0, 45.0, 11.0, 46.0],
                start_date="2024-06-30",
                end_date="2024-06-01",
            )

    def test_invalid_date_format(self) -> None:
        with self.assertRaises(ValidationError):
            validate_search_params(
                bbox=[10.0, 45.0, 11.0, 46.0],
                start_date="invalid-date",
                end_date="2024-06-01",
            )

    def test_invalid_cloud_cover(self) -> None:
        with self.assertRaises(ValidationError):
            validate_search_params(
                bbox=[10.0, 45.0, 11.0, 46.0],
                start_date="2024-06-01",
                end_date="2024-06-15",
                max_cloud_cover=120.0,
            )


class TestSTACPayloadAndParsing(unittest.TestCase):
    """Test STAC search payload generation and GeoJSON feature parsing."""

    def test_build_stac_search_payload(self) -> None:
        bbox = BoundingBox(14.0, 50.0, 15.0, 51.0)
        payload = build_stac_search_payload(
            bbox=bbox,
            start_iso="2024-06-01T00:00:00Z",
            end_iso="2024-06-30T23:59:59Z",
            max_cloud_cover=15.0,
            limit=5,
        )
        self.assertEqual(payload["collections"], ["sentinel-2-l2a"])
        self.assertEqual(payload["bbox"], [14.0, 50.0, 15.0, 51.0])
        self.assertEqual(payload["datetime"], "2024-06-01T00:00:00Z/2024-06-30T23:59:59Z")
        self.assertEqual(payload["query"], {"eo:cloud_cover": {"lte": 15.0}})
        self.assertEqual(payload["limit"], 5)

    def test_parse_stac_feature(self) -> None:
        sample_feature = {
            "id": "S2A_MSIL2A_20240613T100031_N0510_R122_T33UVR_TEST",
            "collection": "sentinel-2-l2a",
            "bbox": [14.0, 50.0, 15.0, 51.0],
            "properties": {
                "datetime": "2024-06-13T10:00:31Z",
                "eo:cloud_cover": 8.45,
                "platform": "Sentinel-2A",
                "s2:mgrs_tile": "33UVR",
            },
            "assets": {
                "B04_10m": {
                    "title": "Red (band 4) - 10m",
                    "href": "s3://eodata/Sentinel-2/.../B04_10m.jp2",
                    "type": "image/jp2",
                    "file:size": 92471965,
                    "gsd": 10,
                    "roles": ["data", "reflectance"],
                    "alternate": {
                        "https": {
                            "href": "https://download.dataspace.copernicus.eu/odata/.../$value"
                        }
                    },
                },
                "B08_10m": {
                    "title": "NIR (band 8) - 10m",
                    "href": "s3://eodata/Sentinel-2/.../B08_10m.jp2",
                    "type": "image/jp2",
                    "gsd": 10,
                },
                "SCL_20m": {
                    "title": "Scene Classification Layer - 20m",
                    "href": "s3://eodata/Sentinel-2/.../SCL_20m.jp2",
                    "type": "image/jp2",
                    "gsd": 20,
                },
            },
        }

        scene = parse_stac_feature(sample_feature)
        self.assertIsInstance(scene, Sentinel2SceneMetadata)
        self.assertEqual(scene.scene_id, "S2A_MSIL2A_20240613T100031_N0510_R122_T33UVR_TEST")
        self.assertEqual(scene.cloud_cover_percentage, 8.45)
        self.assertEqual(scene.tile_id, "33UVR")
        self.assertEqual(len(scene.assets), 3)

        # Verify band retrieval helpers
        red_asset = scene.get_red_band()
        self.assertIsNotNone(red_asset)
        self.assertEqual(red_asset.name, "B04_10m")
        self.assertTrue(red_asset.alternate_https.startswith("https://"))

        nir_asset = scene.get_nir_band()
        self.assertIsNotNone(nir_asset)
        self.assertEqual(nir_asset.name, "B08_10m")

        scl_asset = scene.get_scl_layer()
        self.assertIsNotNone(scl_asset)
        self.assertEqual(scl_asset.name, "SCL_20m")


class TestSearchSentinel2Mocked(unittest.TestCase):
    """Test search_sentinel2 with a mocked HTTP response to avoid network dependence."""

    @patch("tools.satellite_data.requests.post")
    def test_search_sentinel2_mocked_http(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "id": "S2A_SCENE_2",
                    "properties": {"datetime": "2024-06-15T10:00:00Z", "eo:cloud_cover": 5.0},
                    "assets": {},
                },
                {
                    "id": "S2A_SCENE_1",
                    "properties": {"datetime": "2024-06-05T10:00:00Z", "eo:cloud_cover": 12.0},
                    "assets": {},
                },
            ]
        }
        mock_post.return_value = mock_response

        scenes = search_sentinel2(
            bbox=[14.0, 50.0, 15.0, 51.0],
            start_date="2024-06-01",
            end_date="2024-06-30",
            max_cloud_cover=15.0,
            limit=2,
        )

        self.assertEqual(len(scenes), 2)
        # Verify chronological sorting (SCENE_1 datetime is earlier than SCENE_2)
        self.assertEqual(scenes[0].scene_id, "S2A_SCENE_1")
        self.assertEqual(scenes[1].scene_id, "S2A_SCENE_2")


if __name__ == "__main__":
    unittest.main()
