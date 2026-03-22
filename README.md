# ── SOW Analyzer ─────────────────────────────────────────────────────────
  - canonicalPath: parties.client.name
    sourceAnalyzer: sow
    sourceField: parties
    transform: as_is
    precedence: 4

  - canonicalPath: dates.effectiveDate
    sourceAnalyzer: sow
    sourceField: effectiveDateGood result for a real SOW file. The pipeline is working correctly. Let me give you an honest read of this output:

---

## What worked well ✅
- `parties.client.name` → Helios Global Manufacturing Corporation (0.754)
- `parties.vendor.name` → Apex Digital Transformation Services Ltd. (0.754)
- `dates.expirationDate` → extracted from SOW (0.653)
- `scope.description` → rich summary from SOW (0.653)
- `missingFields` → clean, no structural keys ✅
- `review` fields no longer in missingFields ✅
- Conflicts detected correctly between deal_intake and sow

---

## Issues to address

**Issue 1 — `scope.deliverables` are garbage**

```
"Migration of source systems\" (per
analytics segment includes Power BI workspace governance?
Grafana dashboards or
```

These are truncated fragments. The SOW deliverables field is a long string with `\n\n` separators — the unwrap logic is treating it as a CU array but it's actually a plain string. Fix in `_extract_derived_fields` in `pdf_handler.py`:

```python
# Add this to the array_fields unwrap section
# SOW returns deliverables as a plain string with \n\n separators
# deal_intake returns as CU array — handle both

def _split_string_deliverables(value) -> list:
    """Split string deliverables into a clean list."""
    if isinstance(value, str):
        items = [
            item.strip()
            for item in value.replace("\n\n", "\n").split("\n")
            if item.strip()
        ]
        return items
    return value
```

Then in `_extract_derived_fields` add:

```python
# Split string-based deliverables (SOW returns these as plain strings)
for field in ("deliverables", "inScopeItems", "milestones"):
    val = extracted.get(field)
    if isinstance(val, str) and val:
        extracted[field] = _split_string_deliverables(val)
```

**Issue 2 — `parties.client.name` conflict with SOW**

SOW returns:
```
PARTY::Helios Global... | ROLE::client || PARTY::Apex... | ROLE::vendor
```

This is the structured party format from the SOW schema. The conflict is expected but the SOW value is unparsed. Add a transform to `map_to_canonical.py` to parse this format:

In `apply_transform()` add:

```python
if transform == "parse_party_client":
    # Extract PARTY where ROLE::client
    for segment in str(value).split("||"):
        if "ROLE::client" in segment:
            for part in segment.split("|"):
                if part.strip().startswith("PARTY::"):
                    return part.strip().replace("PARTY::", "").strip()
    return value

if transform == "parse_party_vendor":
    for segment in str(value).split("||"):
        if "ROLE::vendor" in segment:
            for part in segment.split("|"):
                if part.strip().startswith("PARTY::"):
                    return part.strip().replace("PARTY::", "").strip()
    return value
```

Then update the SOW mapping rules:

```yaml
  - canonicalPath: parties.client.name
    sourceAnalyzer: sow
    sourceField: parties
    transform: parse_party_client
    precedence: 4

  - canonicalPath: parties.vendor.name
    sourceAnalyzer: sow
    sourceField: parties
    transform: parse_party_vendor
    precedence: 4
```

**Issue 3 — `commercials` all empty**

The SOW has `paymentTerms`, `feesSummary`, `pricingModel` fields but they're not in your mapping yet. Add to `mapping-matrix.yaml`:

```yaml
  - canonicalPath: commercials.paymentTerms
    sourceAnalyzer: sow
    sourceField: paymentTerms
    transform: as_is
    precedence: 5

  - canonicalPath: commercials.totalValue
    sourceAnalyzer: sow
    sourceField: feesSummary
    transform: as_is
    precedence: 4
```

**Issue 4 — `risks` empty**

SOW has a `risks` field. Add to mapping:

```yaml
  - canonicalPath: risks
    sourceAnalyzer: sow
    sourceField: risks
    transform: as_is
    precedence: 4
```

---

## `map_to_canonical.py` needs to call transforms

Right now `apply_transform()` exists but `map_to_canonical()` never calls it. Find this block in `map_to_canonical()`:

```python
value = raw_result.get(source_field)
if value is None:
    continue
set_nested(canonical, canonical_path, value)
```

Replace with:

```python
value = raw_result.get(source_field)
if value is None:
    continue
transform = rule.get("transform", "as_is")
value = apply_transform(value, transform)
set_nested(canonical, canonical_path, value)
```

---

Make these 4 fixes, run the SOW file again, and the output will be significantly cleaner. The core pipeline is solid — this is just refinement at this point.
    transform: as_is
    precedence: 5

  - canonicalPath: dates.expirationDate
    sourceAnalyzer: sow
    sourceField: term
    transform: as_is
    precedence: 5

  - canonicalPath: scope.description
    sourceAnalyzer: sow
    sourceField: scopeSummary
    transform: as_is
    precedence: 4

  - canonicalPath: scope.deliverables
    sourceAnalyzer: sow
    sourceField: deliverables
    transform: as_is
    precedence: 5

  - canonicalPath: scope.milestones
    sourceAnalyzer: sow
    sourceField: milestones
    transform: as_is
    precedence: 5

  - canonicalPath: commercials.paymentTerms
    sourceAnalyzer: sow
    sourceField: paymentTerms
    transform: as_is
    precedence: 4

  - canonicalPath: legal.governingLaw
    sourceAnalyzer: sow
    sourceField: governingLaw
    transform: as_is
    precedence: 3

  - canonicalPath: legal.disputeResolution
    sourceAnalyzer: sow
    sourceField: disputeResolution
    transform: as_is
    precedence: 5
