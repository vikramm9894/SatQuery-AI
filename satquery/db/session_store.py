"""
satquery.db.session_store
=========================
SQLite-backed persistent session and analysis store (Section 26 & 27).
Manages multi-turn conversation memory, asset registrations, analysis runs,
and geospatial findings without requiring external database services.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from satquery.db.models import (
    AnalysisRunRecord,
    EvidenceDBRecord,
    FindingDBRecord,
    ImageAssetRecord,
    QueryRecord,
    SessionRecord,
)

logger = logging.getLogger(__name__)


class DatabaseSessionStore:
    """
    Thread-safe SQLite database store for SatQuery AI.
    """

    def __init__(self, db_path: Path | str):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT,
                active_asset_ids TEXT,
                query_history TEXT,
                created_at REAL,
                updated_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                session_id TEXT,
                filename TEXT,
                file_path TEXT,
                file_size_bytes INTEGER,
                crs TEXT,
                resolution_m REAL,
                width INTEGER,
                height INTEGER,
                bands INTEGER,
                sensor_category TEXT,
                sha256_checksum TEXT,
                created_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                query_id TEXT PRIMARY KEY,
                session_id TEXT,
                query_text TEXT,
                target_entity TEXT,
                task_type TEXT,
                status TEXT,
                answer TEXT,
                composite_confidence REAL,
                created_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                run_id TEXT,
                label TEXT,
                verdict TEXT,
                confidence_score REAL,
                confidence_label TEXT,
                area_m2 REAL,
                area_ha REAL,
                geojson_geometry_json TEXT,
                explanation TEXT,
                created_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                finding_id TEXT,
                source_asset_id TEXT,
                workflow TEXT,
                agent_name TEXT,
                confidence REAL,
                physics_checks_json TEXT,
                created_at REAL
            );
            """)
            conn.commit()

    def create_or_get_session(self, session_id: str, title: str = "Earth Observation Session") -> SessionRecord:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            if row:
                return SessionRecord(
                    session_id=row["session_id"],
                    title=row["title"],
                    active_asset_ids=json.loads(row["active_asset_ids"]),
                    query_history=json.loads(row["query_history"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            # Create new
            now = time.time()
            cur.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, title, json.dumps([]), json.dumps([]), now, now)
            )
            conn.commit()
            return SessionRecord(session_id=session_id, title=title, created_at=now, updated_at=now)

    def register_asset(self, asset: ImageAssetRecord) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset.asset_id, asset.session_id, asset.filename, asset.file_path,
                asset.file_size_bytes, asset.crs, asset.resolution_m, asset.width,
                asset.height, asset.bands, asset.sensor_category, asset.sha256_checksum,
                asset.created_at
            ))
            # Update session active assets
            cur.execute("SELECT active_asset_ids FROM sessions WHERE session_id = ?", (asset.session_id,))
            row = cur.fetchone()
            if row:
                assets = json.loads(row["active_asset_ids"])
                if asset.asset_id not in assets:
                    assets.append(asset.asset_id)
                cur.execute(
                    "UPDATE sessions SET active_asset_ids = ?, updated_at = ? WHERE session_id = ?",
                    (json.dumps(assets), time.time(), asset.session_id)
                )
            conn.commit()

    def record_query(self, query: QueryRecord) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO queries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query.query_id, query.session_id, query.query_text, query.target_entity,
                query.task_type, query.status, query.answer, query.composite_confidence,
                query.created_at
            ))
            # Update session history
            cur.execute("SELECT query_history FROM sessions WHERE session_id = ?", (query.session_id,))
            row = cur.fetchone()
            if row:
                hist = json.loads(row["query_history"])
                hist.append(query.query_id)
                cur.execute(
                    "UPDATE sessions SET query_history = ?, updated_at = ? WHERE session_id = ?",
                    (json.dumps(hist), time.time(), query.session_id)
                )
            conn.commit()

    def record_finding(self, finding: FindingDBRecord) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                finding.finding_id, finding.run_id, finding.label, finding.verdict,
                finding.confidence_score, finding.confidence_label, finding.area_m2,
                finding.area_ha, finding.geojson_geometry_json, finding.explanation,
                finding.created_at
            ))
            conn.commit()

    def record_evidence(self, ev: EvidenceDBRecord) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ev.evidence_id, ev.finding_id, ev.source_asset_id, ev.workflow,
                ev.agent_name, ev.confidence, ev.physics_checks_json, ev.created_at
            ))
            conn.commit()

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT query_id, query_text, task_type, answer, composite_confidence, created_at
            FROM queries WHERE session_id = ? ORDER BY created_at ASC
            """, (session_id,))
            return [dict(r) for r in cur.fetchall()]


# Default singleton database store
_default_db_file = Path(__file__).resolve().parent.parent.parent / "storage" / "satquery_platform.db"
db_store = DatabaseSessionStore(_default_db_file)
