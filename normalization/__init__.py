"""
normalization/__init__.py
─────────────────────────
Routes incoming files to the correct normalizer based on file extension.

Normalizers return a list of extraction dicts that the orchestration
layer feeds into the mapping matrix. All normalizers produce the same
shape so the rest of the pipeline doesn't care about the input modality.

Supported input types:
    .pdf            → pdf_handler  → Azure CU analysis
    .docx / .doc    → docx_handler → Azure CU analysis
    .eml            → email_handler → Azure CU / text extraction
    .mp3 / .wav / .m4a → audio_handler → Azure Speech + GPT-4o-mini
"""

import logging
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}
DOCX_EXTENSIONS  = {".docx", ".doc"}
PDF_EXTENSIONS   = {".pdf"}
EMAIL_EXTENSIONS = {".eml"}


def normalize(
    file_path: str,
    contract_type: Literal["nda", "sow", "auto"] = "auto",
    upload_to_blob: bool = True,
) -> list[dict]:
    """
    Normalize any supported input file into a list of extraction dicts.

    Args:
        file_path:      Absolute or relative path to the input file.
        contract_type:  Pipeline hint — passed through to analyzers.
        upload_to_blob: Whether to upload to Azure Blob (required for
                        audio batch transcription and CU analysis).

    Returns:
        List of extraction dicts. Most inputs return a single dict;
        multi-document inputs (e.g. email with attachments) may return
        several — the merge engine handles collapsing them.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(file_path).suffix.lower()
    log.info(f"[Normalizer] Routing {ext} file → appropriate handler")

    if ext in AUDIO_EXTENSIONS:
        from normalization.audio_handler import handle_audio
        return handle_audio(
            file_path=file_path,
            contract_type=contract_type,
            upload_to_blob=upload_to_blob,
        )

    elif ext in PDF_EXTENSIONS:
        from normalization.pdf_handler import handle_pdf
        return handle_pdf(
            file_path=file_path,
            contract_type=contract_type,
            upload_to_blob=upload_to_blob,
        )

    elif ext in DOCX_EXTENSIONS:
        from normalization.docx_handler import handle_docx
        return handle_docx(
            file_path=file_path,
            contract_type=contract_type,
            upload_to_blob=upload_to_blob,
        )

    elif ext in EMAIL_EXTENSIONS:
        from normalization.email_handler import handle_email
        return handle_email(
            file_path=file_path,
            contract_type=contract_type,
            upload_to_blob=upload_to_blob,
        )

    else:
        supported = sorted(
            AUDIO_EXTENSIONS | PDF_EXTENSIONS | DOCX_EXTENSIONS | EMAIL_EXTENSIONS
        )
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported extensions: {supported}"
        )
