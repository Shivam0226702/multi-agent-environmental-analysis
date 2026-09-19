# Satellite Data Acquisition: Sentinel-2 Asset Retrieval Pipeline

> **Phase 1B Documentation: Asset Retrieval & Temporal Scene Selection**  
> *Target AOI: Sanjay Gandhi National Park, Mumbai, India*

---

## 1. Study Area Definition (AOI)

For prototyping temporal vegetation and environmental change detection, the initial Area of Interest (AOI) is **Sanjay Gandhi National Park (SGNP)**, situated in northern Mumbai and Thane, Maharashtra, India.

- **Geographic Center**: $\approx 19.22^\circ\text{ N}, 72.91^\circ\text{ E}$
- **Bounding Box (EPSG:4326)**:
  - $\text{min\_lon} = 72.85$ (Western Express Highway / Borivali boundary)
  - $\text{min\_lat} = 19.15$ (Southern boundary / Aarey Milk Colony)
  - $\text{max\_lon} = 73.00$ (Eastern boundary / Thane ridge & Tulsi Lake)
  - $\text{max\_lat} = 19.33$ (Northern boundary / Ghodbunder Road / Bassein Creek)
- **Primary Sentinel-2 MGRS Tile**: `43QBB` (Relative Orbit `R005`)
- **Ecological Context**: A unique protected tropical moist and dry deciduous forest ecosystem surrounded by a mega-city. It experiences sharp phenological contrasts between the post-monsoon green canopy (December–February) and the dry pre-monsoon leaf-shedding period (April–May).

---

## 2. Dynamic Scene Selection Methodology

Rather than hardcoding arbitrary acquisition dates, the system uses `tools.satellite_data.search_sentinel2()` and `tools.satellite_download.select_temporal_pair()` to discover optimal imagery dynamically:

1. **Spatial Filtering**: Restrict queries to the SGNP bounding box.
2. **Atmospheric Thresholding**: Reject scenes with cloud cover $> 10\%$.
3. **Tile Uniformity**: Enforce that both scenes belong to MGRS tile `43QBB` to ensure identical sensor geometry and orthorectification grids.
4. **Temporal Baseline**: Target a 30- to 120-day separation across the dry transition window (March to April 2024).

### Selected Temporal Pair for SGNP:

| Scene | Observation Date | Cloud Cover | Sensor Platform | MGRS Tile | Scene ID |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Date 1 (Baseline)** | 2024-03-07 | **0.00%** | Sentinel-2A | `43QBB` | `S2A_MSIL2A_20240307T053701_N0510_R005_T43QBB_20240307T093354` |
| **Date 2 (Target)** | 2024-04-16 | **1.48%** | Sentinel-2A | `43QBB` | `S2A_MSIL2A_20240416T053641_N0510_R005_T43QBB_20240416T095346` |

*Both scenes are virtually cloud-free, have identical orbital parameters (`R005`, `N0510`), and provide a 40-day temporal baseline.*

---

## 3. Targeted Asset Retrieval Strategy

Full Sentinel-2 Level-2A `.SAFE` packages range between 800 MB and 1.2 GB per acquisition. Downloading two complete archives would consume over 2.2 GB of storage and network bandwidth.

To optimize data transfer, `tools.satellite_download.plan_scene_downloads()` extracts only the **exact single-band assets** required for vegetation index calculation:

1. **Band 4 (Red, 665 nm, 10 m resolution)**: `B04_10m.jp2` ($\approx 108\text{ MB}$)
2. **Band 8 (NIR, 842 nm, 10 m resolution)**: `B08_10m.jp2` ($\approx 112\text{ MB}$)
3. **Scene Classification Layer (20 m resolution)**: `SCL_20m.jp2` ($\approx 1\text{ MB}$)

**Total size per scene**: $\approx 220\text{ MB}$ (an **80% reduction** in bandwidth).

### Resolved CDSE OData HTTPS Download Endpoints:

#### Date 1 (2024-03-07):
- **B04 (Red)**: `https://download.dataspace.copernicus.eu/odata/v1/Products(4efc2517-4f13-4a7c-9fcd-261c7ada852e)/Nodes(S2A_MSIL2A_20240307T053701_N0510_R005_T43QBB_20240307T093354.SAFE)/Nodes(GRANULE)/Nodes(L2A_T43QBB_A045476_20240307T054532)/Nodes(IMG_DATA)/Nodes(R10m)/Nodes(T43QBB_20240307T053701_B04_10m.jp2)/$value`
- **B08 (NIR)**: `https://download.dataspace.copernicus.eu/odata/v1/Products(4efc2517-4f13-4a7c-9fcd-261c7ada852e)/Nodes(S2A_MSIL2A_20240307T053701_N0510_R005_T43QBB_20240307T093354.SAFE)/Nodes(GRANULE)/Nodes(L2A_T43QBB_A045476_20240307T054532)/Nodes(IMG_DATA)/Nodes(R10m)/Nodes(T43QBB_20240307T053701_B08_10m.jp2)/$value`
- **SCL (Mask)**: `https://download.dataspace.copernicus.eu/odata/v1/Products(4efc2517-4f13-4a7c-9fcd-261c7ada852e)/Nodes(S2A_MSIL2A_20240307T053701_N0510_R005_T43QBB_20240307T093354.SAFE)/Nodes(GRANULE)/Nodes(L2A_T43QBB_A045476_20240307T054532)/Nodes(IMG_DATA)/Nodes(R20m)/Nodes(T43QBB_20240307T053701_SCL_20m.jp2)/$value`

