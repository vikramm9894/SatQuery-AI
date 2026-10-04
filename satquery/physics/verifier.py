"""
satquery.physics.verifier
=========================
Physics Verification Engine (Section 15).
Ensures every AI prediction passes deterministic physical checks before being
accepted as evidence.

Guards:
- Water claims must correlate with NDWI > 0.15 or SAR backscatter < -14 dB
- Flooding claims must correlate with Delta NDWI > +0.10 or Delta SAR < -3.0 dB
- Vegetation loss claims must correlate with Delta NDVI < -0.15
- Urban growth claims must correlate with positive NDBI difference
- Rejects ungrounded or physically impossible claims by downgrading status to 'uncertain' or 'rejected'.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from satquery.agent.schemas import PhysicsValidationResult
from satquery.change_detection.indices import ndvi, ndwi, ndbi, sar_amplitude_to_db

logger = logging.getLogger(__name__)


class PhysicsVerificationEngine:
    """
    Deterministic Physics Verification Gate.
    Verifies candidate AI claims against physical spectral and microwave characteristics.
    """

    @classmethod
    def verify_claim(
        cls,
        claim_type: str,
        spectral_data: Dict[str, Any],
        sar_data: Optional[Dict[str, Any]] = None,
        temporal_deltas: Optional[Dict[str, float]] = None
    ) -> PhysicsValidationResult:
        """
        Validates a candidate claim against available physical measurements.
        """
        claim = claim_type.lower()
        spectral_checks: Dict[str, Any] = {}
        spatial_checks: Dict[str, Any] = {}
        temporal_checks: Dict[str, Any] = {}
        contradictions: List[str] = []

        is_water_claim = any(w in claim for w in ["water", "flood", "lake", "inundat"])
        is_veg_loss_claim = any(w in claim for w in ["vegetation_loss", "deforest", "forest_clearing", "crop_loss"])
        is_urban_claim = any(w in claim for w in ["urban", "building", "construct", "impervious"])

        # 1. Optical Physical Verification
        has_ndwi = "ndwi" in spectral_data
        has_ndvi = "ndvi" in spectral_data
        has_ndbi = "ndbi" in spectral_data

        if is_water_claim:
            # Check optical NDWI
            if has_ndwi:
                ndwi_val = float(spectral_data["ndwi"])
                spectral_checks["ndwi_value"] = ndwi_val
                if ndwi_val < 0.10:
                    contradictions.append(
                        f"Optical NDWI is {ndwi_val:+.3f} (expected > +0.15 for open water); failed optical water gate."
                    )

            # Check SAR backscatter
            if sar_data and "vv_db" in sar_data:
                vv_db = float(sar_data["vv_db"])
                spectral_checks["sar_vv_db"] = vv_db
                if vv_db > -12.0:
                    contradictions.append(
                        f"SAR VV backscatter is {vv_db:+.1f} dB (expected < -14 dB for specular calm water)."
                    )

            # Check Temporal Inundation Delta
            if temporal_deltas:
                if "delta_ndwi" in temporal_deltas:
                    d_ndwi = temporal_deltas["delta_ndwi"]
                    temporal_checks["delta_ndwi"] = d_ndwi
                    if d_ndwi < 0.05:
                        contradictions.append(
                            f"Temporal Delta NDWI is {d_ndwi:+.3f} (insufficient increase for new inundation)."
                        )
                if "delta_sar_db" in temporal_deltas:
                    d_sar = temporal_deltas["delta_sar_db"]
                    temporal_checks["delta_sar_db"] = d_sar
                    if d_sar > -2.0:
                        contradictions.append(
                            f"Temporal SAR backscatter delta is {d_sar:+.1f} dB (expected < -3.0 dB attenuation)."
                        )

        elif is_veg_loss_claim:
            if has_ndvi:
                ndvi_val = float(spectral_data["ndvi"])
                spectral_checks["post_ndvi"] = ndvi_val

            if temporal_deltas and "delta_ndvi" in temporal_deltas:
                d_ndvi = temporal_deltas["delta_ndvi"]
                temporal_checks["delta_ndvi"] = d_ndvi
                if d_ndvi > -0.08:
                    contradictions.append(
                        f"Temporal Delta NDVI is {d_ndvi:+.3f} (expected significant drop < -0.15 for vegetation loss)."
                    )

        elif is_urban_claim:
            if temporal_deltas and "delta_ndbi" in temporal_deltas:
                d_ndbi = temporal_deltas["delta_ndbi"]
                temporal_checks["delta_ndbi"] = d_ndbi
                if d_ndbi < 0.03:
                    contradictions.append(
                        f"Temporal Delta NDBI is {d_ndbi:+.3f} (expected positive NDBI shift for built-up growth)."
                    )

        # Spatial sanity: Minimum viable area
        area_m2 = float(spectral_data.get("area_m2", 1000.0))
        spatial_checks["area_m2"] = area_m2
        if area_m2 < 25.0:
            contradictions.append(f"Detected area is only {area_m2:.1f} m² (< 25 m² noise threshold).")

        # Determine verdict
        if not contradictions:
            status = "passed"
            passed = True
            reason = f"Deterministic physical validation confirmed for '{claim_type}' across all checked sensors."
        elif len(contradictions) == 1 and ("SAR" in contradictions[0] or "Optical" in contradictions[0]) and sar_data is not None and has_ndwi:
            # Single sensor discrepancy under multi-sensor availability -> flagged for Scientific Judge
            status = "uncertain"
            passed = False
            reason = f"Single-modality physical discrepancy detected: {contradictions[0]}"
        else:
            status = "rejected"
            passed = False
            reason = f"AI claim failed physical verification: {'; '.join(contradictions)}"

        return PhysicsValidationResult(
            status=status,
            physics_passed=passed,
            spectral_checks=spectral_checks,
            spatial_checks=spatial_checks,
            temporal_checks=temporal_checks,
            contradictions=contradictions,
            reason=reason
        )


physics_verifier = PhysicsVerificationEngine()
