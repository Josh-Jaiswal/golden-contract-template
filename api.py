"""
api.py
──────
FastAPI endpoint for the Contract Intelligence Pipeline.

Accepts file uploads, runs the full pipeline asynchronously,
and returns generated NDA and SOW PDFs for download.

Usage (local):
    pip install fastapi uvicorn python-multipart
    python api.py

Then open: http://localhost:8000/docs  (interactive API docs)

Endpoints:
    POST /analyze          — upload file, get job_id back
    GET  /jobs/{job_id}    — check status, get download URLs when ready
    GET  /download/{job_id}/nda  — download NDA PDF
    GET  /download/{job_id}/sow  — download SOW PDF
    GET  /health           — health check
"""

import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Security, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security.api_key import APIKeyHeader

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger("contract-api")

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Contract Intelligence Platform",
    description=(
        "Transforms unstructured contract documents into standardised "
        "NDA and SOW PDFs using Azure Content Understanding."
    ),
    version="1.0.0",
)

# Allow all origins locally — lock this down before production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Key auth ──────────────────────────────────────────────────────────────
API_KEY        = os.getenv("CONTRACT_API_KEY", "dev-key-change-in-production")
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


# ── Job storage (in-memory for local, swap for Redis/DB in production) ────────
# Structure: { job_id: { status, created_at, file_name, error, outputs } }
JOBS: dict = {}

# Directories
UPLOAD_DIR = Path("api_uploads")
OUTPUT_DIR = Path("api_outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Supported file types
SUPPORTED_TYPES = {
    "application/pdf":                          ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword":                       ".doc",
    "message/rfc822":                           ".eml",
    "audio/mpeg":                               ".mp3",
    "audio/wav":                                ".wav",
    "audio/x-wav":                              ".wav",
    "audio/mp4":                                ".m4a",
}


# ── Background pipeline runner ────────────────────────────────────────────────
async def run_pipeline_job(job_id: str, file_path: str, contract_type: str):
    """
    Run the full pipeline in the background.
    Updates JOBS[job_id] with status and output paths.
    """
    import asyncio

    JOBS[job_id]["status"] = "processing"
    log.info(f"[Job {job_id}] Pipeline starting — file={Path(file_path).name}")

    try:
        # Run pipeline in thread pool so it doesn't block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _run_pipeline_sync,
            job_id,
            file_path,
            contract_type,
        )
        JOBS[job_id].update({
            "status":     "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "outputs":    result,
        })
        log.info(f"[Job {job_id}] Complete")

    except Exception as e:
        log.error(f"[Job {job_id}] Failed: {e}", exc_info=True)
        JOBS[job_id].update({
            "status": "failed",
            "error":  str(e),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })


def _run_pipeline_sync(job_id: str, file_path: str, contract_type: str) -> dict:
    """
    Synchronous pipeline execution (runs in thread pool).
    Returns dict of output file paths.
    """
    import sys
    # Ensure project root is on path
    ROOT = Path(__file__).resolve().parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from orchestration.functions.run_pipeline import run_pipeline
    from generation.generate_contract_pdf import generate_pdf

    job_output_dir = OUTPUT_DIR / job_id
    job_output_dir.mkdir(exist_ok=True)

    # Step 1 — Run extraction pipeline
    canonical = run_pipeline(
        input_path=file_path,
        contract_type=contract_type,
        upload_to_blob=True,
    )

    # Step 2 — Save canonical JSON
    canonical_path = job_output_dir / "canonical.json"
    import json
    with open(canonical_path, "w") as f:
        json.dump(canonical, f, indent=2)

    # Step 3 — Generate NDA PDF
    nda_path = str(job_output_dir / "generated-nda.pdf")
    generate_pdf(canonical, "nda", nda_path)

    # Step 4 — Generate SOW PDF
    sow_path = str(job_output_dir / "generated-sow.pdf")
    generate_pdf(canonical, "sow", sow_path)

    return {
        "canonical": str(canonical_path),
        "nda_pdf":   nda_path,
        "sow_pdf":   sow_path,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    """Check API is running."""
    return {
        "status":  "ok",
        "version": "1.0.0",
        "time":    datetime.now(timezone.utc).isoformat(),
    }


@app.post("/analyze", tags=["Pipeline"])
async def analyze(
    file:          UploadFile = File(..., description="Contract document to process"),
    contract_type: str        = Form("auto", description="nda | sow | auto"),
    _key:          str        = Security(verify_api_key),
):
    """
    Upload a contract document and start the extraction pipeline.

    Returns a job_id. Poll GET /jobs/{job_id} to check status.
    When status = 'complete', download URLs will be included.

    Supported formats: PDF, DOCX, EML, MP3, WAV, M4A
    """
    # Validate file type
    content_type = file.content_type or ""
    file_ext = Path(file.filename or "").suffix.lower()

    allowed_extensions = {".pdf", ".docx", ".doc", ".eml", ".mp3", ".wav", ".m4a"}
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file_ext}. "
                   f"Allowed: {sorted(allowed_extensions)}"
        )

    # Validate contract_type
    if contract_type not in ("nda", "sow", "auto"):
        raise HTTPException(
            status_code=422,
            detail="contract_type must be 'nda', 'sow', or 'auto'"
        )

    # Save uploaded file
    job_id    = str(uuid.uuid4())
    safe_name = f"{job_id}{file_ext}"
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    log.info(
        f"[Job {job_id}] File received — "
        f"name={file.filename}, size={file_path.stat().st_size} bytes"
    )

    # Register job
    JOBS[job_id] = {
        "job_id":       job_id,
        "status":       "queued",
        "created_at":   datetime.now(timezone.utc).isoformat(),
        "file_name":    file.filename,
        "contract_type": contract_type,
        "outputs":      None,
        "error":        None,
    }

    # Start pipeline in background
    import asyncio
    asyncio.create_task(
        run_pipeline_job(job_id, str(file_path), contract_type)
    )

    return {
        "job_id":      job_id,
        "status":      "queued",
        "message":     "Pipeline started. Poll /jobs/{job_id} for status.",
        "poll_url":    f"/jobs/{job_id}",
    }


