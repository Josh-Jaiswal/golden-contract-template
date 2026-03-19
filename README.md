
## Question 1 — How does it know it's an NDA?

Look at `pdf_handler.py` in `_detect_contract_type()`:

```python
def _detect_contract_type(deal_intake_result: dict) -> Literal["nda", "sow", "unknown"]:
    contract_type = str(deal_intake_result.get("contractType", "")).lower()
    if "nda" in contract_type or "confidential" in contract_type:
        return "nda"
```

But your deal-intake analyzer doesn't return a `contractType` field — it returns `requestedDocumentTypes: NDA+SOW`. So it's actually falling back to the `--type nda` flag you're passing manually on the command line.

Fix `_detect_contract_type()` to use the real field:

```python
def _detect_contract_type(deal_intake_result: dict) -> Literal["nda", "sow", "unknown"]:
    # Check requestedDocumentTypes field from your deal-intake analyzer
    doc_types = str(deal_intake_result.get("requestedDocumentTypes", "")).lower()
    nda_required = str(deal_intake_result.get("ndaRequired", "")).lower()
    
    has_nda = "nda" in doc_types or nda_required == "yes"
    has_sow = "sow" in doc_types

    if has_nda and has_sow:
        return "nda"  # run NDA first, SOW handled separately
    if has_nda:
        return "nda"
    if has_sow:
        return "sow"
    return "unknown"
```

---

## Question 2 — Yes, that IS the effective date

You're completely right. "Target NDA execution: 2026-03-18" is the effective date. CU just stored it inside `nextSteps` as an action item instead of a dedicated field.

Two ways to fix this:

**Option A — Update your deal-intake CU analyzer schema** to add an `ndaTargetExecutionDate` field. This is the cleanest fix — go into Foundry, edit the deal-intake analyzer schema, add the field, retrain. Then map it:

```yaml
  - canonicalPath: dates.effectiveDate
    sourceAnalyzer: deal_intake
    sourceField: ndaTargetExecutionDate
    transform: as_is
    precedence: 5
```

**Option B — Extract it in code from `nextSteps`** without touching CU. Add this to `_parse_cu_result()` in `pdf_handler.py`:

```python
def _extract_derived_fields(extracted: dict) -> dict:
    """
    Extract fields that CU buries in nested structures.
    """
    # Pull NDA execution date from nextSteps
    next_steps = extracted.get("nextSteps", [])
    for step in next_steps:
        if isinstance(step, dict):
            obj = step.get("valueObject", {})
            action = obj.get("action", {}).get("valueString", "").lower()
            due_date = obj.get("dueDate", {}).get("valueDate", "")
            if "nda" in action and "template" in action and due_date:
                extracted["ndaTargetExecutionDate"] = due_date
                break
    return extracted
```

Then call it inside `_parse_cu_result()` before returning:
```python
    extracted = _extract_derived_fields(extracted)
    return extracted
```

And add to `mapping-matrix.yaml`:
```yaml
  - canonicalPath: dates.effectiveDate
    sourceAnalyzer: deal_intake
    sourceField: ndaTargetExecutionDate
    transform: as_is
    precedence: 4
```

**Option A is better long term. Option B works right now without touching Azure.**

---

## Question 3 — Fix confidence scores

The problem is in `_parse_cu_result()`. CU returns confidence **per field** but your code reads it at the top level of the response, which doesn't exist. Here's the fix:

Replace `_parse_cu_result()` in `pdf_handler.py` with this:

```python
def _parse_cu_result(result: dict, source_label: str) -> dict:
    """
    Parse CU response into flat field dict.
    Correctly reads per-field confidence scores.
    """
    extracted = {"_confidence": 0.0, "_fieldConfidence": {}}

    try:
        contents = result.get("result", {}).get("contents", [])
        if not contents:
            log.warning(f"[CU] No contents in result for {source_label}")
            return extracted

        fields = contents[0].get("fields", {})
        confidences = []

        for field_name, field_data in fields.items():
            # Unwrap the value
            value = (
                field_data.get("valueString")
                or field_data.get("valueNumber")
                or field_data.get("valueArray")
                or field_data.get("valueObject")
                or field_data.get("content")
            )
            if value is not None:
                extracted[field_name] = value

            # Read per-field confidence
            confidence = field_data.get("confidence")
            if confidence is not None:
                extracted["_fieldConfidence"][field_name] = confidence
                confidences.append(confidence)

        # Overall confidence = average of all field confidences
        if confidences:
            extracted["_confidence"] = round(
                sum(confidences) / len(confidences), 3
            )

    except Exception as e:
        log.error(f"[CU] Failed to parse result: {e}")

    return extracted
```

---

Run it again after these three fixes and you'll see:
- Confidence scores populated for both analyzers
- `dates.effectiveDate` populated if you go with Option B
- Contract type auto-detected without needing `--type nda` flag