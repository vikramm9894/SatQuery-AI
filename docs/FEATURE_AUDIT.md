# SatQuery AI — Feature & Architecture Audit

> **SIH26167 / ISRO Space Applications Centre Problem Statement**  
> Multimodal Agentic Remote Sensing Intelligence Copilot  
> **Date**: October 2026  
> **Audit Status**: Complete

---

## 1. Executive Summary of Audit

An exhaustive code audit of `vikramm9894/SatQuery-AI` was performed across both the core scientific GeoCV engine (`satquery/`), the API service layers (`satquery/api/` and `backend/app/`), the agentic orchestration frameworks, the frontend dashboard, and the test suites (148 passing tests).

### Key Findings
1. **Core Bi-Temporal Change Detection Engine (`satquery/change_detection/`)**:
   - **Status**: Production-grade, fully functional, 100% deterministic, 40/40 tests passing.
   - **Features Present**: STSF-Net pseudo-change suppression, Otsu thresholding, bimodal histogram confidence scoring, spectral differencing (NDVI, NDWI, NDBI, EVI, RVI, dB), morphological filtering, GeoJSON vector polygonization, geodetic equal-area re-projection, and execution trace.
   - **Action**: **PRESERVE** completely and extend with the requested 12 change classes (`vegetation_loss`, `vegetation_gain`, `water_expansion`, `water_reduction`, `urban_growth`, `urban_loss`, `bare_land_change`, `construction`, `deforestation`, `flooding`, `possible_damage`, `unknown_change`).

2. **Agent Orchestration Layers**:
   - There are currently two parallel agent implementations:
     - `satquery/agent/`: Adaptive DAG Planner, IntentParser, TaskExecutor, CrossModalArbitrationEngine, TraceStore, Specialists (ChangeDetector, VLM, SAR).
     - `backend/app/services/agent.py`: ReActAgent with Tool1 (VQA/Grounding), Tool3 (Change), Tool4 (Optical-SAR Fusion).
   - **Action**: **UNIFY** into a single master Agentic Orchestration layer where the Mission Planner, Sensor Router, Specialists (VQA, Captioning, Grounding, Change, SAR, Fusion), Physics Verification, Scientific Judge, and Confidence Engine operate in a unified DAG state machine with deterministic fallbacks.

3. **Multi-Sensor & SAR Capabilities**:
   - `satquery/change_detection/indices.py` supports SAR dB and RVI; `satquery/agent/specialists` and `backend/app/tools/tool4_fusion.py` contain SAR analysis and gated cross-modal fusion.
   - **Action**: Implement a dedicated `SARAnalysisAgent` with VV, VH, VV/VH ratio, dB, water/flood detection, speckle filtering, texture analysis, and integrate with the `ScientificJudge`.

4. **Physics Verification & Anti-Hallucination**:
   - Guardrails exist in `satquery/evaluation/guardrails.py` and `satquery/change_detection/vlm_guard.py`.
   - **Action**: Elevate to a central `PhysicsVerificationEngine` and `ScientificJudge` that cross-examines all VQA, grounding, and change predictions against physical indices and backscatter before emitting verified findings with `TARGET_NOT_FOUND` honest abstention.

5. **Frontend & Visualization**:
   - `frontend/` contains a Three.js 3D globe landing page, dual-panel dashboard, canvas image viewer, SVG bounding box overlay, before/after slider, and chat console.
   - **Action**: Upgrade with an interactive GIS map view (GeoJSON layers, polygon click inspection), synchronous before/after split slider, 3D Earth cockpit toggle, real-time SSE execution trace stream, and instant report download.

---

## 2. Feature Audit Matrix

