"""
satquery.agent.confidence_engine
================================
Explainable Composite Confidence Engine (Section 18 & 19).
Calculates mathematically grounded, explainable confidence scores for Earth observation
findings by combining model score, physical validation, spatial consistency, temporal
consistency, sensor concordance, and Vikram's bimodal histogram separation metric.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from satquery.agent.schemas import ExplainableConfidence
from satquery.change_detection.confidence import compute_confidence, confidence_label

logger = logging.getLogger(__name__)


class CompositeConfidenceEngine:
    """
    Computes explainable, multi-factor confidence scores.
    """

    @classmethod
    def calculate_confidence(
        cls,
        model_score: float = 0.85,
        physics_passed: bool = True,
        spatial_consistency: float = 0.90,
        temporal_consistency: float = 0.90,
        sensor_agreement: float = 0.92,
        bimodal_separation_score: Optional[float] = None,
        pseudo_change_ratio: Optional[float] = None
    ) -> ExplainableConfidence:
        """
        Combines 5 core components with weightings:
        - Model Confidence: 0.20
        - Physics Agreement: 0.25
        - Spatial Consistency: 0.15
        - Temporal Consistency: 0.15
        - Sensor Agreement & Bimodal Histogram: 0.25
        """
        # Physical gate penalty: if physics failed, physical component collapses
        phys_score = 0.95 if physics_passed else 0.25

        # Incorporate bimodal separation score if available from Change Detection
        if bimodal_separation_score is not None:
            effective_sensor_agree = (sensor_agreement * 0.5) + (bimodal_separation_score * 0.5)
        else:
            effective_sensor_agree = sensor_agreement

        # STSF pseudo-change suppression factor
        if pseudo_change_ratio is not None:
            # If excessive pseudo-change was removed (> 60%), slight uncertainty penalty
            if pseudo_change_ratio < 0.40:
                spatial_consistency = max(0.50, spatial_consistency * 0.85)

        w_model = 0.20
        w_phys = 0.25
        w_spatial = 0.15
        w_temp = 0.15
        w_sensor = 0.25

        composite_score = (
            w_model * model_score +
            w_phys * phys_score +
            w_spatial * spatial_consistency +
            w_temp * temporal_consistency +
            w_sensor * effective_sensor_agree
        )

        composite_score = round(max(0.05, min(0.98, composite_score)), 3)

        if composite_score >= 0.80:
            label = "HIGH"
            explanation = (
                f"High confidence ({composite_score*100:.1f}%): Finding is substantiated by strong physical agreement "
                f"({phys_score*100:.0f}%), consistent spatial clustering, and concordant sensor evidence."
            )
        elif composite_score >= 0.60:
            label = "MEDIUM"
            explanation = (
                f"Medium confidence ({composite_score*100:.1f}%): Finding is supported by primary observations "
                f"with minor sensor or discretization noise."
            )
        elif composite_score >= 0.40:
            label = "LOW"
            explanation = (
                f"Low confidence ({composite_score*100:.1f}%): Finding exhibits weak spectral or physical support "
                f"and should be treated as preliminary."
            )
        else:
            label = "VERY_LOW"
            explanation = (
                f"Very low confidence ({composite_score*100:.1f}%): Insufficient evidence to substantiate the claim."
            )

        components = {
            "model": round(model_score, 3),
            "physics": round(phys_score, 3),
            "spatial": round(spatial_consistency, 3),
            "temporal": round(temporal_consistency, 3),
            "sensor_agreement": round(effective_sensor_agree, 3)
        }

        return ExplainableConfidence(
            score=composite_score,
            label=label,
            components=components,
            explanation=explanation
        )


confidence_engine = CompositeConfidenceEngine()
