# Makefile — Contract Intelligence Platform
# Usage: make test, make test-unit, make test-pdf, make golden

.PHONY: test test-unit test-pdf test-golden test-all generate-golden install

## Run fast unit tests only (no Azure needed) — use this before every commit
test-unit:
	pytest tests/test_golden.py -v -m "unit"

## Run PDF generation tests (no Azure needed)
test-pdf:
	pytest tests/test_golden.py -v -m "pdf"

## Run golden snapshot tests (no Azure needed)
test-golden:
	pytest tests/test_golden.py -v -m "golden"

## Run unit + pdf + golden (everything except integration)
test:
	pytest tests/test_golden.py -v -m "not integration"

## Run ALL tests including integration (requires Azure keys in .env)
test-all:
	pytest tests/test_golden.py -v

## Regenerate golden snapshot files after intentional schema changes
generate-golden:
	pytest tests/test_golden.py -v -m "integration" --generate-golden

## Install test dependencies
install:
	pip install pytest pytest-asyncio jsonschema reportlab pyyaml python-dotenv

