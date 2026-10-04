"""
satquery.agent.sensor_router
============================
Autonomous Sensor Router (Agent 3).
Inspects raster metadata (band count, wavelengths, polarizations, spatial resolution),
user query intent, and environmental conditions to automatically determine sensor
modalities and optimal specialist routing.

Routing Rules:
- Flood + cloudy scene            -> SAR Specialist
- Vegetation health               -> Optical + NDVI
- Urban expansion                 -> Optical + NDBI + Change Detection
- Multi-temporal flood/disaster   -> Optical + SAR + Change Detection
- Generic object / scene question -> VQA + Grounding
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SensorCategory = Literal["optical", "sar", "optical_sar", "multispectral", "panchromatic", "rgb", "unknown"]


class SensorProfile(BaseModel):
    """Profile describing the sensor characteristics of a single satellite asset."""
    asset_id: str
    sensor_category: SensorCategory
    band_count: int
    has_polarization: bool = False
    polarizations: List[str] = Field(default_factory=list)
    has_nir: bool = False
    has_swir: bool = False
    has_red_edge: bool = False
    estimated_gsd_m: float = 10.0
    detected_sensor_name: str = "generic_sensor"
    is_cloud_affected: bool = False


class RoutingDecision(BaseModel):
    """Routing plan specifying the assigned specialists and analysis strategy."""
    primary_sensor_category: SensorCategory
    recommended_specialists: List[str]
    spectral_indices: List[str]
    use_sar_penetration: bool = False
    use_cross_modal_fusion: bool = False
    explanation: str


class SensorRouter:
    """
    Agent 3: Autonomous Sensor Router.
    Analyzes raster metadata and query intent to dispatch appropriate specialists.
    """

    @classmethod
    def profile_asset(cls, asset_id: str, metadata: Dict[str, Any]) -> SensorProfile:
        """
        Inspects raster metadata dictionary (bands, tags, descriptions, resolution).
        """
        bands = int(metadata.get("bands") or metadata.get("count") or 1)
        tags = metadata.get("tags") or {}
        descriptions = [str(d).lower() for d in metadata.get("descriptions") or []]
        fn = str(metadata.get("filename") or "").lower()

        # Check for SAR polarizations (VV, VH, HH, HV)
        pols: List[str] = []
        for pol in ["vv", "vh", "hh", "hv"]:
            if pol in fn or any(pol in d for d in descriptions) or pol in str(tags).lower():
                pols.append(pol.upper())

        is_sar = len(pols) > 0 or "sar" in fn or "risat" in fn or "sentinel-1" in fn or "s1" in fn

        # Check for multispectral bands (NIR, SWIR, Red Edge)
        has_nir = False
        has_swir = False
        has_red_edge = False

        if not is_sar:
            if bands >= 4:
                has_nir = True  # Standard 4-band (B, G, R, NIR)
            if bands >= 5:
                has_swir = True  # Standard 5-band includes SWIR
            if "nir" in str(tags).lower() or any("nir" in d for d in descriptions):
                has_nir = True
            if "swir" in str(tags).lower() or any("swir" in d for d in descriptions):
                has_swir = True

        # Sensor category categorization
        if is_sar:
            category: SensorCategory = "sar"
            sensor_name = "SAR (RISAT-1 / Sentinel-1)"
        elif bands >= 4:
            category = "multispectral"
            sensor_name = "Multispectral Optical (Cartosat-2S / Sentinel-2 / Landsat)"
        elif bands == 3:
            category = "rgb"
            sensor_name = "RGB Optical"
        elif bands == 1:
            category = "panchromatic"
            sensor_name = "Panchromatic High-Resolution"
        else:
            category = "optical"
            sensor_name = "Generic Optical"

        gsd = float(metadata.get("resolution_m") or metadata.get("gsd") or 10.0)

        return SensorProfile(
            asset_id=asset_id,
            sensor_category=category,
            band_count=bands,
            has_polarization=len(pols) > 0,
            polarizations=pols,
            has_nir=has_nir,
            has_swir=has_swir,
            has_red_edge=has_red_edge,
            estimated_gsd_m=gsd,
            detected_sensor_name=sensor_name,
            is_cloud_affected=bool(metadata.get("cloud_cover_pct", 0) > 20.0)
        )

    @classmethod
    def route_query(
        cls,
        query: str,
        asset_profiles: List[SensorProfile]
    ) -> RoutingDecision:
        """
        Determines the optimal specialist tools and spectral indices based on user intent
        and available sensor modalities.
        """
        q = query.lower()
        has_sar = any(p.sensor_category == "sar" for p in asset_profiles)
        has_optical = any(p.sensor_category in ["optical", "multispectral", "rgb", "panchromatic"] for p in asset_profiles)
        is_cloudy = any(p.is_cloud_affected for p in asset_profiles)

        specialists: List[str] = []
        indices: List[str] = []
        use_sar = False
        use_fusion = False

        # Intent classification heuristics
        is_flood = any(w in q for w in ["flood", "water", "inundat", "submerge", "river", "lake"])
        is_vegetation = any(w in q for w in ["vegetation", "forest", "crop", "tree", "deforest", "green"])
        is_urban = any(w in q for w in ["urban", "building", "construct", "city", "built", "expansion", "road"])
        is_change = any(w in q for w in ["change", "difference", "compare", "between", "t1", "t2", "expansion", "loss", "growth"])

        # Rule 1: Optical + SAR Co-presence
        if has_optical and has_sar:
            category = "optical_sar"
            use_fusion = True
            use_sar = True
            specialists.extend(["multimodal_fusion", "scientific_judge"])
            if is_change:
                specialists.append("change_detection")
            if is_flood:
                indices.extend(["ndwi", "db_vv", "rvi"])
                explanation = "Optical and SAR co-registered pair detected: routed to Cross-Modal Fusion for flood and water mapping with microwave cloud penetration."
            else:
                indices.extend(["ndvi", "ndbi", "rvi"])
                explanation = "Multimodal Optical + SAR pair routed to Cross-Modal Fusion and Scientific Judge."

        # Rule 2: SAR Only or Flood + Cloud
        elif has_sar or (is_flood and is_cloudy and has_sar):
            category = "sar"
            use_sar = True
            specialists.append("sar_specialist")
            if is_change:
                specialists.append("change_detection")
            indices.extend(["db_vv", "db_vh", "rvi"])
            explanation = "SAR microwave imagery identified: routed to SAR Specialist for active microwave backscatter differencing and inundation extraction."

        # Rule 3: Optical Vegetation / Deforestation
        elif is_vegetation:
            category = "multispectral" if any(p.has_nir for p in asset_profiles) else "optical"
            indices.append("ndvi")
            if any(p.has_swir for p in asset_profiles):
                indices.append("evi")
            if is_change:
                specialists.extend(["change_detection", "physics_verifier"])
                explanation = "Vegetation query on optical imagery: routed to Change Detection with NDVI spectral differencing and STSF pseudo-change suppression."
            else:
                specialists.extend(["vqa_specialist", "grounding_specialist"])
                explanation = "Vegetation inspection on optical imagery: routed to VQA and Grounding specialists."

        # Rule 4: Urban Expansion / Building Detection
        elif is_urban:
            category = "multispectral" if any(p.has_swir for p in asset_profiles) else "optical"
            indices.extend(["ndbi", "ndvi"])
            if is_change:
                specialists.extend(["change_detection", "physics_verifier"])
                explanation = "Urban change query: routed to Change Detection with NDBI/NDVI spectral differencing and polygonization."
            else:
                specialists.extend(["grounding_specialist", "vqa_specialist"])
                explanation = "Urban structure query: routed to Grounding Specialist for open-vocabulary building and road extraction."

        # Rule 5: Generic / VQA / Captioning
        else:
            category = "optical"
            if "describe" in q or "caption" in q or "land cover" in q:
                specialists.append("captioning_specialist")
                explanation = "Scene description query: routed to Scene Captioning Specialist."
            elif is_change:
                specialists.append("change_detection")
                indices.append("ndvi")
                explanation = "General bi-temporal comparison query: routed to Change Detection engine."
            else:
                specialists.extend(["vqa_specialist", "grounding_specialist"])
                explanation = "Visual question query: routed to VQA and Grounding specialists."

        return RoutingDecision(
            primary_sensor_category=category,
            recommended_specialists=specialists,
            spectral_indices=indices,
            use_sar_penetration=use_sar,
            use_cross_modal_fusion=use_fusion,
            explanation=explanation
        )


sensor_router = SensorRouter()