| Feature | Existing Status | Keep / Modify / New | Files Involved | Priority |
| :--- | :--- | :--- | :--- | :---: |
| **Bi-temporal change detection** | Fully implemented, 40 unit/integration tests passing | **Keep & Extend** | `satquery/change_detection/*` | **P0** |
| **Spectral Indices (NDVI, NDWI, NDBI, EVI, RVI, dB)** | Fully implemented & tested | **Keep** | `satquery/change_detection/indices.py` | **P0** |
| **STSF Pseudo-Change Suppression** | Implemented & benchmarked | **Keep** | `satquery/change_detection/detector.py` | **P0** |
| **Bimodal Histogram Confidence** | Implemented (Otsu variance, valley-to-peak, area penalty) | **Keep & Integrate** | `satquery/change_detection/confidence.py` | **P0** |
| **Extended 12 Change Classes** | Partially (5 classes currently) | **Modify** (Add 7 classes + semantic mapper) | `satquery/change_detection/metrics.py` | **P0** |
| **Geospatial & CRS Engine** | High quality (Equal-area Albers, UTM, Affine, Shapely) | **Keep & Standardize** | `satquery/core/geodetic.py`, `raster_io.py` | **P0** |
| **GeoValidator Sanity Checks** | Fully implemented (CRS, overlap, inverted time, bounds) | **Keep** | `satquery/core/validator.py` | **P0** |
| **Mission Planner & Intent Parser** | Implemented in `satquery/agent/` | **Modify** (Support full prompt taxonomy) | `satquery/agent/planner.py`, `intent.py` | **P0** |
| **Sensor Router** | Basic rule in `backend/app/services/agent.py` | **New** (Dedicated Autonomous Router) | `satquery/agent/sensor_router.py` | **P0** |
| **VQA Agent** | Stub / mock in `tool1_vlm.py` & `vlm_feature.py` | **Modify / Enhance** (ModelProvider + Offline Fallback) | `satquery/agent/specialists/vqa.py` | **P0** |
| **Scene Captioning Agent** | Generic text in `vlm_feature.py` | **New** (Structured land cover / sensor description) | `satquery/agent/specialists/captioning.py` | **P0** |
| **Grounding Agent** | BBox heuristic in `tool1_vlm.py` | **Modify / Enhance** (Open-vocab + GeoJSON) | `satquery/agent/specialists/grounding.py` | **P0** |
| **Dedicated SAR Agent** | Partial in `tool4_fusion.py` | **Modify / Expand** (VV/VH, dB, flood, texture) | `satquery/agent/specialists/sar.py` | **P0** |
| **Optical + SAR Fusion** | Partial in `satquery/agent/fusion.py` & `tool4_fusion.py` | **Modify / Unify** (Gated cross-modal + judge) | `satquery/agent/fusion.py` | **P0** |
| **Physics Verification Engine** | Guardrails exist in `satquery/evaluation` | **New** (Deterministic physics check pipeline) | `satquery/physics/verifier.py` | **P0** |
| **Scientific Judge** | Arbitrator in `fusion.py` | **New / Expand** (Confirmed / Probable / Uncertain / Rejected / TARGET_NOT_FOUND) | `satquery/agent/judge.py` | **P0** |
| **Anti-Hallucination & TARGET_NOT_FOUND** | Partial numerical guardrails | **New** (Full abstention & threshold engine) | `satquery/agent/anti_hallucination.py` | **P0** |
| **Explainable Confidence Engine** | Split between `confidence.py` and `fusion.py` | **Modify / Unify** (Explainable 5-component breakdown) | `satquery/agent/confidence_engine.py` | **P0** |
| **RFC 7946 GeoJSON Export** | Fully implemented | **Keep** | `satquery/core/raster_io.py`, `exporter.py` | **P0** |
| **Evidence System (EvidenceRecord)** | MeasurementRecord exists | **Modify / Expand** (`EvidenceRecord` with audit trail) | `satquery/agent/schemas.py`, `evidence.py` | **P0** |
| **Execution Trace Streaming** | TraceStepEvent and TraceStore exist | **Keep & Wire to SSE** | `satquery/agent/trace.py`, `backend/app/main.py` | **P0** |
| **API Endpoints (REST v1)** | Dual implementations (`/api/v1` and `/api`) | **Modify / Unify** (Clean REST v1 OpenAPI) | `satquery/api/v1/*`, `backend/app/main.py` | **P0** |
| **Model Provider Abstraction** | Ollama/mock in `rs_vlm_backend.py` | **Modify / Expand** (Gemini, OpenAI, Ollama, Mock) | `satquery/models/provider.py` | **P1** |
| **Satellite Provider Abstraction** | None (Local files only) | **New** (Sentinel, ISRO, NASA GIBS, Local) | `satquery/providers/*` | **P1** |
| **Offline-First Mode** | Fully functional for change detection | **Keep & Guarantee** across all agents | `satquery/agent/fallback.py` | **P0** |
| **Storage Abstraction** | Local directory only | **Modify** (LocalStorage / S3 / MinIO interface) | `satquery/storage/base.py` | **P1** |
| **Session & History Manager** | In-memory dict with TTL | **Modify** (Persistent SQLite / Postgres DB) | `satquery/db/session_store.py` | **P1** |
| **Report Generation (PDF/MD/JSON)** | ReportLab PDF exporter in `exporter.py` | **Keep & Enhance** (Physics evidence & maps) | `satquery/reports/generator.py` | **P0** |
| **Interactive Map & Split Slider UI** | Slider exists in `frontend/index.html` | **Enhance** (Leaflet / OpenStreetMap + sync zoom) | `frontend/app.js`, `frontend/index.html` | **P1** |
| **3D Earth Cockpit** | Three.js globe exists on landing | **Keep & Connect** (Orbit visualization & 2D/3D toggle) | `frontend/app.js` | **P2** |
| **Security & Path Traversal** | Basic upload limit exists | **Modify** (Strict sanitization, CORS, headers) | `satquery/security/sanitizer.py` | **P1** |
| **Docker & Docker Compose** | Simple backend Dockerfile | **Modify** (Full multi-container config) | `Dockerfile`, `docker-compose.yml` | **P1** |

---

## 3. Preservation Safeguards for Vikram's GeoCV Engine

Under no circumstances should the following files or algorithmic logic be broken or replaced:
1. `satquery/change_detection/detector.py`: STSF-Net pseudo-change suppression filter (`suppress_pseudo_changes`), Gaussian differencing, Otsu auto-thresholding.
2. `satquery/change_detection/confidence.py`: Bimodal histogram separation confidence metric ($\omega \cdot v \cdot p$).
3. `satquery/core/validator.py`: Fast pre-execution checks on CRS, bounding box overlap, resolution ratio, and post-execution polygon bounding checks.
4. `satquery/core/raster_io.py`: GeoTIFF I/O, reprojection, and GeoJSON polygonization.
5. All 40 existing unit/integration tests in `tests/test_change_pipeline.py` and 23 tests in `tests/test_scientific_geocv.py` must continuously pass without regression.
