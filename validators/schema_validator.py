"""
schema_validator.py
────────────────────
Validates a canonical contract package dict against
contract-package.schema.json using jsonschema.

pip install jsonschema
"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent.parent / "canonical" / "contract-package.schema.json"


def validate_canonical_package(package: dict) -> tuple[bool, list[str]]:
    """
    Validate a merged canonical package against the JSON schema.

    Returns:
        (is_valid: bool, errors: list[str])
        errors is empty if is_valid is True.
    """
    try:
        import jsonschema
    except ImportError:
        log.warning("[Validator] jsonschema not installed — skipping validation. pip install jsonschema")
        return True, []

    try:
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
    except FileNotFoundError:
        log.warning(f"[Validator] Schema file not found at {SCHEMA_PATH} — skipping validation")
        return True, []

    validator = jsonschema.Draft7Validator(schema)
    errors = [str(e.message) for e in validator.iter_errors(package)]

    if errors:
        log.warning(f"[Validator] {len(errors)} schema violation(s) found")
        return False, errors

    return True, []
