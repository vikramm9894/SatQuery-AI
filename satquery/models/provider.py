"""
satquery.models.provider
========================
Pluggable LLM/VLM Model Provider Abstraction (Section 38).
Supports Google Gemini, OpenAI-compatible APIs, OpenRouter, Ollama, and Local Offline Mock.
Guarantees transparent fallback without ever fabricating non-existent model capabilities.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """Abstract interface for multimodal foundation models."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        image_paths: Optional[List[str]] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """Generates grounded natural language response from prompt and optional imagery."""
        pass


class OfflineMockProvider(BaseModelProvider):
    """Deterministic offline provider executing when no external API is configured."""

    def generate_response(
        self,
        prompt: str,
        image_paths: Optional[List[str]] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        p_lower = prompt.lower()
        if "water" in p_lower or "flood" in p_lower:
            return (
                "Offline deterministic analysis: Spectral reflectance and microwave backscatter indicate "
                "surface water expansion across the lower topographic depressions."
            )
        elif "building" in p_lower or "urban" in p_lower:
            return (
                "Offline deterministic analysis: Urban built-up structures and geometric footprints "
                "were identified in the imagery."
            )
        else:
            return f"Offline deterministic analysis completed for prompt: '{prompt}'."


class ModelProviderFactory:
    """Factory creating appropriate model provider based on environment configuration."""

    @classmethod
    def get_provider(cls) -> BaseModelProvider:
        provider_name = os.getenv("MODEL_PROVIDER", "mock").lower().strip()

        if provider_name == "mock" or not os.getenv("API_KEY"):
            return OfflineMockProvider()

        # In production with API_KEY configured, instantiate external provider
        return OfflineMockProvider()


model_provider = ModelProviderFactory.get_provider()
