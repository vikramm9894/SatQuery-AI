# SatQuery AI — API Reference Specification

**Version:** 3.0.0  
**Specification:** Smart India Hackathon / ISRO Problem Statement SIH26167  
**Base URL:** `http://localhost:8000/api`

---

## 1. Overview
SatQuery AI provides an asynchronous, ReAct-driven REST API for multimodal Earth Observation intelligence. The API allows clients to upload multi-sensor satellite rasters (Optical, SAR, Multispectral), execute natural-language queries, track step-by-step specialist reasoning, render vector overlays, and export cryptographically sealed intelligence reports.

---

## 2. Core Endpoints

### 2.1 System Health
`GET /api/health`
Returns system status, active version, and hardware tier.

**Response:**
```json
{
  "status": "healthy",
  "service": "SatQuery AI",
  "version": "3.0.0",
  "gpu_allowed": true
}
```

---

### 2.2 Active Tools & Specialists Registry
`GET /api/tools`
Lists all active specialist agents, execution modes, and hardware acceleration tiers.

**Response:**
```json
[
  {
    "name": "geocv_change_detector",
    "description": "Bi-temporal change detection with STSF-Net pseudo-change suppression",
    "tier_available": "gpu",
    "active_mode": "real_model",
    "model_version": "v3.0.0"
  },
  {
    "name": "sar_specialist",
    "description": "SAR microwave radar calibration, speckle filtering, and flood inundation mapping",
    "tier_available": "gpu",
    "active_mode": "real_model",
    "model_version": "v1.2.0"
  },
  {
    "name": "grounding_specialist",
    "description": "Open-vocabulary geospatial object and parcel boundary detection",
    "tier_available": "gpu",
    "active_mode": "real_model",
    "model_version": "v2.0.0"
  }
]
```

---

### 2.3 Input Validation & Co-Registration
`POST /api/validate-inputs`
Validates uploaded GeoTIFFs, checks CRS consistency, spatial resolution, and performs pixel-level co-registration.

**Headers:** `Content-Type: multipart/form-data`  
**Parameters:**
- `files`: One or more raster files (GeoTIFF, PNG, JPEG).
- `session_id` (optional): Target session UUID.

**Response (ValidationResult):**
```json
{
  "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "valid": true,
  "mode": "bi_temporal",
  "images": [
    {
      "id": "img_001",
      "filename": "T1.tif",
      "crs": "EPSG:4326",
      "bounds": [72.82, 18.95, 72.95, 19.12],
      "resolution_m": 0.65,
      "width": 1024,
      "height": 1024,
      "bands": 3,
      "sensor_type": "optical",
      "checksum_sha256": "8a35f7...",
      "preview_url": "/api/session/9b1deb4d/preview/img_001"
    }
  ],
  "overlap_area_m2": 450000.0,
  "overlap_pct": 100.0,
  "is_coregistered": true,
  "warnings": [],
  "errors": []
}
```

---

### 2.4 Pre-Packaged Demo Scenarios
`POST /api/load-sample`
Instantly loads a pre-packaged ISRO Earth-observation benchmark scenario.

**Request Body:**
```json
{
  "session_id": "demo_session_abc",
  "scenario_id": "flood"
}
```
*Supported `scenario_id` values:* `"flood"`, `"deforestation"`, `"urban"`, `"cartosat_sar"`.

---

### 2.5 Autonomous ReAct Query
`POST /api/query`
The primary conversational intelligence endpoint. Executes mission planning, invokes appropriate specialists, runs physics verification, checks anti-hallucination guardrails, and returns an auditable response.

**Request Body:**
```json
{
  "session_id": "demo_session_abc",
  "query": "Assess ground inundation with SAR microwave penetration through cloud cover.",
  "force_mode": "auto"
}
```

**Response (QueryResponse):**
```json
{
  "session_id": "demo_session_abc",
  "query": "Assess ground inundation with SAR microwave penetration through cloud cover.",
  "final_answer": "Confirmed 18.4 hectares of water inundation. Radar backscatter specular drop verified at -19.4 dB.",
  "confidence": 0.912,
  "confidence_breakdown": {
    "model": 0.92,
    "physics": 0.95,
    "spatial": 0.88
  },
  "sensor_calibration_badge": "Cartosat-2S & RISAT-1A Paired",
  "execution_mode": "hybrid",
  "trace": [
    {
      "step_number": 1,
      "tool_called": "sar_specialist",
      "why_this_tool": "Penetrate monsoon cloud cover to measure specular backscatter attenuation",
      "step_confidence": 0.94,
      "observation_summary": "Specular radar attenuation detected over 18.4 ha agricultural plain."
    }
  ],
  "composite_overlays": {
    "features": [],
    "bboxes": [
      {
        "ymin": 0.22,
        "xmin": 0.35,
        "ymax": 0.58,
        "xmax": 0.72,
        "label": "Water Inundation",
        "confidence": 0.91,
        "sensor": "risat1a_sar"
      }
    ]
  },
  "metrics_summary": {
    "inundated_area_ha": 18.4,
    "mean_sar_db": -19.4
  },
  "run_signature_hash": "a1b2c3d4e5f60123456789abcdef0123456789abcdef0123456789abcdef01",
  "report_tamper_token": "hmac_tamper_token_99182",
  "generated_at": "2026-10-05T00:15:00Z"
}
```

---

### 2.6 Report Export (PDF, GeoJSON, Markdown, JSON)
`GET /api/export-report?session_id={session_id}&format={pdf|geojson|markdown|json}`  
`POST /api/export-report`

Exports intelligence verdicts into downloadable official formats:
- `pdf`: Executive ReportLab document with tamper seals and audit tables (`application/pdf`).
- `geojson`: RFC 7946 compliant FeatureCollection with WGS84 coordinates (`application/geo+json`).
- `markdown`: Publication-grade markdown summary (`text/markdown`).
- `json`: Canonical audit dictionary (`application/json`).
