"""
satquery.storage.local
======================
Local filesystem storage implementation with structured asset categorization.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from satquery.storage.base import BaseStorage

logger = logging.getLogger(__name__)

STANDARD_CATEGORIES = [
    "originals",
    "previews",
    "masks",
    "heatmaps",
    "overlays",
    "geojson",
    "reports"
]


class LocalStorage(BaseStorage):
    """
    Local filesystem storage backend.
    """

    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir).resolve()
        self._init_dirs()

    def _init_dirs(self) -> None:
        for cat in STANDARD_CATEGORIES:
            (self.root_dir / cat).mkdir(parents=True, exist_ok=True)

    def _get_category_dir(self, category: str) -> Path:
        cat_dir = self.root_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        return cat_dir

    def save_bytes(self, category: str, filename: str, data: bytes) -> str:
        cat_dir = self._get_category_dir(category)
        safe_fn = os.path.basename(filename)
        dest = cat_dir / safe_fn
        dest.write_bytes(data)
        return str(dest)

    def read_bytes(self, category: str, filename: str) -> bytes:
        target = self.get_path(category, filename)
        if not target.exists():
            raise FileNotFoundError(f"Storage file not found: {category}/{filename}")
        return target.read_bytes()

    def get_path(self, category: str, filename: str) -> Path:
        safe_fn = os.path.basename(filename)
        return self._get_category_dir(category) / safe_fn

    def exists(self, category: str, filename: str) -> bool:
        return self.get_path(category, filename).exists()

    def list_files(self, category: str) -> List[str]:
        cat_dir = self._get_category_dir(category)
        return [f.name for f in cat_dir.iterdir() if f.is_file()]

    def delete(self, category: str, filename: str) -> bool:
        target = self.get_path(category, filename)
        if target.exists():
            try:
                target.unlink()
                return True
            except Exception as e:
                logger.warning("Failed to delete %s: %s", target, e)
                return False
        return False


# Default local storage instance under storage/
_default_storage_path = Path(__file__).resolve().parent.parent.parent / "storage"
storage = LocalStorage(_default_storage_path)
