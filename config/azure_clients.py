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
    AZURE_OPENAI_DEPLOYMENT    GPT-4o deployment name (e.g. "gpt-4o")
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

    TODO: Replace with the correct SDK class for your CU setup.
    If using Azure AI Document Intelligence SDK:
        pip install azure-ai-documentintelligence
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential

    If using Content Understanding directly (newer):
        from azure.ai.documentintelligence import DocumentIntelligenceClient
    """
    endpoint = _require_env("AZURE_CU_ENDPOINT")
    key = _require_env("AZURE_CU_KEY")

    # TODO: Uncomment once you've confirmed your CU SDK package:
    # from azure.ai.documentintelligence import DocumentIntelligenceClient
    # from azure.core.credentials import AzureKeyCredential
    # return DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    log.warning("[AzureClients] CU client is a stub — install SDK and uncomment above")
    return _StubClient("CU", endpoint)


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
    Azure OpenAI client for GPT-4o extraction.
    pip install openai

    NOTE: You need to request Azure OpenAI access if not already approved.
    Takes ~1 business day: https://aka.ms/oai/access
    """
    endpoint = _require_env("AZURE_OPENAI_ENDPOINT")
    key = _require_env("AZURE_OPENAI_KEY")

    # TODO: Uncomment once Azure OpenAI is provisioned:
    # from openai import AzureOpenAI
    # return AzureOpenAI(azure_endpoint=endpoint, api_key=key, api_version="2024-02-01")

    log.warning("[AzureClients] OpenAI client is a stub — provision Azure OpenAI and uncomment above")
    return _StubClient("OpenAI", endpoint)


@lru_cache(maxsize=1)
def get_speech_config():
    """
    Azure Speech Services config for audio transcription.
    pip install azure-cognitiveservices-speech

    NOTE: Speech Services free tier = 5 hours/month transcription.
    Enable in Azure Portal → Create Resource → Speech.
    """
    key = _require_env("AZURE_SPEECH_KEY")
    region = _require_env("AZURE_SPEECH_REGION")

    # TODO: Uncomment once Speech Services is provisioned:
    # import azure.cognitiveservices.speech as speechsdk
    # config = speechsdk.SpeechConfig(subscription=key, region=region)
    # config.speech_recognition_language = "en-US"
    # return config

    log.warning("[AzureClients] Speech config is a stub — provision Speech Services and uncomment above")
    return _StubClient("Speech", region)


class _StubClient:
    """Placeholder client for services not yet provisioned."""
    def __init__(self, service_name: str, endpoint: str):
        self._service = service_name
        self._endpoint = endpoint

    def __getattr__(self, name):
        raise NotImplementedError(
            f"{self._service} client is not yet configured. "
            f"See azure_clients.py for setup instructions."
        )
