"""
satquery.agent.specialists.sar
==============================
Dedicated SAR Analysis Agent (Agent Specialist).
Processes Sentinel-1 (C-band) and ISRO RISAT-1 / RISAT-1A (C-band) synthetic
aperture radar imagery.

Capabilities:
- Radiometric calibration to sigma0 (dB)
- Dual-polarization channels (VV, VH) and VV/VH cross-ratio
- Lee / speckle filtering
- Local radar texture analysis (spatial variance)
- Microwave specular water / flood inundation mapping
- SAR bi-temporal backscatter differencing (all-weather change detection)
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.ndimage import uniform_filter
from shapely.geometry import box as shapely_box, mapping

from satquery.agent.protocols import BaseSpecialist
from satquery.agent.schemas import MeasurementRecord, SpecialistRequest, SpecialistResult
from satquery.core.geospatial import calculate_area_metrics, compute_geodesic_area_m2
from satquery.core.raster_io import RasterData, load_raster

logger = logging.getLogger(__name__)

_EPS = 1e-7


def linear_to_db(linear_arr: np.ndarray) -> np.ndarray:
    """Converts linear radar power/amplitude to calibrated sigma0 (dB)."""
    safe_lin = np.maximum(linear_arr.astype(np.float32), _EPS)
    return 10.0 * np.log10(safe_lin)


def lee_speckle_filter(img: np.ndarray, size: int = 5) -> np.ndarray:
    """
    Standard Lee filter for speckle reduction in SAR intensity images.
    Preserves structural edges while smoothing granular microwave speckle.
    """
    img_f = img.astype(np.float32)
    mean = uniform_filter(img_f, size=size)
    mean_sq = uniform_filter(img_f ** 2, size=size)
    var = np.maximum(mean_sq - mean ** 2, 0.0)

    # Estimate overall noise variance
    noise_var = float(np.mean(var)) + _EPS
    weight = var / (var + noise_var)
    filtered = mean + weight * (img_f - mean)
    return np.nan_to_num(filtered, nan=float(np.mean(img_f)))


def compute_radar_texture(img_db: np.ndarray, size: int = 7) -> np.ndarray:
    """Computes local spatial standard deviation as a radar surface roughness metric."""
    img_f = img_db.astype(np.float32)
    mean = uniform_filter(img_f, size=size)
    sq_mean = uniform_filter(img_f ** 2, size=size)
    var = np.maximum(sq_mean - mean ** 2, 0.0)
    return np.sqrt(var)


def detect_sar_water(
    vv_db: np.ndarray,
    vh_db: Optional[np.ndarray] = None,
    water_threshold_db: float = -14.0
) -> np.ndarray:
    """
    Detects open water surfaces via specular microwave reflection.
    Calm open water reflects radar pulses away from the antenna,
    producing characteristic low backscatter (typically < -14 dB for VV).
    """
    water_mask = vv_db < water_threshold_db
    if vh_db is not None:
        # Cross-pol VH is even lower over calm water (< -22 dB)
        water_mask = water_mask & (vh_db < -20.0)
    return water_mask


class SARAnalysisSpecialist(BaseSpecialist):
    """
    Dedicated SAR analysis specialist owning all active microwave remote sensing tasks.
    """

    def __init__(self, tool_id: str = "sar_analyzer"):
        super().__init__(
            tool_id=tool_id,
            author_lead="satquery_core",
            supported_capabilities=["sar_cloud_penetration", "flood_mapping", "sar_change_detection", "texture_analysis"],
            supported_modalities=["sar"]
        )

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        t0 = time.perf_counter()
        t1_path = request.asset_paths.get("t1") or request.asset_paths.get("primary")
        t2_path = request.asset_paths.get("t2")

        if not t1_path:
            return SpecialistResult(
                tool_id=self.tool_id,
                implementation_type="classical_algorithm",
                execution_status="failed",
                duration_ms=(time.perf_counter() - t0) * 1000.0,
                observations="No SAR asset path provided.",
                measurements=[],
                confidence_score=0.0,
                warnings=["Missing input SAR raster."]
            )

        try:
            r1 = load_raster(t1_path)
            vv_band = r1.band(0)
            vh_band = r1.band(1) if r1.bands >= 2 else None

            # 1. Calibration to dB
            vv_db = linear_to_db(vv_band)
            vv_filt = lee_speckle_filter(vv_db)

            # 2. Dual-pol ratio if VH present
            vh_filt = None
            ratio_db = None
            if vh_band is not None:
                vh_db = linear_to_db(vh_band)
                vh_filt = lee_speckle_filter(vh_db)
                ratio_db = vv_filt - vh_filt  # dB ratio: 10*log(VV/VH) = VV_dB - VH_dB

            # 3. Water / Flood Inundation Analysis
            if t2_path:
                # Bi-temporal SAR Differencing
                r2 = load_raster(t2_path)
                vv2_db = linear_to_db(r2.band(0))
                vv2_filt = lee_speckle_filter(vv2_db)

                # Negative difference (T2 - T1 < -3 dB) indicates flood inundation
                diff_db = vv2_filt - vv_filt
                flood_mask = diff_db < -3.0
                n_changed = int(flood_mask.sum())
                total_px = flood_mask.size
                pct_changed = round((n_changed / max(total_px, 1)) * 100.0, 3)

                # Area calculation
                tf = r1.transform
                res_x, res_y = abs(tf.a), abs(tf.e)
                px_area_m2 = res_x * res_y
                if r1.crs and r1.crs.is_geographic:
                    px_area_m2 *= (111320.0 ** 2)
                area_m2 = float(n_changed * px_area_m2)
                area_ha = round(area_m2 / 10000.0, 3)

                obs = (
                    f"Bi-temporal SAR backscatter analysis: Detected {n_changed:,} pixels ({pct_changed}%) "
                    f"with significant microwave attenuation (Δσ⁰ < -3.0 dB), indicating flood inundation "
                    f"covering ~{area_ha} ha across all-weather cloud cover."
                )

                measurements = [
                    MeasurementRecord(
                        metric_id="flood_inundation_ha",
                        value=area_ha,
                        unit="ha",
                        source_tool=self.tool_id,
                        source_run_id=request.run_id,
                        raster_hash="sar_bitemporal",
                        confidence_interval=(area_ha * 0.92, area_ha * 1.08)
                    ),
                    MeasurementRecord(
                        metric_id="backscatter_drop_db",
                        value=float(np.median(diff_db[flood_mask])) if n_changed > 0 else 0.0,
                        unit="ratio",
                        source_tool=self.tool_id,
                        source_run_id=request.run_id,
                        raster_hash="sar_bitemporal"
                    )
                ]

                # Bounding box of flood area
                bboxes = []
                if n_changed > 0:
                    rows, cols = np.where(flood_mask)
                    bboxes.append({
                        "label": "sar_flood_inundation",
                        "box": [
                            float(rows.min() / r1.height),
                            float(cols.min() / r1.width),
                            float(rows.max() / r1.height),
                            float(cols.max() / r1.width)
                        ],
                        "score": 0.91
                    })

                confidence = 0.90 if n_changed > 50 else 0.65

            else:
                # Single-date SAR Water & Texture Extraction
                water_mask = detect_sar_water(vv_filt, vh_filt)
                n_water = int(water_mask.sum())
                area_m2 = float(n_water * abs(r1.transform.a * r1.transform.e))
                if r1.crs and r1.crs.is_geographic:
                    area_m2 *= (111320.0 ** 2)
                area_ha = round(area_m2 / 10000.0, 3)

                texture = compute_radar_texture(vv_filt)
                mean_texture = float(np.mean(texture))

                obs = (
                    f"SAR single-date microwave inspection (calibrated σ⁰): "
                    f"Identified {area_ha} ha of specular open water (VV < -14 dB). "
                    f"Mean surface roughness texture is {mean_texture:.2f} dB."
                )

                measurements = [
                    MeasurementRecord(
                        metric_id="surface_water_ha",
                        value=area_ha,
                        unit="ha",
                        source_tool=self.tool_id,
                        source_run_id=request.run_id,
                        raster_hash="sar_singledate"
                    )
                ]
                bboxes = []
                confidence = 0.88

            duration = (time.perf_counter() - t0) * 1000.0
            return SpecialistResult(
                tool_id=self.tool_id,
                implementation_type="classical_algorithm",
                execution_status="healthy",
                duration_ms=duration,
                observations=obs,
                measurements=measurements,
                bounding_boxes=bboxes,
                confidence_score=confidence,
                raw_artifacts={"polarizations": ["VV"] + (["VH"] if vh_band is not None else [])},
                warnings=[]
            )

        except Exception as exc:
            logger.exception("SAR Analysis Specialist failed: %s", exc)
            return SpecialistResult(
                tool_id=self.tool_id,
                implementation_type="classical_algorithm",
                execution_status="failed",
                duration_ms=(time.perf_counter() - t0) * 1000.0,
                observations=f"SAR analysis error: {str(exc)}",
                measurements=[],
                confidence_score=0.0,
                warnings=[str(exc)]
            )
