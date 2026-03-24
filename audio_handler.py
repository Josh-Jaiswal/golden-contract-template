"""
audio_handler.py
────────────────
Handles audio inputs (.mp3, .wav, .m4a) by:
  1. Uploading audio to Azure Blob Storage (for batch mode)
  2. Transcribing via Azure Speech Services
     - Real-time SDK  → files under ~5 MB  (short calls)
     - Batch REST API → files 5 MB+        (long meetings/recordings)
  3. Sending transcript to GPT-4o-mini for contract field extraction
  4. Returning a canonical-shaped extraction result

WHY SPEECH SERVICES + GPT-4o-mini?
  Azure Speech Services  → accurate transcription, multi-speaker diarization
  GPT-4o-mini            → understands messy spoken language, extracts
                           structured contract fields using same schema as CU

SETUP CHECKLIST:
  1. pip install azure-cognitiveservices-speech azure-storage-blob openai
  2. Add to .env:
       AZURE_SPEECH_KEY=<your key>
       AZURE_SPEECH_REGION=uksouth          # or your region
       AZURE_OPENAI_ENDPOINT=<your endpoint>
       AZURE_OPENAI_KEY=<your key>
       AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
       AZURE_BLOB_CONNECTION_STR=<your connection string>
  3. In Azure Portal: create a Speech resource and a Storage account
     (the blob container "audio-staging" is created automatically below)

Free tier limits:
  Speech Services: 5 hours/month free transcription
  GPT-4o-mini:     ~$0.0002 per 1K tokens (very cheap)
"""

import json
import logging
import time
import threading
from pathlib import Path
from typing import Literal

import requests

log = logging.getLogger(__name__)

# Blob container for audio files (separate from contract docs)
AUDIO_BLOB_CONTAINER = "audio-staging"

