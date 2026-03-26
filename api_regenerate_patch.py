"""
api_regenerate_patch.py
═══════════════════════
TWO CHANGES to make to api.py. Read carefully — they go in different places.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHANGE 1 of 2  →  Replace _run_pipeline_sync (already exists in api.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Find your existing def _run_pipeline_sync(...) and replace the whole
function with this one. This fixes the auto-detect bias.
"""

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
    #
    # FIX: run_pipeline() never writes contract_type back to the canonical dict
    # so we cannot read it from there. For "auto" we use heuristics on canonical
    # content fields to decide what was actually detected.
    #
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


"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHANGE 2 of 2  →  Paste everything below AFTER download_canonical route
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
In api.py find the last route before  if __name__ == "__main__":

    @app.get("/download/{job_id}/canonical", tags=["Downloads"])
    def download_canonical(...):
        ...        ← end of that function

Paste everything from here to the end of this file right after it.

Also add this one import near the top of api.py with your other imports:
    from pydantic import BaseModel
(pydantic is already installed — FastAPI depends on it.)
"""

from pydantic import BaseModel


class RegenerateRequest(BaseModel):
    overrides: dict
    # Keys are dot-notation canonical paths, values are the replacement strings.
    # Examples:
    #   { "confidentiality.term": "3 years" }
    #   { "parties.client.name": "Contoso India Pvt. Ltd." }
    #   { "commercials.totalValue": "1200000" }


@app.post("/jobs/{job_id}/regenerate", tags=["Pipeline"])
async def regenerate_job(
    job_id: str,
    body: RegenerateRequest,
    _key: str = Security(verify_api_key),
):
    """
    Patch the saved canonical JSON with user-supplied overrides and
    re-run ONLY the PDF generation step.

    No Azure calls are made — extraction is skipped entirely.
    Reads the canonical.json saved during the original run, applies
    the overrides, writes new PDFs to the same output folder, and
    reuses the same job_id so the frontend poll works without change.

    POST body:
        { "overrides": { "canonical.field.path": "corrected_value" } }
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
            job.get("contract_type", "auto"),
        )
    )

    return {
        "job_id":            job_id,
        "status":            "queued",
        "message":           f"Regeneration queued with {len(body.overrides)} override(s). Poll /jobs/{job_id}.",
        "poll_url":          f"/jobs/{job_id}",
        "overrides_applied": list(body.overrides.keys()),
    }


async def _run_regenerate_job(
    job_id: str,
    canonical_path: str,
    overrides: dict,
    contract_type: str,
):
    """Background task: patch canonical → regenerate PDFs only."""
    import asyncio
    JOBS[job_id]["status"] = "processing"
    log.info(f"[Job {job_id}] Regenerating — overrides on: {list(overrides.keys())}")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _regenerate_sync,
            job_id,
            canonical_path,
            overrides,
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


def _regenerate_sync(
    job_id: str,
    canonical_path: str,
    overrides: dict,
    contract_type: str,
) -> dict:
    """
    1. Load saved canonical.json
    2. Patch it with user overrides (dot-notation supported)
    3. Remove resolved conflicts from the conflicts list so the PDF
       appendix reflects the user's corrected values
    4. Save patched canonical back to disk
    5. Call generate_pdf() only — zero Azure calls
    """
    import json, sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from generation.generate_contract_pdf import generate_pdf
    from orchestration.functions.map_to_canonical import set_nested

    with open(canonical_path) as f:
        canonical = json.load(f)

    # Apply user overrides
    for key, value in overrides.items():
        set_nested(canonical, key, value)

    # Remove conflicts that the user has now resolved so the PDF appendix
    # doesn't still flag them as outstanding issues
    resolved_fields = set(overrides.keys())
    canonical["conflicts"] = [
        c for c in canonical.get("conflicts", [])
        if c.get("field") not in resolved_fields
    ]

    # Persist patched canonical
    with open(canonical_path, "w") as f:
        json.dump(canonical, f, indent=2)

    job_output_dir = OUTPUT_DIR / job_id
    outputs = {"canonical": str(canonical_path)}

    # For regeneration: use existing PDFs on disk as the source of truth for
    # what was originally generated (avoids re-running auto-detect heuristics)
    if contract_type in ("nda", "both"):
        generate_nda = True
        generate_sow = contract_type == "both"
    elif contract_type == "sow":
        generate_nda = False
        generate_sow = True
    else:  # auto — whatever was produced first time is still on disk
        generate_nda = (job_output_dir / "generated-nda.pdf").exists()
        generate_sow = (job_output_dir / "generated-sow.pdf").exists()

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
