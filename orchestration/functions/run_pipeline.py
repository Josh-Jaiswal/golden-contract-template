"""
run_pipeline.py
───────────────
ENTRY POINT for the full contract processing pipeline.

Accepts any supported input file, routes it to the correct
modality handler, runs the appropriate CU analyzer(s) or
LLM extractor, maps to canonical schema, merges conflicts,
and returns a validated contract package.

Usage:
    python run_pipeline.py --input path/to/file.pdf --type nda
    python run_pipeline.py --input path/to/email.eml
    python run_pipeline.py --input path/to/call.mp3
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Literal

from orchestration.functions.map_to_canonical import map_to_canonical
from orchestration.functions.merge_engine import merge_results
from normalization.pdf_handler import handle_pdf
from normalization.docx_handler import handle_docx
from normalization.email_handler import handle_email
from normalization.audio_handler import handle_audio
from validators.schema_validator import validate_canonical_package

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Supported input types and their handlers
MODALITY_ROUTER = {
    ".pdf":  handle_pdf,
    ".docx": handle_docx,
    ".doc":  handle_docx,
    ".eml":  handle_email,
    ".msg":  handle_email,
    ".mp3":  handle_audio,
    ".wav":  handle_audio,
    ".m4a":  handle_audio,
}

ContractType = Literal["nda", "sow", "auto"]


def run_pipeline(
    input_path: str,
    contract_type: ContractType = "auto",
    upload_to_blob: bool = True,
) -> dict:
    """
    Main pipeline entry point.

    Args:
        input_path:     Local path to the input file.
        contract_type:  "nda" | "sow" | "auto" (auto-detected from content).
        upload_to_blob: Whether to stage file in Azure Blob before processing.

    Returns:
        A validated canonical contract package (dict matching schema).
    """
    path = Path(input_path)
    ext = path.suffix.lower()

    if ext not in MODALITY_ROUTER:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(MODALITY_ROUTER)}")

    log.info(f"[Pipeline] Starting — file={path.name}, type={contract_type}")

    # ── Step 1: Route to modality handler ────────────────────────────────────
    # Each handler returns a list of raw extracted dicts (one per analyzer run)
    handler = MODALITY_ROUTER[ext]
    raw_results: list[dict] = handler(
        file_path=str(path),
        contract_type=contract_type,
        upload_to_blob=upload_to_blob,
    )
    log.info(f"[Pipeline] Extraction complete — {len(raw_results)} result(s) from handler")

    # ── Step 2: Map each result to canonical schema fields ───────────────────
    canonical_candidates: list[dict] = []
    for result in raw_results:
        mapped = map_to_canonical(result)
        canonical_candidates.append(mapped)

    # ── Step 3: Merge + apply precedence rules ────────────────────────────────
    merged_package = merge_results(canonical_candidates)
    log.info("[Pipeline] Merge complete")

    # ── Step 4: Validate against canonical schema ─────────────────────────────
    is_valid, errors = validate_canonical_package(merged_package)
    if not is_valid:
        log.warning(f"[Pipeline] Schema validation warnings: {errors}")
        merged_package["_validationErrors"] = errors
    else:
        log.info("[Pipeline] Schema validation passed")

    return merged_package


# ── CLI entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contract Processing Pipeline")
    parser.add_argument("--input", required=True, help="Path to input file")
    parser.add_argument("--type", default="auto", choices=["nda", "sow", "auto"])
    parser.add_argument("--no-blob", action="store_true", help="Skip Blob Storage upload")
    args = parser.parse_args()

    result = run_pipeline(
        input_path=args.input,
        contract_type=args.type,
        upload_to_blob=not args.no_blob,
    )
    print(json.dumps(result, indent=2))
