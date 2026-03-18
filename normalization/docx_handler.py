"""
docx_handler.py
───────────────
Handles DOCX/DOC inputs by converting them to PDF first,
then routing through the standard PDF → CU analyzer pipeline.

This is the cleanest approach since your CU analyzers are trained on PDFs.
The conversion preserves layout and formatting so CU extraction quality
remains high.

Dependencies:
    pip install python-docx reportlab pypandoc
    + LibreOffice installed on the machine (for best quality conversion)

Conversion strategy (in order of preference):
    1. LibreOffice (best quality, preserves formatting)
    2. pypandoc (good quality, pure Python)
    3. python-docx → reportlab (fallback, basic formatting only)
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)


def handle_docx(
    file_path: str,
    contract_type: Literal["nda", "sow", "auto"] = "auto",
    upload_to_blob: bool = True,
) -> list[dict]:
    """
    Convert DOCX to PDF, then process through the PDF handler.

    Args:
        file_path:      Local path to the .docx or .doc file.
        contract_type:  Passed through to the PDF handler.
        upload_to_blob: Passed through to the PDF handler.

    Returns:
        List of raw extraction dicts (same format as pdf_handler).
    """
    log.info(f"[DOCX Handler] Converting: {file_path}")

    pdf_path = convert_docx_to_pdf(file_path)
    log.info(f"[DOCX Handler] Converted to PDF: {pdf_path}")

    # Route through the standard PDF pipeline
    from normalization.pdf_handler import handle_pdf
    results = handle_pdf(
        file_path=pdf_path,
        contract_type=contract_type,
        upload_to_blob=upload_to_blob,
    )

    # Tag results so we know they came from a DOCX source
    for r in results:
        r["_originalFormat"] = "docx"
        r["_originalPath"] = file_path

    return results


def convert_docx_to_pdf(docx_path: str) -> str:
    """
    Convert a DOCX file to PDF using the best available method.

    Returns:
        Path to the generated PDF file (in system temp directory).

    Raises:
        RuntimeError if conversion fails with all methods.
    """
    input_path = Path(docx_path)
    output_pdf = Path(tempfile.mkdtemp()) / f"{input_path.stem}.pdf"

    # Try methods in order of preference
    converters = [
        _convert_with_libreoffice,
        _convert_with_pypandoc,
        _convert_with_docx2pdf,
    ]

    for converter in converters:
        try:
            result = converter(str(input_path), str(output_pdf))
            if Path(result).exists():
                log.info(f"[DOCX Handler] Conversion succeeded with {converter.__name__}")
                return result
        except Exception as e:
            log.warning(f"[DOCX Handler] {converter.__name__} failed: {e} — trying next")

    raise RuntimeError(f"All DOCX→PDF conversion methods failed for: {docx_path}")


def _convert_with_libreoffice(input_path: str, output_pdf: str) -> str:
    """
    Convert using LibreOffice headless (best quality).
    Requires LibreOffice installed: apt install libreoffice
    """
    output_dir = str(Path(output_pdf).parent)
    subprocess.run(
        [
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", output_dir, input_path,
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    # LibreOffice names output as <input_stem>.pdf in the output dir
    return str(Path(output_dir) / f"{Path(input_path).stem}.pdf")


def _convert_with_pypandoc(input_path: str, output_pdf: str) -> str:
    """
    Convert using pypandoc (requires pandoc + LaTeX installed).
    pip install pypandoc
    """
    import pypandoc
    pypandoc.convert_file(input_path, "pdf", outputfile=output_pdf)
    return output_pdf


def _convert_with_docx2pdf(input_path: str, output_pdf: str) -> str:
    """
    Convert using docx2pdf (works well on Windows/Mac with Word installed,
    limited on Linux).
    pip install docx2pdf
    """
    from docx2pdf import convert
    convert(input_path, output_pdf)
    return output_pdf
