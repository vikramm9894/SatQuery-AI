# SatQuery AI — Multi-Agent Architecture & Specialist System

**Architecture:** Distributed ReAct Specialist Swarm with Scientific Arbitration  
**Standard:** ISRO SIH26167 Intelligent Ground Station Operations

---

## 1. Multi-Agent Ecosystem Overview
SatQuery AI departs from monolithic LLM wrappers by deploying a specialized multi-agent hierarchy where each agent possesses domain expertise in a specific remote-sensing or computational discipline.

```
                   User Question / Command
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
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
 [Optical GeoCV]       [SAR Specialist]     [Grounding Agent]
   (STSF-Net)             (Lee Radar)        (Open-Vocab BBox)
        │                     │                      │
        └─────────────────────┼──────────────────────┘
                              │
                              ▼
            [Deterministic Physics Verifier Engine]
                              │
                              ▼
                  [Scientific Judge Agent]
                              │
                              ▼
              [Anti-Hallucination Guardrail]
                              │
                              ▼
        Verified Georeferenced Answer + Evidence Chain
```

---

## 2. Agent Catalog

| Agent Name | Module | Primary Capability | Scientific Backing |
| :--- | :--- | :--- | :--- |
| **Intent Parser** | `satquery.agent.intent_parser` | Query intent classification & entity extraction | Categorizes queries into change detection, object search, or inundation |
| **Adaptive Planner** | `satquery.agent.planner` | Formulates deterministic ReAct execution steps | Prevents unnecessary tool invocation |
| **Sensor Router** | `satquery.agent.sensor_router` | Modality matching (Optical, SAR, Panchromatic) | Directs cloud-penetration queries to microwave SAR |
| **GeoCV Detector** | `satquery.change_detection` | Bi-temporal change detection & class metrics | STSF-Net pseudo-change suppression & Otsu thresholding |
| **SAR Specialist** | `satquery.agent.specialists.sar` | Microwave radar calibration & water extraction | Linear-to-dB conversion & Lee speckle filter |
| **Grounding Specialist**| `satquery.agent.specialists.grounding`| Bounding box localization of objects | Normalized spatial coordinates & RFC 7946 Polygons |
| **Captioning Specialist**| `satquery.agent.specialists.captioning`| Dense semantic scene descriptions | Structured land-cover & hydrology reporting |
| **VQA Specialist** | `satquery.agent.specialists.vqa` | Spatial question answering | Physical grounding with region citations |
| **Physics Verifier** | `satquery.physics.verifier` | Non-negotiable physical checks | NDVI, NDWI, NDBI, and radar backscatter boundaries |
| **Scientific Judge** | `satquery.agent.judge` | Multi-sensor arbitration | Cross-modal truth resolution & conflict mediation |
| **Anti-Hallucination Guard**| `satquery.agent.anti_hallucination`| Confidence enforcement & honest abstention | Emits `TARGET_NOT_FOUND` if evidence score < 0.40 |

---

## 3. The ReAct Loop (Reason + Act + Observe)
At each step $t$, the active specialist:
1. **Thoughts / Reason:** Evaluates the current state and mission objective.
2. **Action:** Invokes a deterministic calculation or model inference.
3. **Observation:** Receives numeric matrices, masks, or spectral indices.
4. **Confidence Rating:** Computes an explainable step score.
5. **Trace Emission:** Appends the step to the immutable `AgentTraceStep` audit log.
