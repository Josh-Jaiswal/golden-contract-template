
raw_results: list[dict] = handler(
    file_path=str(path),
    contract_type=contract_type,
    upload_to_blob=upload_to_blob,
)
# TEMP DEBUG
for r in raw_results:
    print(f"\n=== RAW FIELDS FROM {r.get('_source')} ===")
    for k, v in r.items():
        if not k.startswith('_'):
            print(f"  {k}: {v}")

# Contract Processing Pipeline
# Multi-modal → Canonical Schema
raw_results: list[dict] = handler(...)
for r in raw_results:
    log.info(f"RAW FIELDS FROM {r.get('_source')}: {[k for k in r.keys() if not k.startswith('_')]}")
## Architecture

```
Input (PDF / DOCX / Email / Audio)
         │
         ▼
┌─────────────────────────────────────┐
│       Modality Normalization        │
│                                     │
│  PDF  ──────────────────► CU ────┐  │
│  DOCX ──► convert to PDF ► CU    │  │
│  Email ──► parse text ──► GPT-4o─┤  │
│  Audio ──► Speech ──────► GPT-4o─┘  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         map_to_canonical.py         │
│    (applies mapping-matrix.yaml)    │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│           merge_engine.py           │
│   (applies precedence-rules.yaml)   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     contract-package.schema.json    │
│      (validated canonical output)   │
└─────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Copy and fill in env vars
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the pipeline (stub mode — no Azure calls yet)
python orchestration/functions/run_pipeline.py --input sample.pdf --type nda

# 4. Wire up Azure services in config/azure_clients.py (see TODOs)
```

## File Structure

```
contract-pipeline/
├── orchestration/functions/
│   ├── run_pipeline.py        ← MAIN ENTRY POINT
│   ├── map_to_canonical.py    ← applies mapping-matrix.yaml
│   └── merge_engine.py        ← applies precedence-rules.yaml
│
├── normalization/
│   ├── pdf_handler.py         ← PDF → CU analyzers
│   ├── docx_handler.py        ← DOCX → PDF → CU
│   ├── email_handler.py       ← Email → GPT-4o
│   ├── audio_handler.py       ← Audio → Speech → GPT-4o
│   └── blob_uploader.py       ← uploads to Azure Blob Storage
│
├── canonical/
│   ├── contract-package.schema.json   ← your existing schema ✅
│   ├── mapping-matrix.yaml            ← your existing mappings ✅
│   └── precedence-rules.yaml          ← your existing rules ✅
│
├── analyzers/                 ← your 3 CU analyzers ✅
│   ├── deal-intake/
│   ├── nda/
│   └── sow/
│
├── validators/
│   └── schema_validator.py    ← validates final output
│
├── config/
│   └── azure_clients.py       ← all Azure service clients
│
├── tests/                     ← wire up your golden test cases
├── .env.example               ← copy to .env and fill in
└── requirements.txt
```
python orchestration/functions-or-container-app/run_pipeline.py --input orchestration/functions-or-container-app/run_pipeline.py --type nda --no-blob
## What Needs Wiring (TODOs)

| File | TODO | Azure Service |
|------|------|---------------|
| `pdf_handler.py` | Replace `_stub_extraction()` with real CU call | CU ✅ |
| `email_handler.py` | Wire `_extract_with_llm()` | Azure OpenAI ❌ |
| `audio_handler.py` | Wire `transcribe_audio()` | Speech Services ❌ |
| `azure_clients.py` | Uncomment SDK clients as services are provisioned | — |

## Recommended Build Order

1. ✅ Confirm stubs run: `python run_pipeline.py --input test.pdf`
2. 🔧 Wire CU call in `pdf_handler.py` (you have CU credentials)
3. 🔧 Provision Azure OpenAI → wire email + audio LLM extraction
4. 🔧 Provision Speech Services → wire `_transcribe_realtime()`
5. 🔧 Build `generation/` layer for NDA/SOW template output
