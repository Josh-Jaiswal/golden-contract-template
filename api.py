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
from fastapi import FastAPI, File, Form, HTTPException, Security, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
# from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

def get_api_key_for_limit(request: Request):
    return request.headers.get("X-API-Key") or request.client.host
limiter = Limiter(key_func=get_api_key_for_limit)
app.state.limiter = limiter

# Allow all origins locally — lock this down before production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request,exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )
# ── API Key auth ──────────────────────────────────────────────────────────────
API_KEY        = os.getenv("CONTRACT_API_KEY", "GoldenEY1479")
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
    import sys, json
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
    with open(canonical_path, "w") as f:
        json.dump(canonical, f, indent=2)

    # Step 3 — Decide which docs to generate
    outputs = {"canonical": str(canonical_path)}

    if contract_type == "both":
        generate_nda = True
        generate_sow = True

    elif contract_type == "nda":
        generate_nda = True
        generate_sow = False

    elif contract_type == "sow":
        generate_nda = False
        generate_sow = True

    else:  # "auto"
        parties        = canonical.get("parties", {})
        scope          = canonical.get("scope", {})
        commercials    = canonical.get("commercials", {})
        confidentiality = canonical.get("confidentiality", {})

        nda_type = str(parties.get("ndaType", "")).lower()
        has_nda_signal = (
            "nda" in nda_type
            or bool(confidentiality.get("term"))
            or bool(confidentiality.get("exceptions"))
            or bool(parties.get("disclosingParty"))
        )
        has_sow_signal = (
            bool(scope.get("deliverables"))
            or bool(scope.get("outOfScope"))
            or bool(commercials.get("totalValue"))
            or bool(commercials.get("milestones"))
            or bool(commercials.get("paymentTerms"))
        )

        generate_nda = has_nda_signal
        generate_sow = has_sow_signal

        if not generate_nda and not generate_sow:
            log.warning(f"[Job {job_id}] Auto-detect: no strong signals found — generating both as fallback")
            generate_nda = True
            generate_sow = True
        else:
            log.info(f"[Job {job_id}] Auto-detect: nda={generate_nda}, sow={generate_sow}")

    # Step 4 — Generate only the decided doc(s)
    if generate_nda:
        nda_path = str(job_output_dir / "generated-nda.pdf")
        generate_pdf(canonical, "nda", nda_path)
        outputs["nda_pdf"] = nda_path
        log.info(f"[Job {job_id}] NDA PDF generated")

    if generate_sow:
        sow_path = str(job_output_dir / "generated-sow.pdf")
        generate_pdf(canonical, "sow", sow_path)
        outputs["sow_pdf"] = sow_path
        log.info(f"[Job {job_id}] SOW PDF generated")

    return outputs

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    """Check API is running."""
    return {
        "status":  "ok",
        "version": "1.0.0",
        "time":    datetime.now(timezone.utc).isoformat(),
    }

