The `inScope` field from deal-intake comes back like this:

```python
[
  {'type': 'object', 'valueObject': {'item': {'type': 'string', 'valueString': 'Configure Content Understanding...'}}},
  {'type': 'object', 'valueObject': {'item': {'type': 'string', 'valueString': 'Integrate extracted JSON...'}}},
  ...
]
```

So we need a transform that unwraps that structure into a clean list of strings.

---

## Fix 1 — Add unwrap helper to `pdf_handler.py`

Add this function anywhere in `pdf_handler.py`:

```python
def _unwrap_cu_array(raw_array: list) -> list:
    """
    Unwrap CU nested array format into a flat list of strings.
    CU returns arrays as: [{'type': 'object', 'valueObject': {'item': {'valueString': '...'}}}]
    """
    result = []
    for item in raw_array:
        if not isinstance(item, dict):
            result.append(str(item))
            continue

        obj = item.get("valueObject", {})

        # Try common field names CU uses inside array objects
        for key in ("item", "text", "value", "description", "deliverable"):
            if key in obj:
                val = obj[key]
                text = (
                    val.get("valueString")
                    or val.get("content")
                    or str(val)
                )
                if text:
                    result.append(text)
                    break
        else:
            # Fallback — just grab first string value found
            for val in obj.values():
                if isinstance(val, dict):
                    text = val.get("valueString") or val.get("content")
                    if text:
                        result.append(text)
                        break

    return result
```

---

## Fix 2 — Call it inside `_extract_derived_fields`

In your existing `_extract_derived_fields` function, add this after the nextSteps block:

```python
def _extract_derived_fields(extracted: dict) -> dict:
    # ── Existing: Pull NDA execution date from nextSteps ──────────────────
    next_steps = extracted.get("nextSteps", [])
    for step in next_steps:
        if isinstance(step, dict):
            obj = step.get("valueObject", {})
            action = obj.get("action", {}).get("valueString", "").lower()
            due_date = obj.get("dueDate", {}).get("valueDate", "")
            if "nda" in action and "template" in action and due_date:
                extracted["ndaTargetExecutionDate"] = due_date
                break

    # ── NEW: Unwrap nested array fields ───────────────────────────────────
    array_fields = ["inScope", "outOfScope", "nextSteps", 
                    "participants", "requestedDocuments", "invoiceTriggers"]
    
    for field in array_fields:
        val = extracted.get(field)
        if isinstance(val, list):
            extracted[field] = _unwrap_cu_array(val)

    return extracted
```

---

## Fix 3 — Add deliverables mapping to `mapping-matrix.yaml`

```yaml
  - canonicalPath: scope.deliverables
    sourceAnalyzer: deal_intake
    sourceField: inScope
    transform: as_is
    precedence: 5
```

---

Run it and `scope.deliverables` should now show:

```json
"deliverables": [
  "Configure Content Understanding custom task...",
  "Integrate extracted JSON output into Contoso's internal workflow tool",
  "Provide dashboards for intake volume...",
  "Knowledge transfer session + admin guide."
]
```

Share the output and we'll move to the generation layer next.