#### Date 2 (2024-04-16):
- **B04 (Red)**: `https://download.dataspace.copernicus.eu/odata/v1/Products(275ab199-f99c-463b-b889-94c0bcd85ebf)/Nodes(S2A_MSIL2A_20240416T053641_N0510_R005_T43QBB_20240416T095346.SAFE)/Nodes(GRANULE)/Nodes(L2A_T43QBB_A046048_20240416T054719)/Nodes(IMG_DATA)/Nodes(R10m)/Nodes(T43QBB_20240416T053641_B04_10m.jp2)/$value`
- **B08 (NIR)**: `https://download.dataspace.copernicus.eu/odata/v1/Products(275ab199-f99c-463b-b889-94c0bcd85ebf)/Nodes(S2A_MSIL2A_20240416T053641_N0510_R005_T43QBB_20240416T095346.SAFE)/Nodes(GRANULE)/Nodes(L2A_T43QBB_A046048_20240416T054719)/Nodes(IMG_DATA)/Nodes(R10m)/Nodes(T43QBB_20240416T053641_B08_10m.jp2)/$value`
- **SCL (Mask)**: `https://download.dataspace.copernicus.eu/odata/v1/Products(275ab199-f99c-463b-b889-94c0bcd85ebf)/Nodes(S2A_MSIL2A_20240416T053641_N0510_R005_T43QBB_20240416T095346.SAFE)/Nodes(GRANULE)/Nodes(L2A_T43QBB_A046048_20240416T054719)/Nodes(IMG_DATA)/Nodes(R20m)/Nodes(T43QBB_20240416T053641_SCL_20m.jp2)/$value`

---

## 4. Authentication Architecture

### Discovery vs. Download Access
- **Metadata Search (`/search`)**: **100% Open**. No credentials required.
- **Data Binary Access (`/odata/v1/.../$value`)**: **Requires Authentication**. Requests without an `Authorization: Bearer <token>` header return HTTP 401 with JSON error `{"code":"DAT-ZIP-604","message":"Token not found"}`.

### Token Acquisition Protocol:
`tools.satellite_download.get_cdse_access_token()` automates token acquisition:
1. Checks for a manually supplied Bearer token in `CDSE_ACCESS_TOKEN`.
2. If absent, performs a POST request to:  
   `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`  
   with `client_id=cdse-public`, `grant_type=password`, `username=<CDSE_USERNAME>`, and `password=<CDSE_PASSWORD>`.
3. Returns the JWT access token and attaches it to all outgoing asset download requests.

---

## 5. Download Safety & File Integrity Verification

The download routine (`download_single_asset()`) ensures:
- **Chunked Streaming**: Data is streamed in 64 KB chunks to handle large files without memory exhaustion.
- **Atomic Operations**: Files are downloaded to a temporary filename (`*.tmp`) and renamed to the final filename only after completion.
- **Integrity Validation (`validate_downloaded_file`)**:
  - Verifies file exists on disk.
  - Verifies non-zero byte count.
  - Inspects file headers to detect error JSON messages erroneously saved as binaries.

---

## 6. Credentials, Authentication Verification & Download Workflow

### Local Credentials Storage (`.env`)
- CDSE credentials are stored **exclusively** in the local `.env` file at the project root.
- The `.env` file is explicitly ignored in `.gitignore` (`.gitignore:42:.env`) and is **never committed** to Git.
- Credentials template is provided in `.env.example`:
  ```env
  CDSE_USERNAME=your_registered_email@example.com
  CDSE_PASSWORD=your_password
  # Or optional direct token:
  CDSE_ACCESS_TOKEN=your_direct_token_here
  ```

### How Authentication Is Verified
To verify CDSE authentication without printing, logging, or exposing secrets, use `check_cdse_authentication()`:
```python
from tools.satellite_download import check_cdse_authentication

is_authenticated, status_message = check_cdse_authentication()
print(status_message)
# Outputs:
#   "Authentication successful"
#   OR
#   "CDSE credentials not configured locally."
#   OR
#   "Authentication failed"
```

### Storage Location for Raw Satellite Imagery
- All downloaded satellite bands are saved under `data/raw/<scene_id>/`.
- The `data/raw/*` directory is ignored by `.gitignore` to keep binary raster files outside version control.

### Single-Asset Download Verification
Before downloading all required bands (~447 MB total), single-asset download is verified using the lightweight Scene Classification Layer (`SCL_20m`, ~0.45 MB):
```python
from tools.satellite_download import download_single_asset, plan_scene_downloads
from tools.satellite_data import search_sentinel2
from config.settings import DEFAULT_AOI

# 1. Discover target scene
scenes = search_sentinel2(DEFAULT_AOI.bbox, "2024-04-15", "2024-04-17", max_cloud_cover=5.0, limit=1)

# 2. Plan single SCL asset download
plan = plan_scene_downloads(scenes[0], bands=["SCL"])[0]

# 3. Stream download to data/raw/<scene_id>/
file_path = download_single_asset(plan, destination_dir=f"data/raw/{scenes[0].scene_id}")
print(f"Verified download: {file_path.name} ({file_path.stat().st_size} bytes)")
```
- **Verified Download Result**: `S2A_MSIL2A_20240416T053641_N0510_R005_T43QBB_20240416T095346_SCL_20m.jp2` (469,085 bytes, valid JPEG 2000 binary).

