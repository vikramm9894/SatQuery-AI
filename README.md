# SatQuery AI — Multimodal Agentic Satellite Intelligence Platform

> **Smart India Hackathon / ISRO Problem Statement SIH26167**  
> **Autonomous Vision-Language Remote Sensing Assistant for Optical, SAR, and Paired Satellite Data**  
> **Core Architecture:** Multi-Agent Specialist Swarm · Deterministic Physics Verifier · Vikram's GeoCV Engine · 3D Earth Digital Twin · Tamper-Proof Intelligence Reports

[![CI/CD Pipeline](https://github.com/vikramm9894/SatQuery-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/vikramm9894/SatQuery-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10 | 3.11 | 3.12](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![ISRO: SIH26167](https://img.shields.io/badge/ISRO-SIH26167-orange.svg)](https://www.sih.gov.in/)
[![Tests: 100% Passing](https://img.shields.io/badge/Tests-120%2B%20Passing-brightgreen.svg)](https://github.com/vikramm9894/SatQuery-AI)

---

## 1. Executive Summary

**SatQuery AI** is an enterprise-grade multimodal satellite intelligence copilot designed for ISRO ground station analysts, disaster management teams, and remote-sensing researchers. Non-expert users can upload satellite imagery (Cartosat-2S, RISAT-1A, Sentinel, Landsat, PlanetScope) and ask arbitrary natural-language questions.

Unlike monolithic black-box LLM wrappers, SatQuery AI employs an **autonomous ReAct multi-agent swarm** coupled with **deterministic physics verification** and **cryptographic chain-of-custody seals**. If evidence fails physical boundary checks, the system exercises honest abstention (`TARGET_NOT_FOUND`) rather than hallucinating answers.

---

## 2. Core Architectural Pillars

```
                                 User Mission Query
                                         │
                                         ▼
                             [Agent 1: Intent Parser]
                                         │
                                         ▼
                            [Agent 2: Adaptive Planner]
                                         │
                                         ▼
                             [Agent 3: Sensor Router]
                                         │
            ┌────────────────────────────┼───────────────────────────┐
            ▼                            ▼                           ▼
    [Optical GeoCV]               [SAR Specialist]          [Grounding Agent]
      (STSF-Net)                    (Lee Radar)             (Open-Vocab BBox)
            │                            │                           │
            └────────────────────────────┼───────────────────────────┘
                                         │
                                         ▼
                       [Deterministic Physics Verifier]
                        (NDVI, NDWI, NDBI, SAR dB limits)
                                         │
                                         ▼
                            [Scientific Judge Agent]
                        (Multi-Sensor Evidence Arbiter)
                                         │
                                         ▼
                         [Anti-Hallucination Guardrail]
                          (Honest Abstention < 0.40)
                                         │
                                         ▼
              Verified Answer + Interactive GIS + Tamper-Proof Reports
```

1. **Vikram's GeoCV Engine (Preserved Core)**:
   - STSF-Net pseudo-change suppression filter (eliminates radiometric drift and solar angle noise).
   - Otsu automated thresholding with bimodal histogram separation confidence ($0.0 - 1.0$).
   - Strict spatial co-registration validation across Coordinate Reference Systems (CRS).
2. **SAR Microwave Radar Intelligence**:
   - Radiometric linear-to-dB conversion ($\sigma^0$).
   - Lee speckle filtering and radar texture variance analysis.
   - All-weather cloud-penetrating specular water inundation detection.
3. **Deterministic Physics Verifier**:
   - Non-negotiable spectral boundary enforcement for NDVI, NDWI, NDBI.
   - Cross-checks optical claims against microwave radar backscatter drop.
4. **Interactive Visualization & Digital Twin**:
   - Three.js 3D WebGL Earth globe with orbital satellite tracks and ISRO landmark pins.
   - Synchronized dual-raster before/after split slider.
   - Leaflet GIS map with RFC 7946 GeoJSON vector polygons and area metrics (ha, $m^2$).
5. **Cryptographic Proof of Custody**:
   - Deterministic SHA-256 run signature hashes binding inputs, model versions, and outputs.
   - HMAC tamper-proof audit tokens embedded in downloadable PDF, GeoJSON, Markdown, and JSON reports.

---

## 3. Repository Structure

```text
SatQuery-AI/
├── .github/workflows/ci.yml         # Automated GitHub Actions CI/CD pipeline
├── Dockerfile                       # Multi-stage production container build
├── docker-compose.yml               # Multi-service stack (api, worker, redis, frontend)
├── .env.example                     # Enterprise environment configuration template
├── README.md                        # Master repository documentation
├── requirements.txt                 # Unified dependency specifications
├── run.ps1 / run.bat                # One-click startup scripts for Windows
├── satquery/                        # Production Geospatial Intelligence Library
│   ├── agent/                       # Multi-agent swarm (Router, Planner, Judge, Guard)
│   │   ├── specialists/             # SAR, VQA, Grounding, Captioning specialist agents
│   │   ├── judge.py                 # Scientific multi-sensor arbitrator
│   │   ├── anti_hallucination.py    # Honest abstention & risk tier manager
│   │   └── confidence_engine.py     # Composite explainable confidence scoring
│   ├── change_detection/            # Vikram's GeoCV Engine (STSF-Net, Otsu, Metrics)
│   ├── core/                        # Geospatial math, Affine coordinate reprojection, CRS
│   ├── db/                          # SQLite / Postgres persistence engine
│   ├── models/                      # Multi-modal LLM/VLM providers & offline fallbacks
│   ├── physics/                     # Deterministic spectral index & SAR verifiers
│   ├── providers/                   # Satellite ingest providers (Local, ISRO, Sentinel, NASA)
│   ├── queue/                       # Asynchronous non-blocking job dispatcher
│   ├── reports/                     # Multi-format report generator (PDF, GeoJSON, MD, JSON)
│   ├── security/                    # Path traversal, MIME magic bytes, prompt injection guards
│   └── storage/                     # Partitioned local storage abstraction
├── backend/                         # FastAPI Application Service Layer
│   ├── app/main.py                  # REST API endpoints (/query, /validate, /export-report)
│   └── tests/                       # Backend integration and test client suites
├── frontend/                        # Interactive High-Tech Mission Control UI
│   ├── index.html                   # Glassmorphic layout, Leaflet container, 3D Globe mount
│   ├── style.css                    # Futuristic dark theme styling, badges, GIS controls
│   └── app.js                       # Three.js globe, Leaflet GIS map, ReAct trace renderer
├── demo_data/                       # Pre-packaged ISRO scenarios (flood, forest, urban)
├── docs/                            # Complete Documentation Suite
│   ├── ARCHITECTURE.md              # System design & multi-agent sequence diagrams
│   ├── API.md                       # Comprehensive REST API reference & schemas
│   ├── FEATURES.md                  # 32-feature capabilities matrix
│   ├── DEPLOYMENT.md                # Docker, Kubernetes, and bare-metal guide
│   ├── SECURITY.md                  # Trust architecture & defense-in-depth policy
│   ├── AGENTS.md                    # Specialist agent catalog & ReAct specification
│   ├── DEMO.md                      # SIH26167 live evaluation script for judges
│   └── FEATURE_AUDIT.md             # Baseline feature preservation audit
└── tests/                           # Master Automated Test Suites (120+ tests)
```

---

## 4. Quickstart

### Option A: One-Click Startup (Windows)
```powershell
.\run.ps1
```
Open **`http://localhost:8000`** in your browser.

### Option B: Docker Compose (All Platforms)
```bash
cp .env.example .env
docker compose up --build -d
```
- **Frontend UI:** `http://localhost:3000`
- **Backend API & Swagger Docs:** `http://localhost:8000/docs`

### Option C: Manual Python Setup
```bash
python -m venv .venv
# On Windows: .venv\Scripts\Activate.ps1 | On Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 5. Running the Test Suites

All tests run locally in seconds with **zero external API or GPU dependencies**:

```bash
# Run the complete test suite across all 7 platform tiers
python -m pytest tests/test_change_pipeline.py \
  tests/test_geospatial_foundation.py \
  tests/test_ai_core_specialists.py \
  tests/test_multimodal_physics_judge.py \
  tests/test_data_infrastructure.py \
  tests/test_reports.py \
  tests/test_security_sanitizer.py \
  tests/agent \
  backend/tests
```

**Result: 120+ passed, 0 failures, 100% green.**

---

## 6. Smart India Hackathon (SIH26167) Compliance

| Requirement ID | Problem Statement Requirement | SatQuery AI Implementation |
| :--- | :--- | :--- |
| **REQ-01** | Multi-temporal satellite change detection | Vikram's GeoCV engine with STSF-Net pseudo-change suppression. |
| **REQ-02** | Optical + SAR microwave radar fusion | Dedicated SAR specialist with linear-to-dB conversion and cloud penetration. |
| **REQ-03** | Natural language conversational interface | Autonomous ReAct agent with auditable step-by-step reasoning trace. |
| **REQ-04** | Quantitative, explainable confidence | Composite engine combining physics checks, spatial coherence, and bimodal Otsu scores. |
| **REQ-05** | Anti-hallucination & safety | Deterministic physics verifier enforcing `TARGET_NOT_FOUND` honest abstention. |
| **REQ-06** | Interactive geospatial visualization | Dual-raster before/after split slider, Leaflet GIS map, and 3D Earth digital twin. |
| **REQ-07** | Official audit report generation | Multi-format exports (PDF with ReportLab, RFC 7946 GeoJSON, Markdown, JSON). |
| **REQ-08** | Domestic ISRO sensor support | Calibrated for Cartosat-2S (0.65m GSD) and RISAT-1A microwave radar. |

---

## 7. License & Credits

Developed for **Smart India Hackathon / ISRO Problem Statement SIH26167**.  
Licensed under the [MIT License](LICENSE).
