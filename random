# ── Azure Speech Services (for audio transcription) ──────────────────────────
# Create in Azure Portal → + Create a resource → Speech
# Free tier: 5 hours/month | Standard: ~$1/hour
AZURE_SPEECH_KEY=your_speech_key_here
AZURE_SPEECH_REGION=uksouth          # e.g. uksouth, eastus, westeurope

# ── Azure OpenAI (for transcript field extraction) ────────────────────────────
# Create in Azure Portal → + Create a resource → Azure OpenAI
# Then deploy a model: Azure OpenAI Studio → Deployments → + Create
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_openai_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini  # your deployment name, not the model name

# ── Azure Blob Storage (already in your .env — audio uses same account) ───────
# Audio files go into a separate container: "audio-staging"
# This container is auto-created on first audio upload.
# AZURE_BLOB_CONNECTION_STR=already_set
