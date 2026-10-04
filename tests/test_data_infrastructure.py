"""
tests/test_data_infrastructure.py
=================================
Unit tests for Phase 4:
- Storage Abstraction (satquery.storage)
- Database & Session Store (satquery.db)
- Async Job Dispatcher (satquery.queue)
- Satellite Provider Abstraction (satquery.providers)
- Model Provider Abstraction (satquery.models)
"""

from __future__ import annotations

import asyncio
import time
import pytest

from satquery.storage.local import LocalStorage
from satquery.db.session_store import DatabaseSessionStore
from satquery.db.models import ImageAssetRecord, QueryRecord, FindingDBRecord
from satquery.queue.dispatcher import JobDispatcher
from satquery.providers.local import LocalDatasetProvider
from satquery.models.provider import OfflineMockProvider


def test_local_storage(tmp_path):
    storage = LocalStorage(tmp_path)
    # Save preview
    data = b"fake_png_preview_data"
    saved_path = storage.save_bytes("previews", "thumb_01.png", data)
    assert storage.exists("previews", "thumb_01.png") is True

    # Read back
    read_data = storage.read_bytes("previews", "thumb_01.png")
    assert read_data == data

    # List files
    files = storage.list_files("previews")
    assert "thumb_01.png" in files

    # Delete
    assert storage.delete("previews", "thumb_01.png") is True
    assert storage.exists("previews", "thumb_01.png") is False


def test_database_session_store(tmp_path):
    db_file = tmp_path / "test_sessions.db"
    store = DatabaseSessionStore(db_file)

    # 1. Session creation
    sess = store.create_or_get_session("sess_100", title="Kerala Flood Analysis")
    assert sess.session_id == "sess_100"
    assert sess.title == "Kerala Flood Analysis"

    # 2. Asset registration
    asset = ImageAssetRecord(
        asset_id="asset_t1",
        session_id="sess_100",
        filename="T1.tif",
        file_path="/data/T1.tif",
        file_size_bytes=1048576,
        crs="EPSG:32643",
        resolution_m=0.65,
        width=512,
        height=512,
        bands=4,
        sensor_category="multispectral",
        sha256_checksum="abc123sha"
    )
    store.register_asset(asset)

    # Verify session active assets updated
    sess_updated = store.create_or_get_session("sess_100")
    assert "asset_t1" in sess_updated.active_asset_ids

    # 3. Query recording
    query = QueryRecord(
        query_id="q_001",
        session_id="sess_100",
        query_text="Find water bodies",
        answer="Found 4 water regions",
        composite_confidence=0.92
    )
    store.record_query(query)

    # 4. History retrieval
    history = store.get_session_history("sess_100")
    assert len(history) == 1
    assert history[0]["query_text"] == "Find water bodies"
    assert history[0]["composite_confidence"] == 0.92


def test_job_dispatcher():
    dispatcher = JobDispatcher()

    async def sample_worker(job_id: str):
        await asyncio.sleep(0.01)
        return {"status": "ok", "computed": 42}

    async def run_test():
        job = dispatcher.submit_job(
            query="Analyze change",
            session_id="sess_test",
            coroutine_fn=sample_worker
        )
        assert job.status in ["queued", "running"]

        for _ in range(50):
            if job.status == "completed":
                break
            await asyncio.sleep(0.02)
        return job

    completed_job = asyncio.run(run_test())
    assert completed_job.status == "completed"
    assert completed_job.result == {"status": "ok", "computed": 42}


def test_satellite_and_model_providers(tmp_path):
    # Local satellite provider
    provider = LocalDatasetProvider(tmp_path)
    res = provider.search_products([0, 0, 1, 1], "2024-01-01", "2024-01-02")
    assert isinstance(res, list)

    # Offline mock model provider
    mock_model = OfflineMockProvider()
    resp = mock_model.generate_response("Find water bodies")
    assert "water" in resp.lower()
