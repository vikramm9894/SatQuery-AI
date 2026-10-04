"""
tests/test_ai_core_specialists.py
=================================
Unit and integration tests for AI Core Specialists (Phase 2):
- Sensor Router (Agent 3)
- Dedicated SAR Analysis Specialist
- VQA Specialist
- Scene Captioning Specialist
- Grounding Specialist
- 12 Change Detection Classes
- Cryptographic Evidence Engine
"""

from __future__ import annotations

import numpy as np
import pytest
from affine import Affine
from rasterio.crs import CRS

from satquery.agent.sensor_router import SensorRouter, SensorProfile
from satquery.agent.specialists.sar import (
    linear_to_db,
    lee_speckle_filter,
    compute_radar_texture,
    detect_sar_water,
    SARAnalysisSpecialist
)
from satquery.agent.specialists.vqa import VQASpecialist
from satquery.agent.specialists.captioning import SceneCaptioningSpecialist
from satquery.agent.specialists.grounding import GroundingSpecialist
from satquery.agent.evidence import EvidenceEngine
from satquery.agent.schemas import SpecialistRequest
from satquery.change_detection.metrics import (
    classify_change_direction,
    build_text_summary,
    _DIRECTION_DESCRIPTIONS
)
from satquery.core.raster_io import RasterData


@pytest.fixture
def synthetic_sar_raster(tmp_path):
    """Creates a temporary 2-band (VV, VH) SAR GeoTIFF for testing."""
    import rasterio
    p = tmp_path / "s1_sar.tif"
    h, w = 64, 64
    # VV: amplitude ~ 0.2 (water) in top-left, 0.8 elsewhere
    vv = np.full((h, w), 0.8, dtype=np.float32)
    vv[:20, :20] = 0.02  # water reflection
    # VH: amplitude ~ 0.1
    vh = vv * 0.3

    tf = Affine(10.0, 0.0, 500000.0, 0.0, -10.0, 3000000.0)
    with rasterio.open(
        p, "w", driver="GTiff", height=h, width=w, count=2,
        dtype="float32", crs="EPSG:32643", transform=tf
    ) as dst:
        dst.write(vv, 1)
        dst.write(vh, 2)
        dst.update_tags(descriptions=["VV", "VH"])
    return str(p)


@pytest.fixture
def synthetic_optical_raster(tmp_path):
    """Creates a temporary 4-band (B, G, R, NIR) optical GeoTIFF for testing."""
    import rasterio
    p = tmp_path / "cartosat_optical.tif"
    h, w = 64, 64
    # 4 bands: B, G, R, NIR
    arr = np.full((4, h, w), 0.3, dtype=np.float32)
    # Vegetation in center: high NIR (0.8), low Red (0.1)
    arr[3, 20:45, 20:45] = 0.8  # NIR
    arr[2, 20:45, 20:45] = 0.1  # Red

    tf = Affine(0.65, 0.0, 500000.0, 0.0, -0.65, 3000000.0)
    with rasterio.open(
        p, "w", driver="GTiff", height=h, width=w, count=4,
        dtype="float32", crs="EPSG:32643", transform=tf
    ) as dst:
        for b in range(4):
            dst.write(arr[b], b + 1)
    return str(p)


def test_sensor_router_profiling_and_decisions():
    # 1. Profile SAR
    sar_meta = {"filename": "sentinel1_vv_vh.tif", "bands": 2, "descriptions": ["VV", "VH"]}
    sar_prof = SensorRouter.profile_asset("sar_1", sar_meta)
    assert sar_prof.sensor_category == "sar"
    assert sar_prof.has_polarization is True

    # 2. Profile Optical Multispectral
    opt_meta = {"filename": "cartosat2s_ms.tif", "bands": 4, "resolution_m": 0.65}
    opt_prof = SensorRouter.profile_asset("opt_1", opt_meta)
    assert opt_prof.sensor_category == "multispectral"
    assert opt_prof.has_nir is True

    # 3. Route Flood Query on SAR
    route_sar = SensorRouter.route_query("Map flood extent through monsoon clouds", [sar_prof])
    assert route_sar.primary_sensor_category == "sar"
    assert route_sar.use_sar_penetration is True
    assert "sar_specialist" in route_sar.recommended_specialists

    # 4. Route Multimodal Optical + SAR
    route_multi = SensorRouter.route_query("Assess cyclone flooding and damaged buildings", [opt_prof, sar_prof])
    assert route_multi.primary_sensor_category == "optical_sar"
    assert route_multi.use_cross_modal_fusion is True
    assert "multimodal_fusion" in route_multi.recommended_specialists


