"""
tests/test_geospatial_foundation.py
===================================
Unit tests for the centralized geospatial engine (satquery.core.geospatial)
and canonical data contracts (satquery.agent.schemas).
"""

from __future__ import annotations

import pytest
from affine import Affine
from rasterio.crs import CRS
from shapely.geometry import box as shapely_box, mapping

from satquery.core.geospatial import (
    pixel_to_native_coords,
    native_to_pixel_coords,
    bbox_pixel_to_geometry,
    compute_geodesic_area_m2,
    calculate_area_metrics,
    build_rfc7946_feature,
    build_rfc7946_feature_collection,
)
from satquery.agent.schemas import (
    EvidenceRecord,
    FindingRecord,
    PhysicsValidationResult,
    ScientificVerdict,
    ExplainableConfidence,
)


def test_pixel_and_native_coords_roundtrip():
    # Affine: pixel size 10m x 10m, origin at (500000, 3000000)
    tf = Affine(10.0, 0.0, 500000.0, 0.0, -10.0, 3000000.0)
    
    col, row = 15.5, 42.0
    x_native, y_native = pixel_to_native_coords(col, row, tf)
    
    # Back to pixel
    col_rt, row_rt = native_to_pixel_coords(x_native, y_native, tf)
    assert pytest.approx(col, abs=1e-5) == col_rt
    assert pytest.approx(row, abs=1e-5) == row_rt


def test_bbox_pixel_to_geometry():
    # Projected CRS UTM Zone 43N
    tf = Affine(10.0, 0.0, 500000.0, 0.0, -10.0, 3000000.0)
    crs = CRS.from_epsg(32643)

    bbox_pixel = [10.0, 20.0, 50.0, 60.0]  # ymin, xmin, ymax, xmax
    res = bbox_pixel_to_geometry(bbox_pixel, tf, native_crs=crs)

    assert "native_geometry" in res
    assert "wgs84_geometry" in res
    assert len(res["bounds_wgs84"]) == 4

    min_lon, min_lat, max_lon, max_lat = res["bounds_wgs84"]
    assert min_lon < max_lon
    assert min_lat < max_lat
    # Verify longitude and latitude are in valid geographic range
    assert -180.0 <= min_lon <= 180.0
    assert -90.0 <= min_lat <= 90.0


def test_geodesic_area_calculation():
    # Create a small WGS84 polygon (0.01 deg x 0.01 deg near equator)
    # 0.01 deg is approximately 1.11 km x 1.11 km ≈ 1.23 km² ≈ 123 ha
    poly = shapely_box(77.0, 12.0, 77.01, 12.01)
    geom_wgs84 = mapping(poly)

    area_m2 = compute_geodesic_area_m2(geom_wgs84)
    assert area_m2 > 1_000_000.0  # > 1 km²
    assert area_m2 < 1_500_000.0  # < 1.5 km²

    metrics = calculate_area_metrics(geom_wgs84, scene_total_area_m2=5_000_000.0)
    assert metrics["area_m2"] == pytest.approx(area_m2, rel=1e-2)
    assert metrics["area_ha"] > 100.0
    assert metrics["area_km2"] > 1.0
    assert metrics["area_acres"] > 250.0
    assert 0.0 < metrics["pct_scene"] <= 100.0


def test_rfc7946_feature_generation():
    geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    props = {"label": "water", "confidence": 0.95, "area_ha": 12.5}
    feat = build_rfc7946_feature(geom, props, feature_id="f_001")

    assert feat["type"] == "Feature"
    assert feat["id"] == "f_001"
    assert feat["geometry"] == geom
    assert feat["properties"]["label"] == "water"

    fc = build_rfc7946_feature_collection([feat], metadata={"sensor": "Sentinel-2"})
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert fc["properties"]["sensor"] == "Sentinel-2"


def test_canonical_schemas_validation():
    # 1. PhysicsValidationResult
    p_val = PhysicsValidationResult(
        status="passed",
        physics_passed=True,
        spectral_checks={"ndwi": 0.45, "water_threshold": 0.15},
        reason="NDWI confirms open surface water presence"
    )
    assert p_val.status == "passed"
    assert p_val.physics_passed is True

    # 2. ExplainableConfidence
    conf = ExplainableConfidence(
        score=0.92,
        label="HIGH",
        components={
            "model": 0.90,
            "physics": 0.95,
            "spatial": 0.92,
            "temporal": 0.89,
            "sensor_agreement": 0.94
        },
        explanation="High optical and SAR concordance confirmed by physical water index"
    )
    assert conf.label == "HIGH"
    assert conf.components["physics"] == 0.95

    # 3. ScientificVerdict
    verdict = ScientificVerdict(
        verdict="confirmed",
        confidence=0.92,
        supporting_evidence=["NDWI > 0.3", "SAR backscatter drop > 3dB"],
        reason="Multi-sensor evidence confirms flood extent"
    )
    assert verdict.verdict == "confirmed"

    # 4. EvidenceRecord
    ev = EvidenceRecord(
        evidence_id="ev_001",
        finding_id="find_001",
        source_asset_id="asset_t2",
        workflow="optical_sar_flood",
        agent="SAR Specialist",
        model="SAR-Backscatter-v1.0",
        confidence=0.91,
        geometry={"type": "Polygon", "coordinates": []},
        physics_checks={"delta_db": -4.2},
        timestamp=1700000000.0
    )
    assert ev.evidence_id == "ev_001"

    # 5. FindingRecord
    finding = FindingRecord(
        finding_id="find_001",
        label="water_expansion",
        verdict="confirmed",
        confidence=conf,
        area_m2=125000.0,
        area_ha=12.5,
        area_km2=0.125,
        area_acres=30.88,
        pct_scene=14.2,
        evidence_records=[ev],
        explanation="Cyclone flood inundation confirmed",
        source_assets=["t1_opt.tif", "t2_sar.tif"],
        timestamp=1700000000.0
    )
    assert finding.area_ha == 12.5
    assert len(finding.evidence_records) == 1
