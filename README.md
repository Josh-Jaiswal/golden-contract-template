Now I have everything I need. Two problems are clear:

1. **`_source` is `None`** — the source label isn't being passed through `_parse_cu_result` correctly
2. **Field names are now known** — I can write the complete mapping matrix

---

## Fix 1 — `_source` is None

In `pdf_handler.py`, find `_parse_cu_result()`. The issue is it strips the `_source` before parsing. Check `run_cu_analyzer()` — make sure it sets `_source` **after** calling `_parse_cu_result`:

```python
def run_cu_analyzer(client, analyzer_id: str, file_location: str, source_label: str) -> dict:
    response = client.begin_analyze(analyzer_id, file_location)
    result = client.poll_result(response)
    extracted = _parse_cu_result(result, source_label)
    extracted["_source"] = source_label  # ← confirm this line exists
    extracted["_analyzerUsed"] = analyzer_id
    return extracted
```

---

## Fix 2 — Replace your entire `mapping-matrix.yaml`

Based on the exact field names CU returned, here is the complete mapping:

```yaml
# canonical/mapping-matrix.yaml
mappings:

  # ── Deal Intake Analyzer ──────────────────────────────────────────────────
  - canonicalPath: parties.client.name
    sourceAnalyzer: deal_intake
    sourceField: customerLegalName
    transform: as_is
    precedence: 5

  - canonicalPath: parties.vendor.name
    sourceAnalyzer: deal_intake
    sourceField: vendorLegalName
    transform: as_is
    precedence: 5

  - canonicalPath: commercials.totalValue
    sourceAnalyzer: deal_intake
    sourceField: setupFee
    transform: as_is
    precedence: 5

  - canonicalPath: commercials.currency
    sourceAnalyzer: deal_intake
    sourceField: currency
    transform: as_is
    precedence: 5

  - canonicalPath: commercials.paymentTerms
    sourceAnalyzer: deal_intake
    sourceField: invoicingTerms
    transform: as_is
    precedence: 5

  - canonicalPath: scope.description
    sourceAnalyzer: deal_intake
    sourceField: sowObjective
    transform: as_is
    precedence: 5

  - canonicalPath: legal.governingLaw
    sourceAnalyzer: deal_intake
    sourceField: governingLaw
    transform: as_is
    precedence: 4

  - canonicalPath: confidentiality.term
    sourceAnalyzer: deal_intake
    sourceField: confidentialityTermYears
    transform: as_is
    precedence: 4

  # ── NDA Analyzer ─────────────────────────────────────────────────────────
  - canonicalPath: parties.client.name
    sourceAnalyzer: nda
    sourceField: disclosingParty
    transform: as_is
    precedence: 5

  - canonicalPath: parties.vendor.name
    sourceAnalyzer: nda
    sourceField: receivingParty
    transform: as_is
    precedence: 5

  - canonicalPath: confidentiality.term
    sourceAnalyzer: nda
    sourceField: confidentialityTermYears
    transform: as_is
    precedence: 5

  - canonicalPath: confidentiality.exceptions
    sourceAnalyzer: nda
    sourceField: exclusionsFromConfidentialInfo
    transform: as_is
    precedence: 5

  - canonicalPath: legal.governingLaw
    sourceAnalyzer: nda
    sourceField: governingLaw
    transform: as_is
    precedence: 5

  - canonicalPath: legal.jurisdiction
    sourceAnalyzer: nda
    sourceField: dataResidencyRequirements
    transform: as_is
    precedence: 3
```

---

## Fix 3 — Update `map_to_canonical.py` to handle `_source` being None

In `map_to_canonical()`, the source lookup fails when `_source` is None. Add a fallback:

```python
source = raw_result.get("_source") or raw_result.get("_analyzerUsed", "unknown")
```

---

Make all three changes, run again, and your output should show `parties.client.name: Contoso India Pvt. Ltd.`, `parties.vendor.name: Fabrikam Solutions Pvt. Ltd.`, `confidentiality.term: 3`, `scope.description`, `commercials` all populated. The pipeline will be functionally complete for PDF inputs.