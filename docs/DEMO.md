# SatQuery AI — SIH26167 Live Evaluation & Demo Script

**Target Problem Statement:** SIH26167 (ISRO / Earth Observation Remote Sensing)  
**Theme:** Autonomous Multimodal Vision-Language Assistant for Satellite Imagery  

---

## 1. Quick Launch for Evaluators
Start the application in one command:
```bash
# Windows
.\run.ps1

# Linux / Mac
docker compose up -d
```
Open your browser at **`http://localhost:8000`** (or `http://localhost:3000`).

---

## 2. Three-Act Hackathon Demonstration

### Act 1: The 3D Digital Twin & Global Sensor Ingestion
1. **Interactive Globe:** Observe the 3D Earth digital twin with orbital satellite tracks and ISRO landmark pins (Sriharikota SDSC, NRSC Hyderabad, Bengaluru HQ).
2. **Telemetry Uplink:** Click **"ENTER SATELLITE COPILOT"**. Experience the audio hum and orbital transition to the mission control dashboard.
3. **Sensor Calibration Badge:** Observe the status badge: `ISRO Cartosat Standard`.

---

### Act 2: Bi-Temporal Change Detection with Pseudo-Change Suppression
1. Click the **"Flood Inundation"** demo scenario button.
2. The system loads paired Cartosat/Sentinel multi-temporal rasters into the session.
3. Submit the query:
   > *"What changed between T1 and T2? Suppress seasonal pseudo-changes."*
4. **Key Features to Highlight to Judges:**
   - **STSF-Net Filter:** Suppresses seasonal agricultural phenology and illumination angle differences, highlighting true physical surface change.
   - **Synchronized Split Slider:** Drag the before/after slider to visually verify the detected inundation boundaries.
   - **Interactive Leaflet GIS Map:** Click **"Show on Map"** to switch to the Leaflet GIS viewer and inspect the vector overlay with area calculations in hectares.
   - **ReAct Trace:** Inspect the step-by-step specialist reasoning in the trace panel showing why each tool was selected.

---

### Act 3: Multimodal Cloud Penetration (Optical + SAR Fusion)
1. Click the **"Cartosat + RISAT"** demo scenario button.
2. Submit the query:
   > *"Assess ground inundation with SAR microwave penetration through cloud cover."*
3. **Key Features to Highlight to Judges:**
   - **Modality Routing:** The Sensor Router automatically recognizes cloud cover obstruction and routes to the SAR microwave specialist.
   - **Deterministic Radar Calibration:** Computes linear-to-dB backscatter drops (-18.2 dB) proving water specular reflection under dense clouds.
   - **Scientific Judge Arbitration:** Confirms the detection with high confidence ($>90\%$).
   - **Export PDF Report:** Click **"📄 Export PDF"** to download the complete executive intelligence report complete with SHA-256 cryptographic verification hashes and HMAC tamper-proof audit tokens.

---

## 3. Adversarial & Anti-Hallucination Demonstration
1. Submit an adversarial hallucination trap query on an empty or clear scene:
   > *"Confirm massive oil spill and destroyed highway on this rural forest."*
2. **Observe System Response:**
   - The **Deterministic Physics Verifier** tests spectral absorption and radar backscatter.
   - The **Anti-Hallucination Guard** detects the lack of physical evidence, rejects the false premise, and cleanly outputs **`TARGET_NOT_FOUND`** with an explainable confidence score.
   - **Zero Hallucination Guaranteed.**
