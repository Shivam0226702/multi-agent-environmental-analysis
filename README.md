# Multi-Agent Environmental Analysis System

> **Project Status: Phase 0 — Foundation & Setup**  
> *Notice: This repository is currently in its foundational scaffolding stage. AI agents, ML models, and external data pipelines are not yet implemented or active.*

---

## 1. Project Title
**Multi-Agent Environmental Analysis System** (An Agentic Geospatial & Environmental Intelligence Platform)

---

## 2. Problem Statement
Monitoring large-scale environmental changes—such as deforestation, agricultural drought, vegetative health decline, urban encroachment, and recurring natural disaster damage—requires analyzing massive, multi-temporal Earth Observation (EO) and satellite datasets. Traditional remote sensing workflows often demand manual data retrieval, domain-specific script execution, complex multi-band radiometric calculations, and tedious report compilation.

For environmental analysts, local authorities, and researchers, there is a distinct need for an automated, modular system that can autonomously plan and execute satellite data retrieval, preprocess multi-spectral imagery, compute standard biophysical indices (e.g., NDVI, NDWI), track temporal shifts, identify localized anomalies or disaster footprints, and synthesize actionable, structured intelligence reports.

---

## 3. Project Objective
The primary objective of this engineering mini-project is to build a working, reliable prototype of a **Multi-Agent Environmental Analysis System** using Python and an agent orchestration framework (such as LangGraph). 

Key aims include:
1. Decomposing complex environmental analysis pipelines into modular, single-responsibility AI agents.
2. Automating the querying, ingestion, and preprocessing of multi-temporal satellite data for specific geographic Areas of Interest (AOI).
3. Computing temporal vegetation and environmental index differentials to flag degradation or recovery trends.
4. Analyzing localized environmental events or recurring disaster footprints where relevant data is available.
5. Synthesizing findings into coherent, structured environmental evaluation reports.
6. Maintaining high code quality, deterministic workflow control, and clear separation of concerns suitable for engineering evaluation.

---

## 4. Proposed System Overview
The proposed system employs a multi-agent paradigm where specialized agents interact via a shared state graph. Rather than relying on a single monolithic LLM prompt or an unconstrained autonomous agent, tasks are partitioned across distinct functional layers:

1. **User Interaction & Orchestration Layer**: Receives natural language queries or structured parameters (AOI, target dates, analysis type) and constructs a task execution plan.
2. **Data Acquisition & Preprocessing Layer**: Coordinates downloading or simulating satellite scenes, handles cloud masking, spatial cropping, and format alignment.
3. **Domain-Specific Analysis Layer**: Computes spectral vegetation indices, runs temporal differencing algorithms, and detects significant changes or disaster impacts.
4. **Synthesis & Reporting Layer**: Aggregates metrics, statistical tables, and spatial visual artifacts into an executive environmental summary report.

---

## 5. Proposed Agents & Provisional Responsibilities
The system will feature the following provisional agents:

| Agent Name | Primary Responsibility |
| :--- | :--- |
| **Orchestrator / Coordinator Agent** | Parses user requests, validates input criteria (AOI, temporal window), initializes workflow state, routes tasks between agents, and manages execution flow. |
| **Data Collection Agent** | Queries Earth Observation metadata catalogs (or local sample archives) and retrieves appropriate multi-band satellite data for requested dates and bounding boxes. |
| **Data Processing Agent** | Validates scene quality, performs spatial clipping, band alignment, and radiometric scaling/normalization to produce clean arrays for analysis. |
| **Vegetation / Environmental Analysis Agent** | Computes biophysical and spectral indices (NDVI, NDWI, EVI), calculates mean canopy vitality metrics, and classifies vegetation health tiers. |
| **Temporal Comparison Agent** | Performs pixel-level and statistical differencing across multiple dates ($T_1$ vs. $T_2$) to detect degradation, deforestation, seasonal variation, or regrowth. |
| **Disaster / Event Analysis Agent** | Analyzes anomalies corresponding to acute or recurring environmental shocks (e.g., flood extent, wildfire burn severity via NBR, severe drought stress). |
| **Report / Conclusion Agent** | Collates analytical findings, summary metrics, and generated figure references into a structured Markdown/PDF environmental assessment report. |

---

## 6. Expected Workflow
The expected operational workflow is designed as a directed state machine:

