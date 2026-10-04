"""
Tests for SatQuery AI Multi-Format Report Generator.
Verifies JSON, GeoJSON (RFC 7946), Markdown, and ReportLab PDF outputs.
"""

import json
from pathlib import Path
from satquery.reports.generator import ReportGenerator, report_generator


def test_report_generator_json():
    mock_run = {
        "session_id": "test_session_12345",
        "query": "Is there flood inundation near Mumbai?",
        "final_answer": "Confirmed 14.5 ha water inundation. Radar specular backscatter drop verified at -18.2 dB.",
        "confidence": 0.92,
        "execution_mode": "hybrid",
        "sensor_calibration_badge": "ISRO Cartosat-2S & RISAT-1A",
        "run_signature_hash": "a1b2c3d4e5f60123456789abcdef0123456789abcdef0123456789abcdef01",
        "report_tamper_token": "hmac_token_valid_9988",
        "trace": [
            {
                "step_number": 1,
                "tool_called": "geocv_change_detector",
                "why_this_tool": "Establish baseline surface difference",
                "step_confidence": 0.95
            },
            {
                "step_number": 2,
                "tool_called": "sar_specialist",
                "why_this_tool": "Verify water via radar backscatter attenuation",
                "step_confidence": 0.89
            }
        ]
    }

    json_str = report_generator.generate_json(mock_run)
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["report_type"] == "SATQUERY_INTELLIGENCE_AUDIT_JSON"
    assert parsed["session_id"] == "test_session_12345"
    assert parsed["confidence"] == 0.92
    assert len(parsed["trace"]) == 2


def test_report_generator_geojson():
    mock_run = {
        "session_id": "test_session_geojson",
        "query": "Identify flooded parcels",
        "final_answer": "Detected flooded agricultural sectors.",
        "confidence": 0.88,
        "composite_overlays": {
            "bboxes": [
                {"ymin": 0.2, "xmin": 0.3, "ymax": 0.6, "xmax": 0.7, "label": "Water Inundation", "confidence": 0.91}
            ]
        }
    }

    geojson = report_generator.generate_geojson(mock_run)
    assert geojson["type"] == "FeatureCollection"
    assert "satquery_metadata" in geojson
    assert len(geojson["features"]) == 1
    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Polygon"
    assert feature["properties"]["label"] == "Water Inundation"


def test_report_generator_markdown():
    mock_run = {
        "session_id": "test_session_md",
        "query": "Detect deforestation along riverbank",
        "final_answer": "Detected 4.2 ha tree canopy loss.",
        "confidence": 0.86,
        "sensor_calibration_badge": "Cartosat-2S Paired",
        "run_signature_hash": "c0ffee1234567890abcdef"
    }

    md = report_generator.generate_markdown(mock_run)
    assert "# SATQUERY AI — EARTH OBSERVATION INTELLIGENCE REPORT" in md
    assert "test_session_md" in md
    assert "4.2 ha tree canopy loss" in md
    assert "86.0% (HIGH)" in md
    assert "c0ffee1234567890abcdef" in md


def test_report_generator_pdf(tmp_path: Path):
    mock_run = {
        "session_id": "test_session_pdf",
        "query": "Verify bridge integrity and coastal structures",
        "final_answer": "Target structure identified and verified intact with 94.2% confidence.",
        "confidence": 0.942,
        "sensor_calibration_badge": "Cartosat High-Res Optical",
        "run_signature_hash": "999888777666555444333222111000aaabbbcccdddeeefff0001112223334445",
        "report_tamper_token": "tamper_token_xyz"
    }

    out_file = tmp_path / "test_report.pdf"
    gen = ReportGenerator(output_dir=tmp_path)
    result_path = gen.generate_pdf(mock_run, output_path=out_file)

    assert result_path.exists()
    assert result_path.stat().st_size > 1000
    with open(result_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"
