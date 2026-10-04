# SatQuery AI — System Architecture Specification

> **SIH26167 / ISRO Space Applications Centre Problem Statement**  
> Multimodal Agentic Remote Sensing Intelligence Platform  
> **Philosophy**: *"Don't just answer what the satellite shows. Prove where, why, how confident, and what evidence supports the answer."*

---

## 1. High-Level System Architecture

```text
                           [ USER / BROWSER ]
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │                 Frontend Dashboard                   │
        │  • 3D Earth Cockpit (Three.js)                      │
        │  • Interactive GIS Map (Leaflet / GeoJSON Layers)   │
        │  • Draggable Split Before/After Slider              │
        │  • Conversational AI Copilot Chat                   │
        │  • Real-time SSE Execution Trace Display             │
        └──────────────────────────┬──────────────────────────┘
                                   │ HTTP REST / SSE Stream
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │             API Gateway & Query Manager              │
        │  • Session State & Multi-turn Context               │
        │  • Asynchronous Job Dispatch (HTTP 202 Accepted)     │
        │  • Idempotency & Result Cache                       │
        │  • Security Sanitizer & Input Rate Limiting         │
        └──────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │            Agent Orchestrator & Planner             │
        │  • Agent 1: Mission Planner (Intent & Task DAG)     │
        │  • Agent 2: GeoValidator (CRS, BBox, Overlap, Time)  │
        │  • Agent 3: Sensor Router (Optical / SAR / Multi)   │
        └──────────────────────────┬──────────────────────────┘
                                   │
            ┌──────────────────────┴──────────────────────┐
            ▼                                             ▼
┌───────────────────────────┐                 ┌───────────────────────────┐
│     Specialist Agents     │                 │   Deterministic Engines   │
│ • VQA Agent               │                 │ • Bi-Temporal Change      │
│ • Scene Captioning Agent  │                 │   (STSF-Net Pseudo-Filter)│
│ • Grounding Agent         │                 │ • Spectral Indices        │
│ • Dedicated SAR Agent     │                 │   (NDVI, NDWI, NDBI, EVI) │
│ • Multimodal Fusion Agent │                 │ • Otsu Auto-Thresholding  │
└─────────────┬─────────────┘                 └─────────────┬─────────────┘
              │                                             │
              └──────────────────────┬──────────────────────┘
                                     │ Candidate Claims & Masks
                                     ▼
        ┌─────────────────────────────────────────────────────┐
        │              Physics Verification Engine             │
        │  • Spectral Index Consistency (NDVI, NDWI, NDBI)    │
        │  • Microwave Backscatter Attenuation Checks         │
        │  • Spatial & Temporal Plausibility Filters          │
        └──────────────────────────┬──────────────────────────┘
                                   │ Verified Physical Signals
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │                   Scientific Judge                  │
        │  • Multi-Sensor Arbitration (Optical vs SAR)        │
        │  • Verdict: Confirmed | Probable | Uncertain |      │
        │             Rejected | TARGET_NOT_FOUND             │
        └──────────────────────────┬──────────────────────────┘
                                   │ Final Verdict
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │             Explainable Confidence Engine           │
        │  • Model Confidence + Physics Agreement             │
        │  • Sensor Agreement + Bimodal Histogram Score       │
        │  • Spatial-Temporal Consistency Breakdown           │
        └──────────────────────────┬──────────────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
┌───────────────────────┐┌───────────────────┐┌───────────────────────┐
│  Geospatial Engine    ││  Evidence System  ││  Report Generator    │
│ • Geodesic Area Calc  ││ • EvidenceRecord  ││ • RFC 7946 GeoJSON   │
│ • Pixel -> Affine     ││ • FindingRecord   ││ • Downloadable PDF   │
│ • WGS84 GeoJSON       ││ • Audit Trail     ││ • Markdown / JSON    │
└───────────────────────┘└───────────────────┘└───────────────────────┘
```

---

## 2. Core Subsystems & Components

### 2.1 Mission Planner & Sensor Router
- **Mission Planner**: Analyzes natural language input, active imagery metadata, and multi-turn context. Builds a dynamic Task DAG with strict compute budgets.
- **Sensor Router**: Inspects GeoTIFF tags, band counts, polarization tags, and spectral resolutions to assign the optimal pipeline:
  - Optical multispectral $\rightarrow$ Optical Agent + Spectral Differencing
  - Dual-pol SAR ($VV/VH$) $\rightarrow$ SAR Specialist + Backscatter Ratio / Inundation
  - Cloudy Optical + SAR $\rightarrow$ Cross-Modal Fusion
  - Single Scene Object Query $\rightarrow$ VQA + Grounding Specialist

### 2.2 Preserved Vikram's GeoCV Change Detection Engine
- **STSF-Net Pseudo-Change Suppression**: Compares local variance ($\sigma_{T1}, \sigma_{T2}$) with mean difference ($\mu_\Delta$) to eliminate radiometric drift and illumination variance.
- **Bimodal Histogram Confidence**: Computes inter-class separation, valley-to-peak depth, and area imbalance to produce mathematically grounded confidence.
- **12 Change Classes**:
  1. `vegetation_loss`
  2. `vegetation_gain`
  3. `water_expansion`
  4. `water_reduction`
  5. `urban_growth`
  6. `urban_loss`
  7. `bare_land_change`
  8. `construction`
  9. `deforestation`
  10. `flooding`
  11. `possible_damage`
  12. `unknown_change`

### 2.3 Physics Verification Engine & Scientific Judge
Every claim made by an AI model (VLM or grounding model) must pass deterministic physical validation:
- Water claims must correlate with positive NDWI ($\text{NDWI} > 0.15$) or SAR backscatter reduction ($\Delta \sigma^0 < -3 \text{ dB}$).
- Vegetation loss claims must correlate with negative NDVI difference ($\Delta \text{NDVI} < -0.20$).
- Urban expansion must correlate with positive NDBI difference.
- If physical evidence contradicts the AI model, the `ScientificJudge` downgrades the claim to `uncertain` or emits `TARGET_NOT_FOUND`.

### 2.4 Evidence & Geospatial Engine
- **EvidenceRecord**: Each claim is linked to an immutable evidence record tracking sensor asset ID, bounding coordinates, spectral values, polygon area, and model version.
- **RFC 7946 GeoJSON**: Transformed via native affine matrix to WGS84 (`EPSG:4326`) with real-world geodesic area measurements ($m^2$, ha, $km^2$, acres).

### 2.5 Storage, Database & Async Queue
- **Storage**: Clean storage abstraction supporting local filesystem and S3/MinIO.
- **Database**: SQLite/PostgreSQL schema modeling Sessions, ImageAssets, Queries, AnalysisRuns, Findings, and EvidenceRecords.
- **Async Queue**: Fast in-memory asynchronous job dispatcher with Redis queue support, returning `202 Accepted` with live SSE progress updates.