def test_sar_math_and_filters():
    lin = np.array([0.01, 0.1, 1.0, 10.0], dtype=np.float32)
    db = linear_to_db(lin)
    assert pytest.approx(db[0], abs=0.1) == -20.0
    assert pytest.approx(db[1], abs=0.1) == -10.0
    assert pytest.approx(db[2], abs=0.1) == 0.0
    assert pytest.approx(db[3], abs=0.1) == 10.0

    # Lee speckle filter reduces variance on uniform noisy patch
    np.random.seed(42)
    noisy = np.random.normal(10.0, 2.0, (32, 32)).astype(np.float32)
    filt = lee_speckle_filter(noisy, size=5)
    assert np.var(filt) < np.var(noisy)

    # Radar texture computation
    texture = compute_radar_texture(noisy)
    assert texture.shape == (32, 32)
    assert np.mean(texture) > 0.0

    # Water detection threshold
    water = detect_sar_water(np.array([-18.0, -10.0]))
    assert bool(water[0]) is True
    assert bool(water[1]) is False


import asyncio


def test_sar_specialist_execution(synthetic_sar_raster):
    specialist = SARAnalysisSpecialist()
    req = SpecialistRequest(
        run_id="run_test_sar",
        task_type="sar_analysis",
        query_text="Identify water bodies and radar surface roughness",
        asset_paths={"primary": synthetic_sar_raster}
    )
    res = asyncio.run(specialist.execute(req))
    assert res.execution_status == "healthy"
    assert res.confidence_score > 0.80
    assert any(m.metric_id == "surface_water_ha" for m in res.measurements)


def test_vqa_and_captioning_specialists(synthetic_optical_raster):
    # 1. VQA
    vqa = VQASpecialist()
    req_vqa = SpecialistRequest(
        run_id="run_test_vqa",
        task_type="vqa",
        query_text="Is there any building cluster in this image?",
        asset_paths={"primary": synthetic_optical_raster}
    )
    res_vqa = asyncio.run(vqa.execute(req_vqa))
    assert res_vqa.execution_status == "healthy"
    assert len(res_vqa.bounding_boxes) > 0
    assert res_vqa.confidence_score >= 0.80

    # 2. Captioning
    captioner = SceneCaptioningSpecialist()
    req_cap = SpecialistRequest(
        run_id="run_test_cap",
        task_type="scene_description",
        query_text="Describe the land cover in this scene",
        asset_paths={"primary": synthetic_optical_raster}
    )
    res_cap = asyncio.run(captioner.execute(req_cap))
    assert res_cap.execution_status == "healthy"
    assert "Land Cover:" in res_cap.observations
    assert "Sensor Footprint:" in res_cap.observations


def test_grounding_specialist(synthetic_optical_raster):
    grounder = GroundingSpecialist()
    req = SpecialistRequest(
        run_id="run_test_ground",
        task_type="grounding",
        query_text="Find all buildings and structures",
        asset_paths={"primary": synthetic_optical_raster}
    )
    res = asyncio.run(grounder.execute(req))
    assert res.execution_status == "healthy"
    assert res.geojson_geometry is not None
    assert res.geojson_geometry["type"] == "FeatureCollection"
    assert len(res.bounding_boxes) > 0


def test_12_change_classes_and_descriptions():
    # Verify all 12 target classes have registered descriptions
    expected_classes = [
        "vegetation_loss", "vegetation_gain", "water_expansion",
        "water_reduction", "urban_growth", "urban_loss",
        "bare_land_change", "construction", "deforestation",
        "flooding", "possible_damage", "unknown_change"
    ]
    for c in expected_classes:
        assert c in _DIRECTION_DESCRIPTIONS, f"Missing description for {c}"

    # Verify summary text generation for all classes
    dummy_area = {"area_m2": 50000.0, "area_ha": 5.0, "pct_changed": 10.0}
    for c in expected_classes:
        summary = build_text_summary(dummy_area, c, "ndvi", 2)
        assert "ha" in summary
        assert len(summary) > 30


def test_evidence_engine():
    rec = EvidenceEngine.build_evidence_record(
        finding_id="find_test_1",
        source_asset_path="dummy_path.tif",
        workflow="optical_sar_fusion",
        agent_name="SAR Specialist",
        model_name="SAR-v1.0",
        confidence=0.93,
        physics_checks={"delta_db": -4.2}
    )
    assert rec.evidence_id.startswith("ev_")
    assert rec.finding_id == "find_test_1"
    assert EvidenceEngine.verify_evidence_integrity(rec) is True
