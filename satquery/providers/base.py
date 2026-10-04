"""
satquery.providers.base
=======================
Satellite data provider abstraction interface (Section 36).
Decouples image acquisition from core analysis pipelines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SatelliteProduct(BaseModel):
    product_id: str
    sensor_name: str
    acquisition_timestamp: str
    bounding_box_wgs84: List[float]  # [minx, miny, maxx, maxy]
    cloud_cover_pct: float = 0.0
    download_url_or_path: str
    band_names: List[str]


class BaseSatelliteProvider(ABC):
    """Abstract satellite data provider interface."""

    @abstractmethod
    def search_products(
        self,
        bbox_wgs84: List[float],
        start_date: str,
        end_date: str,
        max_cloud_cover_pct: float = 20.0
    ) -> List[SatelliteProduct]:
        """Searches available satellite products meeting spatial-temporal criteria."""
        pass

    @abstractmethod
    def fetch_product(self, product_id: str, target_dir: str) -> str:
        """Fetches product to local disk and returns local path."""
        pass