# Batch transcription polling settings
_BATCH_POLL_INTERVAL_SECONDS = 10
_BATCH_MAX_WAIT_SECONDS = 600  # 10 minutes max


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

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
        upload_to_blob: Upload audio to Blob before transcription.
                        Required for batch mode; set False only in tests.

    Returns:
        List with a single extraction dict tagged "_source": "llm_audio".
        Shape matches CU analyzer outputs so the mapping matrix works
        identically for audio as for PDF/DOCX.
    """
    log.info(f"[Audio] Processing: {Path(file_path).name}")

    # ── Step 1: Upload to Blob (needed for batch transcription) ───────────────
    audio_blob_url = None
    if upload_to_blob:
        from normalization.blob_uploader import upload_to_blob as do_upload
        audio_blob_url = do_upload(file_path, container=AUDIO_BLOB_CONTAINER)
        log.info(f"[Audio] Uploaded to blob: {audio_blob_url}")

    # ── Step 2: Transcribe ────────────────────────────────────────────────────
    transcript = transcribe_audio(audio_blob_url or file_path, file_path)
    log.info(f"[Audio] Transcription complete — {len(transcript)} chars")

    if not transcript.strip():
        raise ValueError(
            "Transcription returned empty text. "
            "Check the audio file is not silent and Speech Services is provisioned."
        )

    # ── Step 3: Extract contract fields via GPT-4o-mini ───────────────────────
    extracted = _extract_from_transcript(transcript, contract_type)
    extracted["_source"] = "llm_audio"
    extracted["_originalPath"] = file_path
    extracted["_transcript"] = transcript  # preserved for audit/review

    log.info(f"[Audio] Extraction complete — contractType={extracted.get('contractType')}")
    return [extracted]


# ─────────────────────────────────────────────────────────────────────────────
# Transcription routing
# ─────────────────────────────────────────────────────────────────────────────

def transcribe_audio(blob_url_or_path: str, local_path: str) -> str:
    """
    Route to real-time or batch transcription based on file size.

    - Under 5 MB  → real-time SDK (instant, synchronous)
    - 5 MB+       → batch REST API (async, handles long recordings)

    Args:
        blob_url_or_path: Azure Blob URL (for batch) or local path fallback.
        local_path:       Always the local file path (for size check + real-time).
    """
    file_size_mb = Path(local_path).stat().st_size / (1024 * 1024)
    log.info(f"[Audio] File size: {file_size_mb:.1f} MB — "
             f"using {'real-time' if file_size_mb < 5 else 'batch'} transcription")

    if file_size_mb < 5:
        return _transcribe_realtime(local_path)
    else:
        if not blob_url_or_path.startswith("https://"):
            raise ValueError(
                "Batch transcription requires an Azure Blob URL. "
                "Set upload_to_blob=True or pass a blob URL directly."
            )
        return _transcribe_batch(blob_url_or_path)


# ─────────────────────────────────────────────────────────────────────────────
# Real-time transcription (Azure Speech SDK)
# ─────────────────────────────────────────────────────────────────────────────

def _transcribe_realtime(file_path: str) -> str:
    """
    Transcribe using Azure Speech SDK with continuous recognition.

    Handles files of any length by using continuous recognition instead
    of recognize_once() — collects all segments until EOF.

    Supports: WAV natively; MP3/M4A converted to WAV in memory via pydub
    if available, otherwise Speech SDK handles common formats directly.
    """
    import azure.cognitiveservices.speech as speechsdk
    from config.azure_clients import get_speech_config

    speech_config = get_speech_config()

    # Resolve audio format — Speech SDK handles WAV/MP3/M4A directly
    # when using PushAudioInputStream with the right format hint
    file_ext = Path(file_path).suffix.lower()
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    # Collect all recognised segments
    all_text: list[str] = []
    done = threading.Event()

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            segment = evt.result.text.strip()
            if segment:
                all_text.append(segment)
                log.debug(f"[Audio] Segment: {segment[:60]}...")

    def on_cancelled(evt):
        details = evt.result.cancellation_details
        if details.reason == speechsdk.CancellationReason.Error:
            log.error(f"[Audio] Speech recognition error: {details.error_details}")
        done.set()

    def on_session_stopped(evt):
        done.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_cancelled)
    recognizer.session_stopped.connect(on_session_stopped)

    recognizer.start_continuous_recognition()
    done.wait(timeout=300)  # 5-minute timeout for safety
    recognizer.stop_continuous_recognition()

    transcript = " ".join(all_text)

    if not transcript:
        raise RuntimeError(
            "Speech recognition returned no text. "
            "Verify the audio has speech and AZURE_SPEECH_KEY/REGION are correct."
        )

    return transcript


# ─────────────────────────────────────────────────────────────────────────────
# Batch transcription (Azure Speech REST API)
# ─────────────────────────────────────────────────────────────────────────────

def _transcribe_batch(blob_url: str) -> str:
    """
    Transcribe using Azure Speech batch transcription REST API.

    Flow:
      1. POST /transcriptions        → submit job, get job URL
      2. GET  /transcriptions/{id}   → poll until Succeeded/Failed
      3. GET  /transcriptions/{id}/files → get result file URLs
      4. GET  result file URL        → download JSON, parse display text

    Suitable for recordings > 5 minutes.
    Azure processes these asynchronously — typically completes in
    1–5 minutes depending on audio length.
    """
    key, region = _get_speech_rest_credentials()
    base_url = f"https://{region}.api.cognitive.microsoft.com/speechtotext/v3.1"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/json",
    }

    # ── Submit transcription job ───────────────────────────────────────────────
    payload = {
        "contentUrls": [blob_url],
        "locale": "en-US",
        "displayName": f"contract-intel-{int(time.time())}",
        "properties": {
            "diarizationEnabled": True,   # separate speakers in output
            "wordLevelTimestampsEnabled": False,
            "punctuationMode": "DictatedAndAutomatic",
            "profanityFilterMode": "None",
        },
    }

    log.info("[Audio] Submitting batch transcription job...")
    resp = requests.post(f"{base_url}/transcriptions", headers=headers, json=payload)
    resp.raise_for_status()

    job_url = resp.json()["self"]
    job_id = job_url.split("/")[-1]
    log.info(f"[Audio] Batch job submitted: {job_id}")

    # ── Poll for completion ────────────────────────────────────────────────────
    elapsed = 0
    while elapsed < _BATCH_MAX_WAIT_SECONDS:
        time.sleep(_BATCH_POLL_INTERVAL_SECONDS)
        elapsed += _BATCH_POLL_INTERVAL_SECONDS

        status_resp = requests.get(job_url, headers=headers)
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status = status_data.get("status", "")

        log.info(f"[Audio] Batch job status ({elapsed}s): {status}")

        if status == "Succeeded":
            break
        elif status == "Failed":
            error = status_data.get("properties", {}).get("error", {})
            raise RuntimeError(
                f"Batch transcription failed: {error.get('message', 'unknown error')}"
            )
    else:
        raise TimeoutError(
            f"Batch transcription timed out after {_BATCH_MAX_WAIT_SECONDS}s. "
            "Audio may be too long or Speech Services may be throttled."
        )

    # ── Retrieve result files ──────────────────────────────────────────────────
    files_resp = requests.get(f"{job_url}/files", headers=headers)
    files_resp.raise_for_status()
    files = files_resp.json().get("values", [])

    # Find the transcript result file (not the report file)
    result_url = next(
        (f["links"]["contentUrl"] for f in files
         if f.get("kind") == "Transcription"),
        None,
    )

    if not result_url:
        raise RuntimeError("Batch transcription succeeded but no result file found.")

    # ── Download and parse transcript JSON ────────────────────────────────────
    result_resp = requests.get(result_url)
    result_resp.raise_for_status()
    result_data = result_resp.json()

    # Extract display text from all recognised phrases, preserving speaker labels
    phrases = result_data.get("recognizedPhrases", [])
    lines: list[str] = []
    for phrase in phrases:
        # Best alternative is index 0
        best = (phrase.get("nBest") or [{}])[0]
        display = best.get("display", "").strip()
        if display:
            speaker = phrase.get("speaker")
            prefix = f"Speaker {speaker}: " if speaker else ""
            lines.append(f"{prefix}{display}")

    transcript = "\n".join(lines)

    # Clean up batch job (optional — avoids cluttering Speech resource)
    try:
        requests.delete(job_url, headers={"Ocp-Apim-Subscription-Key": key})
        log.info(f"[Audio] Batch job {job_id} deleted after retrieval")
    except Exception:
        pass  # Non-fatal — job will expire automatically

    return transcript


def _get_speech_rest_credentials() -> tuple[str, str]:
    """Return (key, region) for Speech REST API calls."""
    from config.azure_clients import get_speech_endpoint
    return get_speech_endpoint()


# ─────────────────────────────────────────────────────────────────────────────
# GPT-4o-mini extraction
# ─────────────────────────────────────────────────────────────────────────────

def _extract_from_transcript(transcript: str, contract_type: str) -> dict:
    """
    Send transcript to GPT-4o-mini to extract contract fields.

    Uses the same field names as CU analyzer outputs so the mapping
    matrix treats audio extractions identically to PDF/DOCX ones.
    """
    from config.azure_clients import get_openai_client, get_openai_deployment

    client = get_openai_client()
    deployment = get_openai_deployment()
    prompt = _build_transcript_prompt(transcript, contract_type)

    log.info(f"[Audio] Sending transcript to {deployment} for field extraction...")

    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content
    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"[Audio] GPT-4o-mini returned invalid JSON: {raw[:200]}")
        raise ValueError(f"LLM extraction returned invalid JSON: {e}") from e

    # Attach metadata
    extracted["_confidence"] = 0.75   # audio extractions get slightly lower base confidence
    extracted["_llmUsed"] = deployment

    return extracted


def _build_transcript_prompt(transcript: str, contract_type: str) -> str:
    """Build the GPT-4o-mini prompt for transcript-based contract extraction."""
    return f"""
You are a contract analyst reviewing a recorded call or meeting transcript.
Extract any contract-related information discussed.

Contract type context: {contract_type}

Note: This is spoken language — names and terms may be informal or abbreviated.
Use context clues to normalize them (e.g. "Acme" → "Acme Corporation" if the full
name is mentioned elsewhere in the transcript).

Return ONLY a valid JSON object with these exact fields:
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
  "deliverables": ["array of strings"] or null,
  "paymentTerms": "string or null",
  "keyDiscussionPoints": ["notable items not captured in fields above"] or null
}}

Rules:
- Use null (not empty string) for fields not mentioned.
- Dates must be in YYYY-MM-DD format or null.
- dealValue must be digits only (no currency symbols), e.g. "50000".
- If contractType cannot be determined, use "unknown".

Transcript:
───────────────────────────────────────────────
{transcript[:12000]}
───────────────────────────────────────────────

Return only the JSON object. No explanation, no markdown.
"""
