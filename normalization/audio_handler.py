"""
audio_handler.py
────────────────
Handles audio inputs (.mp3, .wav, .m4a) by:
  1. Uploading audio to Azure Blob Storage
  2. Transcribing via Azure Speech Services (batch transcription)
  3. Sending transcript to GPT-4o for contract field extraction
  4. Returning canonical-shaped extraction results

WHY SPEECH SERVICES + GPT-4o?
Azure Speech Services → accurate transcription (supports multiple speakers)
GPT-4o → understands messy spoken language, extracts structured contract fields

You'll need to enable Azure Speech Services in your Azure subscription.
Free tier: 5 hours/month | Standard: pay-per-minute

Dependencies:
    pip install azure-cognitiveservices-speech azure-storage-blob
"""

import json
import logging
import time
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)

# Blob container for audio files (separate from contract docs)
AUDIO_BLOB_CONTAINER = "audio-staging"


def handle_audio(
    file_path: str,
    contract_type: Literal["nda", "sow", "auto"] = "auto",
    upload_to_blob: bool = True,
) -> list[dict]:
    """
    Transcribe audio and extract contract fields.

    Args:
        file_path:      Local path to audio file (.mp3, .wav, .m4a).
        contract_type:  Hint for LLM extraction prompt.
        upload_to_blob: Upload audio to Blob before transcription (required
                        for Azure Speech batch transcription).

    Returns:
        List with a single extraction dict tagged "_source": "llm_audio".
    """
    log.info(f"[Audio Handler] Processing: {file_path}")

    # ── Step 1: Upload audio to Blob Storage ──────────────────────────────────
    from normalization.blob_uploader import upload_to_blob as do_upload
    audio_blob_url = do_upload(file_path, container=AUDIO_BLOB_CONTAINER)
    log.info(f"[Audio Handler] Audio uploaded: {audio_blob_url}")

    # ── Step 2: Transcribe audio ──────────────────────────────────────────────
    transcript = transcribe_audio(audio_blob_url, file_path)
    log.info(f"[Audio Handler] Transcription complete ({len(transcript)} chars)")

    # ── Step 3: Extract contract fields via GPT-4o ────────────────────────────
    extracted = _extract_from_transcript(transcript, contract_type)
    extracted["_source"] = "llm_audio"
    extracted["_originalPath"] = file_path
    extracted["_transcript"] = transcript  # preserve for audit/review

    return [extracted]


def transcribe_audio(blob_url: str, local_path: str) -> str:
    """
    Transcribe audio file using Azure Speech Services.

    Two modes:
    - Real-time SDK: good for files < 60 seconds
    - Batch transcription: better for longer recordings (async)

    TODO: Implement one of the two options below based on your use case.

    Args:
        blob_url:   Azure Blob URL with SAS token (needed for batch mode).
        local_path: Local file path (used for real-time SDK mode).

    Returns:
        Full transcript as a string.
    """
    # Choose transcription mode based on file size
    file_size_mb = Path(local_path).stat().st_size / (1024 * 1024)

    if file_size_mb < 5:  # ~30 mins audio ≈ ~5MB
        return _transcribe_realtime(local_path)
    else:
        return _transcribe_batch(blob_url)


def _transcribe_realtime(file_path: str) -> str:
    """
    Transcribe using Azure Speech SDK (synchronous, good for short files).

    TODO: Implement this using azure-cognitiveservices-speech SDK.

    Example:
        import azure.cognitiveservices.speech as speechsdk
        from config.azure_clients import get_speech_config

        speech_config = get_speech_config()
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        result = recognizer.recognize_once_async().get()
        return result.text

    For longer files, use continuous recognition with a loop.
    See: https://learn.microsoft.com/azure/ai-services/speech-service/
    """
    log.warning("[Audio Handler] Real-time transcription not yet implemented — using stub")
    return _stub_transcript()


def _transcribe_batch(blob_url: str) -> str:
    """
    Transcribe using Azure Speech batch transcription API (async, for long files).
    Submits a job, polls until complete, retrieves result.

    TODO: Implement using Azure Speech REST API (batch transcription).

    Batch transcription flow:
        1. POST /speechtotext/v3.1/transcriptions → get job ID
        2. GET /speechtotext/v3.1/transcriptions/{id} → poll status
        3. GET transcription files URL → download transcript JSON
        4. Parse JSON → extract "display" text per segment

    See: https://learn.microsoft.com/azure/ai-services/speech-service/batch-transcription
    """
    log.warning("[Audio Handler] Batch transcription not yet implemented — using stub")
    return _stub_transcript()


def _extract_from_transcript(transcript: str, contract_type: str) -> dict:
    """
    Send transcript to GPT-4o to extract contract fields.

    Uses same field names as CU analyzer outputs so the mapping
    matrix treats them identically.

    TODO: Wire up Azure OpenAI client.
    """
    from config.azure_clients import get_openai_client

    prompt = _build_transcript_prompt(transcript, contract_type)

    # TODO: Replace stub with actual Azure OpenAI call
    # client = get_openai_client()
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": prompt}],
    #     response_format={"type": "json_object"},
    #     temperature=0,
    # )
    # return json.loads(response.choices[0].message.content)

    log.warning("[Audio Handler] Using stub LLM extraction — wire up Azure OpenAI")
    return {
        "clientName": "",
        "vendorName": "",
        "startDate": "",
        "endDate": "",
        "dealValue": "",
        "contractType": contract_type,
        "_confidence": 0.6,  # audio extractions get lower base confidence
        "_llmUsed": "gpt-4o",
    }


def _build_transcript_prompt(transcript: str, contract_type: str) -> str:
    """Build GPT-4o prompt for transcript extraction."""
    return f"""
You are a contract analyst reviewing a recorded call or meeting transcript.
Extract any contract-related information discussed.

Contract type context: {contract_type}

Note: This is spoken language — names and terms may be informal or abbreviated.
Use context clues to normalize them (e.g., "Acme" → "Acme Corporation" if full name mentioned elsewhere).

Return ONLY valid JSON:
{{
  "clientName": "string or null",
  "vendorName": "string or null",
  "startDate": "YYYY-MM-DD or null",
  "endDate": "YYYY-MM-DD or null",
  "dealValue": "number as string or null",
  "contractType": "NDA | SOW | unknown",
  "confidentialityTerm": "string or null",
  "governingLaw": "string or null",
  "scopeOfWork": "string or null",
  "deliverables": ["array"] or null,
  "paymentTerms": "string or null",
  "keyDiscussionPoints": ["notable items not in above fields"] or null
}}

Transcript:
───────────────
{transcript[:12000]}
───────────────

Return only the JSON object.
"""


def _stub_transcript() -> str:
    """Placeholder transcript for pipeline testing."""
    return """
    Speaker 1: So we're aligned on the NDA terms, the confidentiality period is two years.
    Speaker 2: Yes, and Acme Corp is the disclosing party, TechVendor is receiving.
    Speaker 1: Governing law will be England and Wales.
    Speaker 2: Agreed. The effective date will be first of January 2025.
    """
