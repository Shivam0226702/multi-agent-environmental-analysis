# Project Roadmap: Multi-Agent Environmental Analysis System

This roadmap delineates the phased lifecycle for developing the Multi-Agent Environmental Analysis System. Each phase builds iteratively on the deliverables of the previous phase.

---

## Roadmap Overview

| Phase | Title | Focus Area | Status |
| :--- | :--- | :--- | :--- |
| **Phase 0** | **Foundation** | Repository architecture, documentation, configuration, and scaffolding | **In Progress / Current** |
| **Phase 1** | **Data Acquisition** | Satellite data source selection, API connectors, and sample dataset curation | Upcoming |
| **Phase 2** | **Data Preprocessing** | Geospatial clipping, reprojection, band calibration, and cloud masking | Upcoming |
| **Phase 3** | **Individual Analysis Agents** | Single-responsibility agents (Vegetation, Disaster, Temporal) & specialized tools | Upcoming |
| **Phase 4** | **LangGraph Orchestration** | State graph architecture, inter-agent message passing, and conditional routing | Upcoming |
| **Phase 5** | **Temporal & Environmental Analysis** | Multi-date difference quantification, anomaly detection, and degradation identification | Upcoming |
| **Phase 6** | **Report Generation** | Automated synthesis, statistical summaries, visual chart embedding, and markdown reporting | Upcoming |
| **Phase 7** | **Testing & Evaluation** | Unit test suite, integration tests, edge-case handling (cloudiness, missing bands) | Upcoming |
| **Phase 8** | **Final Demo & Documentation** | End-to-end demonstration, reproducible notebooks, slide deck, and final report | Upcoming |

---

## Phase Details

### Phase 0 — Foundation
- **Description**: Establish a clean, scalable project layout adhering to Python engineering best practices. Set up environment configuration templates, dependency bounds, version control hygiene, and architectural documentation.
- **Expected Deliverables**:
  - Modular project directory structure (`agents/`, `workflows/`, `tools/`, `data/`, etc.).
  - `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/project_decisions.md`.
  - `.gitignore`, `.env.example`, minimal `requirements.txt`, and entry point `main.py`.

---

### Phase 1 — Data Acquisition
- **Description**: Research and select reliable satellite/environmental data sources suitable for engineering students (e.g., Copernicus Sentinel-2 STAC API, Planetary Computer, or USGS Landsat). Implement a basic data collection tool and curate lightweight offline sample datasets in `data/sample/` for offline/reproducible runs.
- **Expected Deliverables**:
  - `tools/data_loader.py` or STAC client connector.
  - Curated sample multi-spectral imagery scenes covering two distinct dates over a target test AOI.
  - Data ingestion documentation in `docs/data_sources.md`.

---

### Phase 2 — Data Preprocessing
- **Description**: Build standard geospatial preprocessing routines. Handle bounding box clipping, CRS alignment, cloud masking, and scaling raw digital numbers to surface reflectance values.
- **Expected Deliverables**:
  - Preprocessing module (`tools/preprocessor.py`).
  - Standardized GeoTIFF outputs saved in `data/processed/`.
  - Verification script ensuring spatial and dimensional alignment across temporal scenes.

---

### Phase 3 — Individual Analysis Agents
- **Description**: Implement individual specialized agents independently. Develop deterministic tools for spectral index calculation (NDVI, NDWI, NBR) and wrap them with agent interfaces capable of interpreting the results.
- **Expected Deliverables**:
  - `tools/spectral_indices.py` (pure Python / NumPy index formulas).
  - Vegetation Agent (`agents/vegetation_agent.py`).
  - Disaster / Anomaly Agent (`agents/disaster_agent.py`).
  - Standalone unit tests for each agent's tool execution.

---

### Phase 4 — LangGraph Orchestration
- **Description**: Construct the LangGraph state machine to orchestrate interaction between agents. Define the shared state schema, graph nodes, conditional edges, and error handling branches.
- **Expected Deliverables**:
  - State model (`workflows/state.py`) using Pydantic.
  - Graph definition (`workflows/graph.py`) linking Orchestrator, Data Agents, Analysis Agents, and Report Agent.
  - Traceable graph execution logs.

---

### Phase 5 — Temporal & Environmental Analysis
- **Description**: Implement multi-date comparative logic. Compute pixel-level difference matrices ($\Delta \text{NDVI}$), detect areas of notable degradation or recovery, and compute zonal statistics.
- **Expected Deliverables**:
  - Temporal comparison tool and agent (`agents/temporal_agent.py`).
  - Change detection raster outputs and spatial masks in `results/`.
  - Statistical summary tables (percentage area degraded, mean index shift).

---

### Phase 6 — Report Generation
- **Description**: Develop the Report / Conclusion Agent to synthesize intermediate analytical artifacts, tables, and visualization charts into an executive-level environmental report.
- **Expected Deliverables**:
  - `agents/report_agent.py` capable of synthesizing Markdown and HTML/PDF summaries.
  - Visualization generator producing clean time-series plots and spatial difference figures in `results/`.
  - Sample generated reports stored in `reports/`.

---

### Phase 7 — Testing & Evaluation
- **Description**: Implement comprehensive testing across the pipeline. Validate handling of missing data, excessive cloud cover, invalid geographic coordinates, and model API timeouts.
- **Expected Deliverables**:
  - Test suite in `tests/` covering tools, state validation, and agent nodes.
  - Benchmark evaluation comparing multi-agent outputs against expected ground metrics on sample test sites.

---

### Phase 8 — Final Demo & Documentation
- **Description**: Finalize end-to-end user experience, interactive demonstration notebook, and complete project documentation suitable for academic/project evaluation.
- **Expected Deliverables**:
  - Interactive Jupyter notebook (`notebooks/demo.ipynb`) illustrating complete workflow run.
  - Final project presentation slides and comprehensive report.
  - Tagged release / versioned GitHub repository.
