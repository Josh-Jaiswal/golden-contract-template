"""
azure_clients.py
─────────────────
Centralised Azure service client factory.

All credentials come from environment variables — never hardcoded.
Copy .env.example to .env and fill in your values.

Required env vars:
    AZURE_CU_ENDPOINT          Content Understanding endpoint URL
    AZURE_CU_KEY               Content Understanding API key
    AZURE_BLOB_CONNECTION_STR  Storage account connection string
    AZURE_OPENAI_ENDPOINT      Azure OpenAI endpoint URL
    AZURE_OPENAI_KEY           Azure OpenAI API key
    AZURE_OPENAI_DEPLOYMENT    GPT-4o deployment name (e.g. "gpt-4o-mini")
    AZURE_SPEECH_KEY           Speech Services subscription key
    AZURE_SPEECH_REGION        Speech Services region (e.g. "uksouth")
"""

import os
import logging
from functools import lru_cache

log = logging.getLogger(__name__)


def _require_env(key: str) -> str:
    """Get env var or raise a clear error."""
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Add it to your .env file. See .env.example for all required vars."
        )
    return val


@lru_cache(maxsize=1)
def get_cu_client():
    """
    Azure Content Understanding / Document Intelligence client.
    pip install azure-ai-documentintelligence
    """
    endpoint = _require_env("AZURE_CU_ENDPOINT")
    key = _require_env("AZURE_CU_KEY")

    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    return DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))


@lru_cache(maxsize=1)
def get_blob_client():
    """
    Azure Blob Storage client.
    pip install azure-storage-blob
    """
    connection_str = _require_env("AZURE_BLOB_CONNECTION_STR")

    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient.from_connection_string(connection_str)


@lru_cache(maxsize=1)
def get_openai_client():
    """
    Azure OpenAI client for GPT-4o-mini extraction.
    pip install openai
    """
    endpoint = _require_env("AZURE_OPENAI_ENDPOINT")
    key = _require_env("AZURE_OPENAI_KEY")

    from openai import AzureOpenAI
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version="2024-02-01",
    )


@lru_cache(maxsize=1)
def get_speech_config():
    """
    Azure Speech Services config for audio transcription.
    pip install azure-cognitiveservices-speech

    Free tier: 5 hours/month transcription.
    Enable: Azure Portal → Create Resource → Speech.
    """
    key = _require_env("AZURE_SPEECH_KEY")
    region = _require_env("AZURE_SPEECH_REGION")

    import azure.cognitiveservices.speech as speechsdk
    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_recognition_language = "en-US"
    # Output detailed results so we can pull full text from all segments
    config.output_format = speechsdk.OutputFormat.Detailed
    return config


def get_speech_endpoint() -> tuple[str, str]:
    """
    Return (key, region) for use with the Speech batch REST API.
    Separate from get_speech_config() because batch API uses raw HTTP,
    not the SDK config object.
    """
    key = _require_env("AZURE_SPEECH_KEY")
    region = _require_env("AZURE_SPEECH_REGION")
    return key, region


def get_openai_deployment() -> str:
    """Return the configured GPT-4o deployment name."""
    return os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
