
# ── Step 1: Route to modality handler ────────────────────────────────────
handler = MODALITY_ROUTER[ext]
raw_results: list[dict] = handler(
    file_path=str(path),
    contract_type=contract_type,
    upload_to_blob=upload_to_blob,
)
log.info(f"[Pipeline] Extraction complete — {len(raw_results)} result(s) from handler")

# TEMP DEBUG — remove after confirming mapping works
for r in raw_results:
    print(f"\n=== RAW FIELDS FROM {r.get('_source')} ===")
    for k, v in r.items():
        if not k.startswith('_'):
            print(f"  {k}: {v}")