"""
tests/test_multimodal_physics_judge.py
======================================
Unit tests for Phase 3:
- Physics Verification Engine (satquery.physics.verifier)
- Scientific Judge (satquery.agent.judge)
- Anti-Hallucination Guard (satquery.agent.anti_hallucination)
- Composite Confidence Engine (satquery.agent.confidence_engine)
"""

from __future__ import annotations

import pytest

from satquery.physics.verifier import PhysicsVerificationEngine
from satquery.agent.judge import ScientificJudge
from satquery.agent.anti_hallucination import AntiHallucinationGuard
from satquery.agent.confidence_engine import CompositeConfidenceEngine
from satquery.agent.schemas import SpecialistResult, MeasurementRecord


def test_physics_verification_engine_water_pass_and_fail():
    # 1. Valid water: NDWI > 0.15, SAR < -14 dB
    res_pass = PhysicsVerificationEngine.verify_claim(
        claim_type="water_expansion",
        spectral_data={"ndwi": 0.45, "area_m2": 5000.0},
        sar_data={"vv_db": -18.2},
        temporal_deltas={"delta_ndwi": 0.35, "delta_sar_db": -5.1}
    )
    assert res_pass.status == "passed"
    assert res_pass.physics_passed is True
    assert len(res_pass.contradictions) == 0

    # 2. Contradictory water: AI claims water, but NDWI is dry (-0.25) and SAR is rough ground (-8 dB)
    res_fail = PhysicsVerificationEngine.verify_claim(
        claim_type="water_expansion",
        spectral_data={"ndwi": -0.25, "area_m2": 5000.0},
        sar_data={"vv_db": -8.0},
        temporal_deltas={"delta_ndwi": -0.10, "delta_sar_db": +1.0}
    )
    assert res_fail.status == "rejected"
    assert res_fail.physics_passed is False
    assert len(res_fail.contradictions) >= 2


def test_physics_verification_vegetation_and_area():
    # Vegetation loss with wrong delta (+0.20 increase)
    res_veg = PhysicsVerificationEngine.verify_claim(
        claim_type="vegetation_loss",
        spectral_data={"ndvi": 0.70, "area_m2": 5000.0},
        temporal_deltas={"delta_ndvi": 0.20}
    )
    assert res_veg.status == "rejected"
    assert any("NDVI" in c for c in res_veg.contradictions)

    # Area too small (< 25 m2)
    res_area = PhysicsVerificationEngine.verify_claim(
        claim_type="building",
        spectral_data={"area_m2": 10.0}
    )
    assert any("noise threshold" in c for c in res_area.contradictions)


def test_scientific_judge_verdicts():
    # Helper to build mock specialist result
    def make_res(tool: str, obs: str, conf: float, measurements=None):
        return SpecialistResult(
            tool_id=tool,
            implementation_type="real_model",
            execution_status="healthy",
            duration_ms=25.0,
            observations=obs,
            measurements=measurements or [],
            confidence_score=conf
        )

    # 1. Multi-Sensor Confirmed Water
    opt_water = make_res("optical_agent", "Identified expanded open water in central basin", 0.92)
    sar_water = make_res(
        "sar_analyzer", "SAR specular water reflection confirmed", 0.90,
        measurements=[MeasurementRecord(
            metric_id="flood_inundation_ha", value=14.2, unit="ha",
            source_tool="sar_analyzer", source_run_id="run_1", raster_hash="h1"
        )]
    )
    v_conf = ScientificJudge.arbitrate("flood", optical_result=opt_water, sar_result=sar_water)
    assert v_conf.verdict == "confirmed"
    assert v_conf.confidence >= 0.88

    # 2. Cross-Modal Conflict -> Uncertain
    opt_dry = make_res("optical_agent", "Optical imagery shows dry cleared agricultural land", 0.85)
    v_conflict = ScientificJudge.arbitrate("flood", optical_result=opt_dry, sar_result=sar_water)
    assert v_conflict.verdict == "uncertain"
    assert v_conflict.confidence < 0.65

    # 3. No Evidence -> target_not_found
    v_not_found = ScientificJudge.arbitrate("bridge", optical_result=None, sar_result=None)
    assert v_not_found.verdict == "target_not_found"
    assert v_not_found.confidence <= 0.30


def test_anti_hallucination_guard():
    # Tier classification
    assert AntiHallucinationGuard.classify_confidence_tier(0.92) == "HIGH"
    assert AntiHallucinationGuard.classify_confidence_tier(0.72) == "MEDIUM"
    assert AntiHallucinationGuard.classify_confidence_tier(0.48) == "LOW"
    assert AntiHallucinationGuard.classify_confidence_tier(0.25) == "VERY_LOW"

    # TARGET_NOT_FOUND sanitization
    text, abstained = AntiHallucinationGuard.sanitize_claim(
        raw_text="I think there might be a bridge here",
        confidence_score=0.25,
        verdict="target_not_found",
        target_entity="suspension bridge"
    )
    assert abstained is True
    assert "TARGET_NOT_FOUND" in text
    assert "suspension bridge" in text

    # Strip exaggerated 100% assertions
    cleaned, _ = AntiHallucinationGuard.sanitize_claim(
        raw_text="The area is 100% accurate flooded",
        confidence_score=0.75,
        verdict="probable"
    )
    assert "100% accurate" not in cleaned


def test_composite_confidence_engine():
    conf = CompositeConfidenceEngine.calculate_confidence(
        model_score=0.90,
        physics_passed=True,
        spatial_consistency=0.92,
        temporal_consistency=0.88,
        sensor_agreement=0.94,
        bimodal_separation_score=0.91,
        pseudo_change_ratio=0.85
    )
    assert conf.label == "HIGH"
    assert conf.score >= 0.85
    assert conf.components["physics"] == 0.95
    assert "High confidence" in conf.explanation

    # Collapsed physics score when physics fails
    conf_fail = CompositeConfidenceEngine.calculate_confidence(
        model_score=0.90,
        physics_passed=False
    )
    assert conf_fail.score < 0.75
    assert conf_fail.components["physics"] == 0.25
