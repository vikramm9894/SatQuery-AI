import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import (
    DemoScenarioRequest,
    ExportReportRequest,
    QueryRequest,
    QueryResponse,
    ToolInfo,
    ValidationResult,
)
from app.services.agent import react_agent
from app.services.exporter import report_exporter
from app.services.input_validator import input_validator
from app.services.registry import registry
from app.services.session_manager import session_manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Agentic Earth-Observation Vision-Language Assistant for ISRO SIH26167"
)

# CORS middleware for Next.js / React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "gpu_allowed": settings.ALLOW_GPU
    }

@app.get("/api/tools", response_model=list[ToolInfo])
def get_tools_status():
    """Surfaces active specialist models, execution modes (real vs fallback), and hardware tiers."""
    return registry.list_tools()

@app.post("/api/validate-inputs", response_model=ValidationResult)
async def validate_inputs(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(None)
):
    """
    Validates uploaded GeoTIFFs, checks CRS/resolution/bounds, and performs pixel-level co-registration.
    """
    sid = session_id or str(uuid.uuid4())
    session_dir = session_manager.get_session_dir(sid, "uploads")

    saved_paths: list[Path] = []
    total_size = 0

    for upload in files:
        file_path = session_dir / upload.filename
        with open(file_path, "wb") as buffer:
            while content := await upload.read(1024 * 1024):
                total_size += len(content)
                if total_size > settings.MAX_SESSION_SIZE_BYTES:
                    raise HTTPException(status_code=413, detail="Total session upload exceeds 500MB limit.")
                buffer.write(content)
        saved_paths.append(file_path)

    result = input_validator.validate_session_inputs(sid, saved_paths)
    session_manager.create_or_update_session(sid, result)
    return result

@app.get("/api/session/{session_id}/preview/{image_id}")
def get_image_preview(session_id: str, image_id: str):
    """
    Returns an 8-bit normalized PNG preview for any uploaded/session raster.
    """
    preview_file = settings.BASE_DIR / "storage" / "previews" / session_id / f"{image_id}.png"
    if not preview_file.exists():
        # Check if corresponding upload exists
        uploads_dir = settings.UPLOADS_DIR / session_id
        session = session_manager.get_session(session_id)
        val = session.get("validation", {}) if session else {}
        matched_file = None
        for img in val.get("images", []):
            if img.get("id") == image_id:
                fn = img.get("filename")
                if fn and (uploads_dir / fn).exists():
                    matched_file = uploads_dir / fn
                    break
        if not matched_file:
            all_files = list(uploads_dir.glob("*.*"))
            if all_files:
                matched_file = all_files[0]

        if matched_file:
            input_validator.generate_preview_png(matched_file, preview_file)

    if preview_file.exists():
        return FileResponse(preview_file, media_type="image/png")
    raise HTTPException(status_code=404, detail="Preview not found.")

@app.post("/api/load-sample", response_model=ValidationResult)
def load_sample_scenario(request: DemoScenarioRequest):
    """
    Loads a pre-packaged ISRO Earth-observation scenario into the active session.
    """
    import shutil
    sid = request.session_id
    session_dir = session_manager.get_session_dir(sid, "uploads")
    root_dir = settings.BASE_DIR.parent
    demo_dir = root_dir / "demo_data"
    sample_dir = settings.BASE_DIR / "sample_data"

    pairs: list[tuple[Path, str]] = []
    if request.scenario_id == "flood":
        src = demo_dir / "flood"
        if src.exists():
            pairs = [(src / "T1.tif", "T1_flood_optical.tif"), (src / "T2.tif", "T2_flood_optical.tif")]
    elif request.scenario_id == "deforestation":
        src = demo_dir / "deforestation"
        if src.exists():
            pairs = [(src / "T1.tif", "T1_forest_optical.tif"), (src / "T2.tif", "T2_forest_cleared.tif")]
    elif request.scenario_id == "urban":
        src = demo_dir / "urban"
        if src.exists():
            pairs = [(src / "T1.tif", "T1_urban_pre.tif"), (src / "T2.tif", "T2_urban_post.tif")]
    elif request.scenario_id == "cartosat_sar":
        pairs = [
            (sample_dir / "cartosat2s_optical_20240901.tif", "cartosat2s_optical.tif"),
            (sample_dir / "risat1a_sar_20240901.tif", "risat1a_sar.tif")
        ]

    if not pairs or not all(p[0].exists() for p in pairs):
        # Fallback to backend sample data
        pairs = [
            (sample_dir / "cartosat2s_optical_20240301.tif", "cartosat2s_t1.tif"),
            (sample_dir / "cartosat2s_optical_20240901.tif", "cartosat2s_t2.tif")
        ]

    saved_paths: list[Path] = []
    for src_path, target_name in pairs:
        if src_path.exists():
            dest = session_dir / target_name
            shutil.copy(src_path, dest)
            saved_paths.append(dest)

    result = input_validator.validate_session_inputs(sid, saved_paths)
    session_manager.create_or_update_session(sid, result)
    return result

@app.post("/api/query", response_model=QueryResponse)
def execute_query(request: QueryRequest):
    """
    Agentic ReAct query endpoint: plans tool sequence, executes specialists,
    fuses multi-sensor evidence, and provides an auditable investigation trace.
    """
    try:
        return react_agent.run_query(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {e!s}")

@app.post("/api/export-report")
def export_report(request: ExportReportRequest, format: str = "pdf"):
    """
    Exports a downloadable PDF intelligence report or GeoJSON with cryptographic audit stamps.
    """
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Retrieve last query response or use provided
    query_resp = request.query_response
    if not query_resp:
        history = session.get("query_history", [])
        if not history:
            raise HTTPException(status_code=400, detail="No completed queries in session to export.")
        query_resp = QueryResponse(**history[-1])

    if format.lower() == "geojson":
        out_file = report_exporter.export_geojson(request.session_id, query_resp)
        return FileResponse(out_file, media_type="application/geo+json", filename=out_file.name)
    else:
        out_file = report_exporter.export_pdf(request.session_id, query_resp)
        return FileResponse(out_file, media_type="application/pdf", filename=out_file.name)

@app.post("/api/maintenance/cleanup")
def cleanup_storage(background_tasks: BackgroundTasks):
    """Purges expired sessions past their sliding TTL."""
    cleaned = session_manager.cleanup_expired_sessions()
    return {"status": "success", "sessions_evicted": cleaned}

from fastapi.staticfiles import StaticFiles
_frontend_dir = settings.BASE_DIR.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

