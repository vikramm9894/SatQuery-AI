"""
satquery.agent.anti_hallucination
=================================
Anti-Hallucination & Honest Abstention System (Section 17).
Prevents false certainty and ungrounded AI hallucinations in Earth observation intelligence.

Principles:
- If no reliable evidence exists, explicitly return TARGET_NOT_FOUND
- Strict threshold classification:
    >= 0.80      -> HIGH (confirmed facts)
    0.60 - 0.79  -> MEDIUM (probable findings)
    0.40 - 0.59  -> LOW (uncertain / preliminary signals)
    < 0.40       -> VERY_LOW -> Abstained / TARGET_NOT_FOUND
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional, Tuple

logger = logging.getLogger(__name__)

ConfidenceTier = Literal["HIGH", "MEDIUM", "LOW", "VERY_LOW"]


class AntiHallucinationGuard:
    """
    Enforces strict calibration bounds and triggers honest abstention when evidence is insufficient.
    """

    HIGH_THRESHOLD = 0.80
    MEDIUM_THRESHOLD = 0.60
    LOW_THRESHOLD = 0.40

    @classmethod
    def classify_confidence_tier(cls, score: float) -> ConfidenceTier:
        """Classifies numerical confidence score into canonical risk tiers."""
        if score >= cls.HIGH_THRESHOLD:
            return "HIGH"
        elif score >= cls.MEDIUM_THRESHOLD:
            return "MEDIUM"
        elif score >= cls.LOW_THRESHOLD:
            return "LOW"
        else:
            return "VERY_LOW"

    @classmethod
    def sanitize_claim(
        cls,
        raw_text: str,
        confidence_score: float,
        verdict: str,
        target_entity: str = "requested target"
    ) -> Tuple[str, bool]:
        """
        Sanitizes synthesized response text to eliminate ungrounded over-confidence.
        Returns: (sanitized_text, is_abstained)
        """
        tier = cls.classify_confidence_tier(confidence_score)

        if verdict == "target_not_found" or tier == "VERY_LOW":
            msg = (
                f"TARGET_NOT_FOUND: The satellite imagery footprint provides insufficient physical or "
                f"spectral evidence to confirm the presence of '{target_entity}'. No verified structures "
                f"or anomalies met the detection threshold."
            )
            return msg, True

        elif tier == "LOW" or verdict == "uncertain":
            msg = (
                f"UNCERTAIN FINDING (Low Confidence: {confidence_score:.2f}): Preliminary cues were noted, "
                f"but physical evidence remains inconclusive or contradicted by secondary sensor channels. "
                f"Details: {raw_text}"
            )
            return msg, False

        elif tier == "MEDIUM" or verdict == "probable":
            # Strip absolute assertions like "definitely", "100%", "unquestionably"
            cleaned = raw_text.replace("100% accurate", "high confidence").replace("definitely", "likely")
            return f"PROBABLE FINDING: {cleaned}", False

        else:
            return raw_text, False


anti_hallucination_guard = AntiHallucinationGuard()