@limiter.limit("5/minute")
@app.post("/analyze", tags=["Pipeline"])
async def analyze(
    request: Request,
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
    if contract_type not in ("nda", "sow", "auto", "both"):
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
        outputs = job.get("outputs") or {}
        job["download_urls"] = {
            k: f"{base}/{k.replace('_pdf','')}"
            for k in outputs
            if k.endswith("_pdf")
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

@app.get("/download/{job_id}/canonical", tags=["Downloads"])
def download_canonical(job_id: str, _key: str = Security(verify_api_key)):
    canonical_path = OUTPUT_DIR / job_id / "canonical.json"
    if not canonical_path.exists():
        raise HTTPException(status_code=404, detail="Canonical JSON not found")
    return FileResponse(
        canonical_path,
        media_type="application/json",
        filename=f"{job_id}-canonical.json"
    )


@app.get("/download/{job_id}/source", tags=["Downloads"])
def download_source(job_id: str, _key: str = Security(verify_api_key)):
    """Return the original uploaded file so the frontend can preview it."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    matches = list(UPLOAD_DIR.glob(f"{job_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Source file not found")

    source_path = matches[0]
    ext = source_path.suffix.lower()

    mime_map = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc":  "application/msword",
        ".eml":  "message/rfc822",
        ".mp3":  "audio/mpeg",
        ".wav":  "audio/wav",
        ".m4a":  "audio/mp4",
        ".txt":  "text/plain",
    }
    media_type = mime_map.get(ext, "application/octet-stream")
    original_name = JOBS[job_id].get("file_name", f"source{ext}")

    return FileResponse(
        path=str(source_path),
        media_type=media_type,
        filename=original_name,
    )


# ── Regenerate ────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import List


class RegenerateRequest(BaseModel):
    overrides: dict
    # Keys are field names (e.g. "confidentiality.term"), values are replacement strings.
    dismissed_fields: List[str] = []
    # Fields the user accepted as-is — these are REMOVED from canonical.conflicts
    # so they no longer appear as conflicts after regeneration.


@app.post("/jobs/{job_id}/regenerate", tags=["Pipeline"])
async def regenerate_job(
    job_id: str,
    body: RegenerateRequest,
    _key: str = Security(verify_api_key),
):
    """
    Patch the saved canonical JSON with user-supplied overrides, remove
    dismissed conflicts, and re-run ONLY the PDF generation step.

    No Azure calls are made — extraction is skipped entirely.

    POST body:
        {
          "overrides": { "field_name": "corrected_value" },
          "dismissed_fields": ["field_name_1", "field_name_2"]
        }

    - overrides      — fields where the user picked an alternative or custom value
    - dismissed_fields — fields where the user accepted the chosen value as correct;
                         these are stripped from canonical.conflicts so they won't
                         reappear as conflicts on the next load
    """
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = JOBS[job_id]
    if job["status"] != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Job must be 'complete' to regenerate. Current status: {job['status']}",
        )

    canonical_path = OUTPUT_DIR / job_id / "canonical.json"
    if not canonical_path.exists():
        raise HTTPException(
            status_code=404,
            detail="canonical.json not found — was the original job completed successfully?",
        )

    # Re-queue the same job_id so frontend poll works as-is
    JOBS[job_id]["status"] = "queued"
    JOBS[job_id]["error"]  = None

    import asyncio
    asyncio.create_task(
        _run_regenerate_job(
            job_id,
            str(canonical_path),
            body.overrides,
            body.dismissed_fields,
            job.get("contract_type", "auto"),
        )
    )

    return {
        "job_id":              job_id,
        "status":              "queued",
        "message":             (
            f"Regeneration queued with {len(body.overrides)} override(s) "
            f"and {len(body.dismissed_fields)} dismissed conflict(s). "
            f"Poll /jobs/{job_id}."
        ),
        "poll_url":            f"/jobs/{job_id}",
        "overrides_applied":   list(body.overrides.keys()),
        "conflicts_dismissed": body.dismissed_fields,
    }


async def _run_regenerate_job(
    job_id: str,
    canonical_path: str,
    overrides: dict,
    dismissed_fields: list,
    contract_type: str,
):
    """Background task: patch canonical → remove dismissed conflicts → regenerate PDFs."""
    import asyncio
    JOBS[job_id]["status"] = "processing"
    log.info(
        f"[Job {job_id}] Regenerating — "
        f"overrides: {list(overrides.keys())} | dismissed: {dismissed_fields}"
    )
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _regenerate_sync,
            job_id,
            canonical_path,
            overrides,
            dismissed_fields,
            contract_type,
        )
        JOBS[job_id].update({
            "status":       "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "outputs":      result,
        })
        log.info(f"[Job {job_id}] Regeneration complete")
    except Exception as e:
        log.error(f"[Job {job_id}] Regeneration failed: {e}", exc_info=True)
        JOBS[job_id].update({
            "status":       "failed",
            "error":        str(e),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })


def _set_nested(d: dict, dot_path: str, value):
    """Set a value in a nested dict using dot notation. e.g. 'parties.client.name'"""
    keys = dot_path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def _regenerate_sync(
    job_id: str,
    canonical_path: str,
    overrides: dict,
    dismissed_fields: list,
    contract_type: str,
) -> dict:
    """
    1. Load saved canonical.json
    2. Remove dismissed conflicts from canonical["conflicts"]
    3. Apply field overrides (dot-notation)
    4. Save updated canonical.json
    5. Regenerate PDFs
    """
    import sys, json
    ROOT = Path(__file__).resolve().parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from generation.generate_contract_pdf import generate_pdf

    job_output_dir = OUTPUT_DIR / job_id

    # ── Step 1: Load canonical ────────────────────────────────────────────────
    with open(canonical_path, "r") as f:
        canonical = json.load(f)

    # ── Step 2: Remove dismissed conflicts ───────────────────────────────────
    # The user accepted these fields as correct — strip them from the conflicts
    # array so they don't reappear as unresolved conflicts on the next load.
    if dismissed_fields:
        dismissed_set = set(dismissed_fields)
        original_conflicts = canonical.get("conflicts", [])
        canonical["conflicts"] = [
            c for c in original_conflicts
            if c.get("field", "") not in dismissed_set
        ]
        removed = len(original_conflicts) - len(canonical["conflicts"])
        log.info(f"[Job {job_id}] Removed {removed} dismissed conflict(s) from canonical")

    # ── Step 3: Apply field overrides ────────────────────────────────────────
    # Also remove overridden fields from conflicts — if the user picked an
    # alternative value, that conflict is resolved too.
    if overrides:
        overridden_fields = set(overrides.keys())
        canonical["conflicts"] = [
            c for c in canonical.get("conflicts", [])
            if c.get("field", "") not in overridden_fields
        ]
        for dot_path, value in overrides.items():
            try:
                _set_nested(canonical, dot_path, value)
                log.info(f"[Job {job_id}] Override applied: {dot_path} = {str(value)[:60]}")
            except Exception as e:
                log.warning(f"[Job {job_id}] Could not apply override '{dot_path}': {e}")

    # ── Step 4: Save updated canonical ───────────────────────────────────────
    with open(canonical_path, "w") as f:
        json.dump(canonical, f, indent=2)
    log.info(f"[Job {job_id}] canonical.json updated and saved")

    # ── Step 5: Regenerate PDFs ───────────────────────────────────────────────
    outputs = {"canonical": canonical_path}

    # Determine which docs to regenerate based on contract_type
    if contract_type == "both":
        generate_nda, generate_sow = True, True
    elif contract_type == "nda":
        generate_nda, generate_sow = True, False
    elif contract_type == "sow":
        generate_nda, generate_sow = False, True
    else:  # auto — use same heuristics as original pipeline
        parties         = canonical.get("parties", {})
        scope           = canonical.get("scope", {})
        commercials     = canonical.get("commercials", {})
        confidentiality = canonical.get("confidentiality", {})

        nda_type = str(parties.get("ndaType", "")).lower()
        generate_nda = (
            "nda" in nda_type
            or bool(confidentiality.get("term"))
            or bool(confidentiality.get("exceptions"))
            or bool(parties.get("disclosingParty"))
        )
        generate_sow = (
            bool(scope.get("deliverables"))
            or bool(scope.get("outOfScope"))
            or bool(commercials.get("totalValue"))
            or bool(commercials.get("milestones"))
            or bool(commercials.get("paymentTerms"))
        )
        if not generate_nda and not generate_sow:
            generate_nda = generate_sow = True

    if generate_nda:
        nda_path = str(job_output_dir / "generated-nda.pdf")
        generate_pdf(canonical, "nda", nda_path)
        outputs["nda_pdf"] = nda_path
        log.info(f"[Job {job_id}] NDA PDF regenerated")

    if generate_sow:
        sow_path = str(job_output_dir / "generated-sow.pdf")
        generate_pdf(canonical, "sow", sow_path)
        outputs["sow_pdf"] = sow_path
        log.info(f"[Job {job_id}] SOW PDF regenerated")

    return outputs


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
