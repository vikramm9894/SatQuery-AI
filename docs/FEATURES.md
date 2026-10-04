# SatQuery AI — Platform Feature Catalogue

**Problem Statement:** Smart India Hackathon / ISRO SIH26167  
**Platform Architecture:** Multi-Agent Multimodal Satellite Intelligence Assistant

---

## 1. Vision & Optical Intelligence
1. **STSF-Net Pseudo-Change Suppression**: Spatial-temporal-spectral filtering suppressing seasonal illumination, cloud shadows, and crop phenology changes.
2. **Otsu Adaptive Thresholding**: Robust automated thresholding computing optimal bi-level segmentations.
3. **Bimodal Histogram Confidence**: Quantitative measure verifying whether difference maps exhibit clean binary separation or noise.
4. **Raster Ingestion & CRS Validator**: Validates coordinate reference systems, pixel resolution, band count, and spatial extents.
5. **Pixel-Level Co-Registration**: Automatic affine alignment ensuring sub-pixel spatial consistency across multi-temporal rasters.
6. **Open-Vocabulary Object Grounding**: Detection of buildings, roads, bridges, water bodies, and construction sites with normalized bounding boxes.
7. **Dense Semantic Captioning**: Automated structured land-cover, hydrology, and infrastructure descriptions.
8. **Visual Question Answering (VQA)**: Grounded visual answers with physical region citations.

---

## 2. SAR & Microwave Radar Intelligence
9. **Linear-to-dB Radiometric Calibration**: Conversion of raw backscatter intensity to calibrated decibel scale ($\sigma^0$).
10. **Lee Speckle Filtering**: Multi-look adaptive filtering reducing granular radar noise while preserving edges.
11. **Radar Texture Analysis**: Local variance and standard deviation mapping to distinguish water from rough surfaces.
12. **Specular Water Inundation Detection**: Threshold-based identification of specular reflection characteristic of still water bodies.
13. **Bi-Temporal SAR Flood Mapping**: Identification of newly inundated terrain during monsoons and extreme weather events.
14. **All-Weather Microwave Penetration**: Cross-sensor analysis penetrating dense cloud cover and darkness.

---

## 3. Autonomous Multi-Agent Architecture
15. **Autonomous Sensor Router**: Classifies incoming query intent and selects appropriate sensor modalities (Optical vs SAR vs Paired).
16. **ReAct Mission Planner**: Formulates dynamic multi-step execution plans with step-by-step reasoning.
17. **Scientific Judge Agent**: Multi-sensor arbitrator resolving discrepancies between optical and microwave evidence.
18. **Anti-Hallucination Guard**: Enforces minimum confidence thresholds and triggers honest `TARGET_NOT_FOUND` abstention when evidence is insufficient.
19. **Composite Explainable Confidence Engine**: Blends model logits, physics verification, spatial coherence, and bimodal separation scores.
20. **Deterministic Fallback Policy**: Badged offline mode ensuring zero hallucinated responses when external LLMs are unavailable.

---

## 4. Geospatial & Physics Verification
21. **Deterministic Physics Verifier**: Spectral index validation (NDVI, NDWI, NDBI) enforcing strict physical boundaries.
22. **Geodesic Area Computation**: High-precision ellipsoidal area calculations ($m^2$, ha, $km^2$, acres).
23. **RFC 7946 GeoJSON Compliance**: Standards-compliant vector generation in EPSG:4326 WGS84 coordinate space.
24. **Sub-Pixel Coordinate Inversion**: Accurate affine transformation between native raster pixel grids and global lat/lon.

---

## 5. Security & Cryptographic Integrity
25. **Path Traversal Protection**: Hardened directory traversal defenses against `../` escapes and null-byte injection.
26. **Binary Magic Bytes Validation**: Strict MIME inspection accepting only valid GeoTIFF, PNG, and JPEG files.
27. **Prompt Injection Mitigation**: Autonomous pattern scrubber neutralizing adversarial jailbreak sequences.
28. **Deterministic SHA-256 Run Hashes**: Cryptographic fingerprints binding input rasters, model versions, and outputs.
29. **HMAC Tamper-Proof Audit Seals**: Signed audit tokens preventing post-generation report alteration.

---

## 6. Visualization & Reporting
30. **Interactive Leaflet GIS Map**: Dark-themed geospatial map with zoom controls, tile layers, and GeoJSON vectors.
31. **Interactive Before/After Split Slider**: Synchronized dual-raster comparison with draggable divider.
32. **Three.js 3D Earth Globe**: WebGL digital twin Earth featuring orbital satellite tracks, satellite beacons, and ISRO ground stations.
33. **Multi-Format Report Generator**: Downloadable reports in PDF (ReportLab), RFC 7946 GeoJSON, Markdown, and JSON.
