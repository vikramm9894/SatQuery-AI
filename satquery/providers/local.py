"""
satquery.providers.local
========================
Local dataset provider and mock cloud catalog adapters.
Allows offline operation using pre-packaged or locally supplied GeoTIFFs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from satquery.providers.base import BaseSatelliteProvider, SatelliteProduct


class LocalDatasetProvider(BaseSatelliteProvider):
    """
    Offline-first provider indexing locally stored GeoTIFF datasets.
    """

    def __init__(self, data_root: Path | str):
        self.data_root = Path(data_root).resolve()

    def search_products(
        self,
        bbox_wgs84: List[float],
        start_date: str,
        end_date: str,
        max_cloud_cover_pct: float = 20.0
    ) -> List[SatelliteProduct]:
        products: List[SatelliteProduct] = []
        if not self.data_root.exists():
            return products

        for tif_file in self.data_root.glob("**/*.tif"):
            fn = tif_file.stem
            products.append(SatelliteProduct(
                product_id=fn,
                sensor_name="Local GeoTIFF",
                acquisition_timestamp=start_date,
                bounding_box_wgs84=bbox_wgs84,
                cloud_cover_pct=0.0,
                download_url_or_path=str(tif_file),
                band_names=["band1"]
            ))
        return products

    def fetch_product(self, product_id: str, target_dir: str) -> str:
        for tif_file in self.data_root.glob(f"**/{product_id}.tif"):
            return str(tif_file)
        raise FileNotFoundError(f"Local satellite product not found: {product_id}")


class SentinelProvider(BaseSatelliteProvider):
    """Placeholder adapter for ESA Copernicus Sentinel API."""
    def search_products(self, bbox_wgs84: List[float], start_date: str, end_date: str, max_cloud_cover_pct: float = 20.0) -> List[SatelliteProduct]:
        return []
    def fetch_product(self, product_id: str, target_dir: str) -> str:
        raise NotImplementedError("Live Copernicus API requires COPERNICUS_API_KEY environment credentials.")


class ISROProvider(BaseSatelliteProvider):
    """Placeholder adapter for ISRO Bhoovan / MOSDAC API."""
    def search_products(self, bbox_wgs84: List[float], start_date: str, end_date: str, max_cloud_cover_pct: float = 20.0) -> List[SatelliteProduct]:
        return []
    def fetch_product(self, product_id: str, target_dir: str) -> str:
        raise NotImplementedError("Live ISRO Bhoovan API requires ISRO_BHOOVAN_KEY credentials.")
