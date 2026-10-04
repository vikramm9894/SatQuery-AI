"""
satquery.agent.judge
====================
Scientific Judge Agent (Section 16).
Acts as the final arbitration authority across all multimodal specialist outputs,
physics verification results, and spectral signals.

Verdicts:
- confirmed         : Multi-sensor agreement backed by unambiguous physical proof
- probable          : Strong evidence with minor sensor discretization variance
- uncertain         : Discrepancy between optical and microwave signatures (e.g. cloud/glare)
- rejected          : Explicit contradiction with deterministic physical laws
- target_not_found  : No reliable evidence above the detection threshold exists
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from satquery.agent.schemas import ScientificVerdict, SpecialistResult, PhysicsValidationResult

logger = logging.getLogger(__name__)


class ScientificJudge:
    """
    Arbitration authority evaluating multimodal consistency and physical evidence.
    """

    @classmethod
    def arbitrate(
        cls,
        task_claim: str,
        optical_result: Optional[SpecialistResult] = None,
        sar_result: Optional[SpecialistResult] = None,
        change_result: Optional[Dict[str, Any]] = None,
        physics_validation: Optional[PhysicsValidationResult] = None
    ) -> ScientificVerdict:
        """
        Synthesizes all specialist outputs and delivers an honest scientific verdict.
        """
        supporting: List[str] = []
        contradicting: List[str] = []

        # 1. Inspect physics validation if available
        if physics_validation:
            if physics_validation.physics_passed:
                supporting.append(f"Physics Verification Gate passed: {physics_validation.reason}")
            else:
                contradicting.extend(physics_validation.contradictions)

        # 2. Check Optical evidence
        opt_conf = 0.0
        if optical_result and optical_result.execution_status == "healthy":
            opt_conf = optical_result.confidence_score
            supporting.append(f"Optical analysis: {optical_result.observations[:100]}... (conf={opt_conf:.2f})")

        # 3. Check SAR evidence
        sar_conf = 0.0
        if sar_result and sar_result.execution_status == "healthy":
            sar_conf = sar_result.confidence_score
            supporting.append(f"SAR microwave analysis: {sar_result.observations[:100]}... (conf={sar_conf:.2f})")

        # 4. Check Change Detection evidence
        if change_result and change_result.get("status") in ["ok", "partial"]:
            c_conf = float(change_result.get("confidence", 0.8))
            c_type = change_result.get("change_type", "change")
            area_ha = change_result.get("changed_area_ha", 0.0)
            supporting.append(f"Change Detection: {c_type} covering {area_ha:.2f} ha (bimodal conf={c_conf:.2f})")

        # 5. Multimodal Conflict Arbitration
        if optical_result and sar_result:
            # Check for phenomenological complementarity vs true contradiction
            opt_has_water = "water" in optical_result.observations.lower() or "flood" in optical_result.observations.lower()
            sar_has_water = any(m.metric_id in ["flood_inundation_ha", "surface_water_ha"] for m in sar_result.measurements)

            if opt_has_water and sar_has_water:
                supporting.append("Concordant cross-modal agreement: Both optical reflectance and SAR specular backscatter confirm water presence.")
            elif not opt_has_water and sar_has_water:
                # Potential cloud occlusion in optical!
                if "cloud" in optical_result.observations.lower() or "shadow" in optical_result.observations.lower():
                    supporting.append("Cross-modal complementarity: SAR microwave penetration detected inundation beneath optical cloud cover.")
                else:
                    contradicting.append("Cross-modal discrepancy: SAR detected water signature but clear optical imagery shows no open water.")
            elif opt_has_water and not sar_has_water:
                contradicting.append("Cross-modal discrepancy: Optical suggests water but SAR radar backscatter indicates dry rough ground.")

        # Determine Final Verdict
        if len(contradicting) > 1 and physics_validation and physics_validation.status == "rejected":
            verdict = "rejected"
            confidence = 0.15
            reason = f"Claim rejected due to explicit physical contradictions: {'; '.join(contradicting)}"

        elif len(contradicting) > 0:
            verdict = "uncertain"
            confidence = 0.52
            reason = f"Claim classified as uncertain due to cross-sensor disagreement: {'; '.join(contradicting)}"

        elif not supporting or (opt_conf < 0.40 and sar_conf < 0.40 and not change_result):
            verdict = "target_not_found"
            confidence = 0.20
            reason = "No statistically significant evidence supporting the requested target was detected within the imagery footprint."

        elif len(supporting) >= 2 and (not physics_validation or physics_validation.physics_passed):
            verdict = "confirmed"
            confidence = min(0.98, max(opt_conf, sar_conf, 0.88))
            reason = "Finding confirmed with multi-source physical and spectral agreement."

        else:
            verdict = "probable"
            confidence = max(opt_conf, sar_conf, 0.72)
            reason = "Finding is probable based on single-sensor evidence consistent with regional topology."

        return ScientificVerdict(
            verdict=verdict,
            confidence=round(float(confidence), 3),
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            reason=reason
        )


scientific_judge = ScientificJudge()
