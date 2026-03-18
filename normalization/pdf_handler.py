"""
pdf_handler.py
──────────────
Handles PDF inputs through the Azure Content Understanding pipeline.

Flow:
  1. Upload PDF to Azure Blob Storage (staging container)
  2. Detect contract type (NDA / SOW / deal-intake) if not specified
  3. Run deal-intake analyzer (always — extracts parties, dates, metadata)
  4. Run NDA or SOW analyzer based on contract type
  5. Return list of raw extraction dicts for mapping

Your 3 CU analyzers are already built — this file just calls them.
"""

import logging
from typing import Literal

from config.azure_clients import get_blob_client, get_cu_client
from normalization.blob_uploader import upload_to_blob

log = logging.getLogger(__name__)

# ── CU Analyzer IDs ───────────────────────────────────────────────────────────
# TODO: Replace these with your actual CU analyzer IDs from Azure portal
CU_ANALYZER_IDS = {
    "deal_intake": "YOUR_DEAL_INTAKE_ANALYZER_ID",
    "nda":         "YOUR_NDA_ANALYZER_ID",
    "sow":         "YOUR_SOW_ANALYZER_ID",
}

# Azure Blob container used for staging files before CU analysis
BLOB_STAGING_CONTAINER = "contract-staging"


def handle_pdf(
    file_path: str,
    contract_type: Literal["nda", "sow", "auto"] = "auto",
    upload_to_blob: bool = True,
) -> list[dict]:
    """
    Process a PDF through the CU analyzer pipeline.

    Args:
        file_path:      Local path to the PDF file.
        contract_type:  "nda" | "sow" | "auto" (detect from content).
        upload_to_blob: Upload to Blob Storage before CU processing.

    Returns:
        List of raw extraction dicts, one per analyzer run.
        Each dict has a "_source" key indicating which analyzer produced it.
    """
    log.info(f"[PDF Handler] Processing: {file_path}")

    # ── Step 1: Upload to Blob Storage ────────────────────────────────────────
    if upload_to_blob:
        blob_url = upload_to_blob(file_path, container=BLOB_STAGING_CONTAINER)
        log.info(f"[PDF Handler] Uploaded to blob: {blob_url}")
    else:
        # TODO: If not uploading, CU still needs a URL — use local file URL or SAS token
        blob_url = file_path

    # ── Step 2: Always run deal-intake analyzer ───────────────────────────────
    results = []
    deal_intake_result = run_cu_analyzer(
        analyzer_id=CU_ANALYZER_IDS["deal_intake"],
        document_url=blob_url,
        source_label="deal_intake",
    )
    results.append(deal_intake_result)

    # ── Step 3: Detect contract type if auto ─────────────────────────────────
    if contract_type == "auto":
        contract_type = _detect_contract_type(deal_intake_result)
        log.info(f"[PDF Handler] Auto-detected contract type: {contract_type}")

    # ── Step 4: Run domain-specific analyzer (NDA or SOW) ────────────────────
    if contract_type in ("nda", "sow"):
        domain_result = run_cu_analyzer(
            analyzer_id=CU_ANALYZER_IDS[contract_type],
            document_url=blob_url,
            source_label=contract_type,
        )
        results.append(domain_result)
    else:
        log.warning(f"[PDF Handler] Could not determine contract type — skipping domain analyzer")

    return results


def run_cu_analyzer(analyzer_id: str, document_url: str, source_label: str) -> dict:
    """
    Call a single Azure Content Understanding analyzer.

    Args:
        analyzer_id:   CU analyzer ID (from Azure portal).
        document_url:  Blob Storage URL (with SAS token) or public URL.
        source_label:  Label for this result ("deal_intake", "nda", "sow").

    Returns:
        Raw extraction dict with "_source" and "_confidence" keys added.

    TODO:
        - Implement actual CU API call using azure-ai-documentintelligence SDK
          or direct REST call to your CU endpoint
        - Handle async polling (CU jobs are async — submit → poll → retrieve)
        - Parse CU response format into flat field dict
    """
    cu_client = get_cu_client()

    # TODO: Replace this block with actual CU SDK call
    # Example structure (adjust to your CU SDK version):
    #
    #   poller = cu_client.begin_analyze_document(
    #       model_id=analyzer_id,
    #       analyze_request={"url": document_url},
    #   )
    #   result = poller.result()
    #   fields = result.documents[0].fields
    #   extracted = {k: v.content for k, v in fields.items()}
    #
    # For now, return a stub so the rest of the pipeline can be tested:
    log.warning(f"[CU] Stub response for analyzer '{analyzer_id}' — replace with real API call")

    extracted = _stub_extraction(source_label)
    extracted["_source"] = source_label
    extracted["_confidence"] = 0.0   # TODO: pull from CU result confidence scores
    extracted["_analyzerUsed"] = analyzer_id
    extracted["_documentUrl"] = document_url

    return extracted


def _detect_contract_type(deal_intake_result: dict) -> Literal["nda", "sow", "unknown"]:
    """
    Infer contract type from deal-intake analyzer output.

    TODO: Implement proper detection logic. Options:
    - Check a "contractType" field if your deal-intake analyzer extracts it
    - Keyword scan on extracted text
    - Use GPT-4o to classify
    """
    # Placeholder: check if deal_intake extracted a contractType field
    contract_type = deal_intake_result.get("contractType", "").lower()
    if "nda" in contract_type or "confidential" in contract_type:
        return "nda"
    if "sow" in contract_type or "statement of work" in contract_type or "services" in contract_type:
        return "sow"
    return "unknown"


def _stub_extraction(source_label: str) -> dict:
    """
    Placeholder extraction results for testing pipeline flow
    before real CU API calls are wired up.
    Remove this once real CU calls are implemented.
    """
    stubs = {
        "deal_intake": {
            "clientName": "Acme Corp",
            "vendorName": "TechVendor Ltd",
            "startDate": "2025-01-01",
            "endDate": "2026-01-01",
            "dealValue": "500000",
            "contractType": "NDA",
        },
        "nda": {
            "confidentialityTerm": "2 years",
            "governingLaw": "England and Wales",
            "obligations": ["maintain confidentiality", "limit disclosure"],
            "exceptions": ["publicly known information", "required by law"],
        },
        "sow": {
            "scopeOfWork": "Software development and integration services",
            "deliverables": ["API", "Documentation", "Test Suite"],
            "milestones": ["M1: Design", "M2: Build", "M3: Deploy"],
            "paymentTerms": "Net 30",
        },
    }
    return stubs.get(source_label, {})