@app.get("/jobs/{job_id}", tags=["Pipeline"])
def get_job(
    job_id: str,
    _key:   str = Security(verify_api_key),
):
    """
    Get the status and results of a pipeline job.

    Status values:
    - queued      — waiting to start
    - processing  — pipeline running
    - complete    — finished, download URLs available
    - failed      — error occurred, see 'error' field
    """
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = JOBS[job_id].copy()

    # Add download URLs if complete
    if job["status"] == "complete":
        base = f"/download/{job_id}"
        job["download_urls"] = {
            "nda_pdf": f"{base}/nda",
            "sow_pdf": f"{base}/sow",
        }

    return job


@app.get("/download/{job_id}/nda", tags=["Downloads"])
def download_nda(
    job_id: str,
    _key:   str = Security(verify_api_key),
):
    """Download the generated NDA PDF for a completed job."""
    _validate_download(job_id)
    pdf_path = OUTPUT_DIR / job_id / "generated-nda.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="NDA PDF not found")

    filename = _safe_filename(job_id, "nda")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )


@app.get("/download/{job_id}/sow", tags=["Downloads"])
def download_sow(
    job_id: str,
    _key:   str = Security(verify_api_key),
):
    """Download the generated SOW PDF for a completed job."""
    _validate_download(job_id)
    pdf_path = OUTPUT_DIR / job_id / "generated-sow.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="SOW PDF not found")

    filename = _safe_filename(job_id, "sow")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )


@app.get("/jobs", tags=["System"])
def list_jobs(_key: str = Security(verify_api_key)):
    """List all jobs and their current status."""
    return {
        "total": len(JOBS),
        "jobs": [
            {
                "job_id":       j["job_id"],
                "status":       j["status"],
                "file_name":    j["file_name"],
                "contract_type": j["contract_type"],
                "created_at":   j["created_at"],
            }
            for j in JOBS.values()
        ],
    }


@app.delete("/jobs/{job_id}", tags=["System"])
def delete_job(
    job_id: str,
    _key:   str = Security(verify_api_key),
):
    """Delete a job and its associated files."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Clean up files
    job_output_dir = OUTPUT_DIR / job_id
    if job_output_dir.exists():
        shutil.rmtree(job_output_dir)

    upload_file = next(UPLOAD_DIR.glob(f"{job_id}.*"), None)
    if upload_file:
        upload_file.unlink(missing_ok=True)

    del JOBS[job_id]
    return {"message": f"Job {job_id} deleted"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _validate_download(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = JOBS[job_id]
    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="Job still processing")
    if job["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'unknown error')}"
        )
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job status: {job['status']}")


def _safe_filename(job_id: str, doc_type: str) -> str:
    """Generate a clean download filename from job metadata."""
    job = JOBS.get(job_id, {})
    original = Path(job.get("file_name", "contract")).stem
    # Sanitise
    safe = "".join(c for c in original if c.isalnum() or c in "-_ ")
    safe = safe.strip()[:40] or "contract"
    return f"{safe}-{doc_type}.pdf"


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    log.info(f"Starting Contract Intelligence API on port {port}")
    log.info(f"API docs available at http://localhost:{port}/docs")
    log.info(
        f"API key: {'[SET]' if os.getenv('CONTRACT_API_KEY') else '[using default dev key]'}"
    )
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True,     # auto-reload on code changes during development
        log_level="info",
    )
