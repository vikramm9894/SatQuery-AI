import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)


def test_png_upload_and_preview_generation():
    test_img = settings.BASE_DIR.parent / "test_image.png"
    assert test_img.exists()

    session_id = f"test_img_sess_{uuid.uuid4().hex[:8]}"

    with open(test_img, "rb") as f:
        resp = client.post(
            "/api/validate-inputs",
            data={"session_id": session_id},
            files={"files": ("test_image.png", f, "image/png")}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["mode"] == "single_image"
    assert len(data["images"]) == 1

    img_meta = data["images"][0]
    assert img_meta["preview_url"] is not None
    assert f"/api/session/{session_id}/preview/" in img_meta["preview_url"]

    # Fetch preview
    preview_resp = client.get(img_meta["preview_url"])
    assert preview_resp.status_code == 200
    assert preview_resp.headers["content-type"] == "image/png"
    assert len(preview_resp.content) > 0

    # Query with the uploaded image
    q_resp = client.post(
        "/api/query",
        json={
            "session_id": session_id,
            "query": "Describe the land cover in this image."
        }
    )
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert len(q_data["final_answer"]) > 0
    assert "composite_overlays" in q_data
    bboxes = q_data["composite_overlays"].get("bboxes", [])
    assert len(bboxes) > 0
    assert "box" in bboxes[0]


def test_demo_scenario_flood_loading_and_change_query():
    session_id = f"test_flood_sess_{uuid.uuid4().hex[:8]}"

    # Load flood demo scenario
    resp = client.post(
        "/api/load-sample",
        json={"session_id": session_id, "scenario_id": "flood"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["mode"] == "bi_temporal"
    assert len(data["images"]) == 2
    assert data["images"][0]["preview_url"] is not None
    assert data["images"][1]["preview_url"] is not None

    # Verify preview exists
    p1 = client.get(data["images"][0]["preview_url"])
    assert p1.status_code == 200
    assert p1.headers["content-type"] == "image/png"

    # Query change detection
    q_resp = client.post(
        "/api/query",
        json={
            "session_id": session_id,
            "query": "What changed between T1 and T2? Suppress seasonal pseudo-changes."
        }
    )
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert "change" in q_data["final_answer"].lower()
    assert len(q_data["composite_overlays"].get("bboxes", [])) > 0
    assert len(q_data["composite_overlays"].get("features", [])) > 0


def test_demo_scenario_cartosat_sar_loading():
    session_id = f"test_sar_sess_{uuid.uuid4().hex[:8]}"

    resp = client.post(
        "/api/load-sample",
        json={"session_id": session_id, "scenario_id": "cartosat_sar"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["mode"] == "optical_sar"
    assert len(data["images"]) == 2

    # Query optical-sar fusion
    q_resp = client.post(
        "/api/query",
        json={
            "session_id": session_id,
            "query": "Assess ground inundation with SAR microwave penetration through cloud cover."
        }
    )
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert len(q_data["composite_overlays"].get("bboxes", [])) > 0
