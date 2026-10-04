"""
satquery.db.models
==================
Relational database models (Section 27).
Implements pure-Python schema for Sessions, Assets, Queries, Runs, Findings, and Evidence.
Compatible with SQLite (local zero-dependency mode) and PostgreSQL/PostGIS.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ImageAssetRecord(BaseModel):
    asset_id: str
    session_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    crs: str = "EPSG:4326"
    resolution_m: float = 10.0
    width: int = 0
    height: int = 0
    bands: int = 1
    sensor_category: str = "optical"
    sha256_checksum: str
    created_at: float = Field(default_factory=time.time)


class QueryRecord(BaseModel):
    query_id: str
    session_id: str
    query_text: str
    target_entity: str = "general"
    task_type: str = "vqa"
    status: str = "completed"  # queued, running, completed, failed
    answer: str = ""
    composite_confidence: float = 0.0
    created_at: float = Field(default_factory=time.time)


class AnalysisRunRecord(BaseModel):
    run_id: str
    query_id: str
    workflow: str
    status: str = "completed"
    duration_ms: float = 0.0
    execution_trace_json: str = "[]"
    run_manifest_json: str = "{}"
    created_at: float = Field(default_factory=time.time)


class FindingDBRecord(BaseModel):
    finding_id: str
    run_id: str
    label: str
    verdict: str  # confirmed, probable, uncertain, rejected, target_not_found
    confidence_score: float
    confidence_label: str
    area_m2: float = 0.0
    area_ha: float = 0.0
    geojson_geometry_json: str = "{}"
    explanation: str = ""
    created_at: float = Field(default_factory=time.time)


class EvidenceDBRecord(BaseModel):
    evidence_id: str
    finding_id: str
    source_asset_id: str
    workflow: str
    agent_name: str
    confidence: float
    physics_checks_json: str = "{}"
    created_at: float = Field(default_factory=time.time)


class SessionRecord(BaseModel):
    session_id: str
    title: str = "Earth Observation Session"
    active_asset_ids: List[str] = Field(default_factory=list)
    query_history: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