```
[User Query / Task Parameters]
             │
             ▼
   [Orchestrator Agent]
             │
      (Task Planning)
             │
             ▼
   [Data Collection Agent] ──► Query/Fetch Multi-temporal Scenes
             │
             ▼
   [Data Processing Agent] ──► Calibrate, Clip, Mask Clouds
             │
             ├───────────────────────────────┐
             ▼                               ▼
[Vegetation Analysis Agent]      [Disaster / Event Agent]
  (NDVI/NDWI Computation)         (Burn/Flood/Drought Anomaly)
             │                               │
             └───────────────┬───────────────┘
                             ▼
               [Temporal Comparison Agent]
                 (Change Detection / ΔNDVI)
                             │
                             ▼
                 [Report / Synthesis Agent]
                 (Structured Intelligence)
                             │
                             ▼
                 [Final Assessment Report]
```

---

## 7. Planned Technologies
- **Core Language**: Python 3.11+
- **Multi-Agent Orchestration**: LangGraph / LangChain (for cyclic state graphs, checkpointing, and controlled routing)
- **Language Models**: Google Gemini / OpenAI / Anthropic (via official SDKs or LangChain wrappers)
- **Data & Schema Validation**: Pydantic v2
- **Geospatial & Image Processing (Future Phases)**:
  - `rasterio` / `rioxarray` (raster data manipulation)
  - `geopandas` / `shapely` (vector boundaries and AOI management)
  - `numpy` / `scipy` (efficient array computing and index differencing)
  - `matplotlib` / `folium` (static visualization and interactive map generation)
- **Configuration & Environment**: `python-dotenv`
- **Testing**: `pytest`
- **Version Control**: Git & GitHub

---

## 8. Expected Inputs
The system is designed to take the following inputs:
- **Area of Interest (AOI)**: Bounding box coordinates `[min_lon, min_lat, max_lon, max_lat]` or a GeoJSON polygon representing the target geographical region.
- **Temporal Baseline & Target Dates**: Two or more observation dates (e.g., $T_1 = \text{2022-03-01}$, $T_2 = \text{2024-03-01}$) to measure change over time.
- **Analysis Focus**: User-specified interest (e.g., "Vegetation Health & Deforestation", "Drought & Water Extent", or "Post-Disaster Assessment").
- **Cloud Cover Threshold**: Maximum allowable cloud coverage percentage (e.g., $< 20\%$).

---

## 9. Expected Outputs
1. **Processed Spectral Indices**: Gridded rasters and statistical summaries of NDVI (Normalized Difference Vegetation Index), NDWI (Normalized Difference Water Index), or NBR (Normalized Burn Ratio).
2. **Temporal Difference Maps ($\Delta$ Index)**: Quantified change matrices highlighting areas of significant negative deviation (degradation/loss) and positive deviation (regrowth/recovery).
3. **Event Impact Summaries**: High-level severity statistics (e.g., total hectares affected, percentage change relative to baseline).
4. **Comprehensive Environmental Report**: A structured Markdown/PDF report containing executive findings, methodology, metric tables, key alerts, and recommendations.

---

## 10. Future Scope
- **Interactive Geospatial Web Dashboard**: Streamlit or FastAPI + React interface allowing users to draw bounding boxes on an interactive map.
- **Near-Real-Time (NRT) Monitoring**: Continuous polling of satellite feeds to trigger automated alerts when index degradation exceeds critical thresholds.
- **Advanced Machine Learning / CV Models**: Incorporating deep learning semantic segmentation models (e.g., U-Net for land-cover classification) if deemed beneficial.
- **Sensor Fusion**: Integrating optical imagery (Sentinel-2, Landsat) with synthetic aperture radar (Sentinel-1 SAR) to facilitate analysis through cloud cover.

---

## 11. Current Project Status
- **Current Phase**: **Phase 0 — Foundation**
- **Completed**:
  - Directory structure scaffolding
  - Baseline configuration templates (`.env.example`)
  - Dependency pinning (`requirements.txt`)
  - Repository ignores (`.gitignore`)
  - Architectural blueprint (`docs/architecture.md`)
  - Project execution roadmap (`docs/roadmap.md`)
  - Architectural decision records (`docs/project_decisions.md`)
  - Foundation entry point (`main.py`)
- **Next Phase**: **Phase 1 — Data Acquisition & Source Selection**
