python orchestration/functions/run_pipeline.py \
  --input tests/fixtures/deal-intake-sample-structured.pdf \
  --type auto \
  --no-blob \
  --output tests/output/canonical-result.json \
  --generate \
  --output-pdf tests/output/generated-nda.pdf
