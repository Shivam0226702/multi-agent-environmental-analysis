# Architectural Decision Records (ADRs)

This document formalizes the key architectural, structural, and design decisions made for the **Multi-Agent Environmental Analysis System**.

---

## ADR-001: Why a Multi-Agent Architecture?

### Context
Analyzing environmental satellite data is inherently multi-disciplinary and multi-stage. It requires heterogeneous skills: API querying, raster manipulation, radiometric calculations, geospatial time-series statistics, disaster footprint identification, and technical report synthesis.

### Alternatives Considered
1. **Single Monolithic LLM Prompt**: Passing all instructions and data summaries to a single prompt.
2. **Sequential Procedural Scripting (Pipeline without Agents)**: Traditional static Python pipeline without LLM reasoning.
3. **Multi-Agent Architecture**: Discrete, specialized agents coordinated via a central orchestrator.

### Decision
Adopt a **Multi-Agent Architecture**.

### Rationale
- **Separation of Concerns**: Each agent possesses a constrained domain (e.g., the Vegetation Agent deals strictly with vegetative biophysical metrics; the Data Collection Agent deals strictly with catalog querying).
- **Reduced Context Window & Prompt Pollution**: An agent only receives the specific data slice, schemas, and tools it needs to fulfill its role, preventing prompt bloat and instruction dilution.
- **Explainability & Traceability**: When an anomaly or error occurs, the exact sub-agent and tool responsible are immediately identifiable.
- **Student Team Scalability**: Different team members can independently develop, test, and optimize specific agents without interfering with other components.

---

## ADR-002: Why LangGraph for Orchestration?

### Context
Coordinating multiple agents requires managing shared memory, passing intermediate artifacts, and executing conditional logic (e.g., branching into disaster analysis only if an extreme event is flagged or requested).

### Alternatives Considered
1. **Pure Autogen / CrewAI**: Highly conversational multi-agent frameworks.
2. **Custom While-Loops & Dict Passing**: Ad-hoc routing in vanilla Python.
3. **LangGraph**: State-machine based directed graph orchestration built on top of LangChain.

### Decision
Target **LangGraph** as the primary orchestration framework.

### Rationale
- **Deterministic State Graphs**: LangGraph models workflows as explicit nodes and edges. For an engineering project, predictable and debuggable state transitions are vastly superior to chaotic conversational loops.
- **Cyclic & Conditional Workflows**: Real-world satellite processing often requires retries (e.g., "cloud cover too high $\rightarrow$ query alternate date"). LangGraph handles cyclic graphs and conditional routing natively.
- **Strictly Typed State**: LangGraph natively leverages Python `TypedDict` or Pydantic schemas, ensuring data contracts are respected across all agent boundaries.
- **Human-in-the-Loop Readiness**: LangGraph supports breakpoints, permitting user confirmation (e.g., confirming AOI or scene selection) before triggering heavy compute steps.

---

## ADR-003: Why Starting with a Modular Architecture?

### Context
In academic and prototype projects, there is a temptation to write all code in a single notebook or script (`analysis.py`). While initially quick, this quickly collapses under the weight of dependencies, state management, and testing.

### Decision
Enforce a clean, modular directory structure from Phase 0 before any agent or ML code is written.

### Rationale
- **Prevents Spaghetti Code**: Clearly demarcating where configuration, tools, models, and workflows live prevents cross-contamination of logic.
- **Facilitates Automated Testing**: Isolated modules (such as mathematical index calculators in `tools/`) can be unit tested without having to spin up an LLM or download gigabytes of satellite rasters.
- **Easier Git Management**: Clean directory boundaries minimize git merge conflicts across multi-student engineering teams.

---

## ADR-004: Why Separating Agents, Tools, Workflows, Data, and Results?

### Context
A robust AI architecture distinguishes between:
- **Decision Makers** (Agents)
- **Action Executors** (Tools)
- **Process Orchestration** (Workflows)
- **Input Artifacts** (Data)
- **Output Artifacts** (Results & Reports)

### Decision
Establish strict physical separation into:
- `agents/`: Contains LLM prompt definitions, system roles, and reasoning boundaries.
- `tools/`: Contains pure, deterministic Python functions (file operations, API requests, raster math) that agents can call. Agents do not contain heavy compute code directly.
- `workflows/`: Contains graph definitions, state models, and edge conditions coordinating the agents.
- `data/`: Segregated into `raw/`, `processed/`, and `sample/` to preserve data provenance and immutability.
- `results/`: Stores raw numerical outputs, GeoTIFFs, and matplotlib figures.
- `reports/`: Stores human-readable synthesis documents (Markdown/PDF).

### Rationale
- **Tools are Reusable & Testable Independently**: A mathematical formula (e.g., NDVI calculation) is deterministic; it does not need an LLM to run. Keeping it in `tools/` allows instant testing via standard `pytest` fixtures without consuming API tokens.
- **Data Immutability**: Raw satellite imagery should never be modified in-place; placing it in `data/raw/` ensures a clear trail to `data/processed/`.
- **Output Traceability**: Keeping intermediate computation results (`results/`) distinct from polished deliverables (`reports/`) ensures that end-users receive clean intelligence while developers retain full debugging logs.
