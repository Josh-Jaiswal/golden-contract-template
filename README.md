raw_results: list[dict] = handler(
    file_path=str(path),
    contract_type=contract_type,
    upload_to_blob=upload_to_blob,
)
log.info(f"[Pipeline] Extraction complete — {len(raw_results)} result(s) from handler")

# TEMP — SOW debug only
for r in raw_results:
    if r.get('_source') == 'sow':
        print(f"\n=== SOW RAW FIELDS ===")
        for k, v in r.items():
            if not k.startswith('_'):
                print(f"  {k}: {v}")
