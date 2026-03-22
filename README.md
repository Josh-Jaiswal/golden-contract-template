Let's go through them one by one systematically.

---

## Fix 1 — Error handling in `run_cu_analyzer`

Replace the current `run_cu_analyzer` function in `pdf_handler.py`:

```python
def run_cu_analyzer(client, analyzer_id: str, file_location: str, source_label: str) -> dict:
    try:
        response = client.begin_analyze(analyzer_id, file_location)
        result = client.poll_result(response)
    except Exception as e:
        log.error(f"[CU] API call failed for {source_label}: {e}")
        return {"_source": source_label, "_analyzerUsed": analyzer_id, "_error": str(e), "_confidence": 0.0}

    try:
        extracted = _parse_cu_result(result, source_label)
    except Exception as e:
        log.error(f"[CU] Parse failed for {source_label}: {e}")
        import traceback
        traceback.print_exc()
        extracted = {"_parseError": str(e), "_confidence": 0.0}

    extracted["_source"] = source_label
    extracted["_analyzerUsed"] = analyzer_id
    log.info(f"[CU] {source_label} done — _source={extracted.get('_source')}, confidence={extracted.get('_confidence')}")
    return extracted
```

---

## Fix 2 — Wire SOW analyzer when document has both NDA+SOW

Replace the domain analyzer block at the bottom of `handle_pdf`:

```python
    # Auto-detect contract type if needed
    if contract_type == "auto":
        contract_type = _detect_contract_type(deal_result)
        log.info(f"[PDF Handler] Detected type: {contract_type}")

    # Run NDA analyzer if needed
    if contract_type in ("nda", "both"):
        nda_result = run_cu_analyzer(
            client, CU_ANALYZER_IDS["nda"], file_location, "nda"
        )
        results.append(nda_result)

    # Run SOW analyzer if needed
    if contract_type in ("sow", "both"):
        sow_result = run_cu_analyzer(
            client, CU_ANALYZER_IDS["sow"], file_location, "sow"
        )
        results.append(sow_result)

    return results
```

Then update `_detect_contract_type` to return `"both"`:

```python
def _detect_contract_type(deal_intake_result: dict) -> Literal["nda", "sow", "both", "unknown"]:
    doc_types = str(deal_intake_result.get("requestedDocumentTypes", "")).lower()
    nda_required = str(deal_intake_result.get("ndaRequired", "")).lower()

    has_nda = "nda" in doc_types or nda_required == "yes"
    has_sow = "sow" in doc_types

    if has_nda and has_sow:
        return "both"
    if has_nda:
        return "nda"
    if has_sow:
        return "sow"
    return "unknown"
```

Also update the type hint at the top of `handle_pdf`:
```python
def handle_pdf(
    file_path: str,
    contract_type: Literal["nda", "sow", "both", "auto"] = "auto",
    upload_to_blob: bool = True,
) -> list[dict]:
```

---

## Fix 3 — Clean up `missingFields` in `merge_engine.py`

Find `collect_all_dot_paths` and replace it entirely:

```python
# Keys that are structural — never treat as missing data fields
STRUCTURAL_KEYS = {
    "missingFields", "conflicts", "provenance", 
    "review", "risks", "_source"
}

def collect_all_dot_paths(d: dict, prefix: str = "") -> list[str]:
    """
    Walk a nested dict and return all dot-notation leaf paths.
    Skips internal metadata keys and structural keys.
    """
    paths = []
    for key, val in d.items():
        if key.startswith("_") or key in STRUCTURAL_KEYS:
            continue
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict):
            paths.extend(collect_all_dot_paths(val, full_key))
        else:
            paths.append(full_key)
    return paths
```

---

## Fix 4 — Add `--output` flag to `run_pipeline.py`

Find the CLI entrypoint at the bottom and replace:

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contract Processing Pipeline")
    parser.add_argument("--input", required=True, help="Path to input file")
    parser.add_argument("--type", default="auto", choices=["nda", "sow", "auto"])
    parser.add_argument("--no-blob", action="store_true", help="Skip Blob Storage upload")
    parser.add_argument("--output", help="Save canonical JSON to this file path")
    args = parser.parse_args()

    result = run_pipeline(
        input_path=args.input,
        contract_type=args.type,
        upload_to_blob=not args.no_blob,
    )

    if args.output:
        from pathlib import Path
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        log.info(f"[Pipeline] Output saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
```

---

## Fix 5 — Remove debug block from `run_pipeline.py`

Delete these lines entirely from Step 1:

```python
# DELETE THIS WHOLE BLOCK
for r in raw_results:
    print(f"\n=== RAW FIELDS FROM {r.get('_source')} ===")
    for k, v in r.items():
        if not k.startswith('_'):
            print(f"  {k}: {v}")
```

---

Make all 5 fixes then run:

```bash
python orchestration/functions/run_pipeline.py --input tests/fixtures/deal-intake-sample-structured.pdf --type auto --no-blob --output tests/output/canonical-result.json
```

Three things to confirm in the output:
1. `missingFields` no longer contains `"missingFields"`, `"conflicts"`, `"provenance"`
2. SOW analyzer runs if document has both NDA+SOW
3. Output saved to file

Share the result and we move to the generation layer.
