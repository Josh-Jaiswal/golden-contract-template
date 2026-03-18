"""
email_handler.py
────────────────
Handles email inputs (.eml, .msg) by:
  1. Parsing the email into clean text (headers + body + thread)
  2. Sending to GPT-4o with a schema-aware extraction prompt
  3. Returning canonical-shaped extraction results

WHY NOT CU?
CU analyzers are trained on structured contract documents.
Emails are unstructured conversation — GPT-4o handles these
much better and extracts the same canonical fields.

Dependencies:
    pip install extract-msg  (for .msg Outlook files)
    Azure OpenAI configured in config/azure_clients.py
"""

import email
import json
import logging
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)

# Path to the extraction prompt template
PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent / "config" / "prompts" / "email_extraction.txt"


def handle_email(
    file_path: str,
    contract_type: Literal["nda", "sow", "auto"] = "auto",
    upload_to_blob: bool = False,  # emails don't need blob staging
) -> list[dict]:
    """
    Extract contract fields from an email thread using GPT-4o.

    Args:
        file_path:      Path to .eml or .msg file.
        contract_type:  Hint for the extraction prompt.
        upload_to_blob: Not used for emails, kept for interface consistency.

    Returns:
        List with a single extraction dict tagged with "_source": "llm_email".
    """
    log.info(f"[Email Handler] Processing: {file_path}")

    # ── Step 1: Parse email to plain text ────────────────────────────────────
    ext = Path(file_path).suffix.lower()
    if ext == ".eml":
        email_text = _parse_eml(file_path)
    elif ext == ".msg":
        email_text = _parse_msg(file_path)
    else:
        raise ValueError(f"Unsupported email format: {ext}")

    log.info(f"[Email Handler] Parsed email ({len(email_text)} chars)")

    # ── Step 2: Extract fields via GPT-4o ────────────────────────────────────
    extracted = _extract_with_llm(email_text, contract_type)
    extracted["_source"] = "llm_email"
    extracted["_originalPath"] = file_path

    return [extracted]


def _parse_eml(file_path: str) -> str:
    """Parse a .eml file into clean text including thread history."""
    with open(file_path, "rb") as f:
        msg = email.message_from_bytes(f.read())

    parts = []

    # Extract headers
    parts.append(f"From: {msg.get('From', '')}")
    parts.append(f"To: {msg.get('To', '')}")
    parts.append(f"Date: {msg.get('Date', '')}")
    parts.append(f"Subject: {msg.get('Subject', '')}")
    parts.append("---")

    # Extract body (prefer plain text over HTML)
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    parts.append(part.get_payload(decode=True).decode("utf-8", errors="replace"))
                except Exception:
                    pass
    else:
        try:
            parts.append(msg.get_payload(decode=True).decode("utf-8", errors="replace"))
        except Exception:
            parts.append(str(msg.get_payload()))

    return "\n".join(parts)


def _parse_msg(file_path: str) -> str:
    """
    Parse an Outlook .msg file into clean text.
    Requires: pip install extract-msg
    """
    try:
        import extract_msg
    except ImportError:
        raise ImportError("Install extract-msg: pip install extract-msg")

    msg = extract_msg.Message(file_path)
    parts = [
        f"From: {msg.sender}",
        f"To: {msg.to}",
        f"Date: {msg.date}",
        f"Subject: {msg.subject}",
        "---",
        msg.body or "",
    ]
    return "\n".join(parts)


def _extract_with_llm(email_text: str, contract_type: str) -> dict:
    """
    Send email text to GPT-4o and extract canonical contract fields.

    The prompt instructs GPT-4o to return JSON matching the
    same field names as the CU analyzer outputs so the mapping
    matrix can treat them identically.

    TODO: Wire up Azure OpenAI client from config/azure_clients.py
    """
    from config.azure_clients import get_openai_client

    prompt = _build_extraction_prompt(email_text, contract_type)

    # TODO: Replace stub with real Azure OpenAI call
    # Example:
    #   client = get_openai_client()
    #   response = client.chat.completions.create(
    #       model="gpt-4o",
    #       messages=[
    #           {"role": "system", "content": SYSTEM_PROMPT},
    #           {"role": "user", "content": prompt},
    #       ],
    #       response_format={"type": "json_object"},
    #       temperature=0,
    #   )
    #   raw_json = response.choices[0].message.content
    #   extracted = json.loads(raw_json)
    #   extracted["_confidence"] = 0.75  # LLM extractions get a fixed confidence score

    log.warning("[Email Handler] Using stub LLM response — wire up Azure OpenAI")
    extracted = {
        "clientName": "",
        "vendorName": "",
        "startDate": "",
        "endDate": "",
        "dealValue": "",
        "contractType": contract_type,
        "_confidence": 0.0,
        "_llmUsed": "gpt-4o",
        "_promptTokens": 0,
    }
    return extracted


def _build_extraction_prompt(email_text: str, contract_type: str) -> str:
    """
    Build the GPT-4o extraction prompt.

    TODO: Load from config/prompts/email_extraction.txt for easy iteration
    without code changes.
    """
    # Inline for now — move to prompt file once stable
    return f"""
You are a contract data extraction specialist. Extract structured contract information from the email thread below.

Contract type hint: {contract_type}

Return ONLY valid JSON with these fields (use null for fields not found):
{{
  "clientName": "string",
  "vendorName": "string",
  "startDate": "YYYY-MM-DD or null",
  "endDate": "YYYY-MM-DD or null",
  "dealValue": "number as string or null",
  "contractType": "NDA | SOW | unknown",
  "confidentialityTerm": "string or null",
  "governingLaw": "string or null",
  "scopeOfWork": "string or null",
  "deliverables": ["list", "of", "items"] or null,
  "paymentTerms": "string or null"
}}

Email thread:
───────────────
{email_text[:8000]}
───────────────

Return only the JSON object, no explanation.
"""
