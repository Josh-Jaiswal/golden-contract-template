Good progress but two clear issues remain. Let me be direct about what's happening:

---

## Problem 1 — `scope.deliverables` is pulling from the wrong analyzer

The deal_intake deliverables are garbage fragments because this is a **SOW document**, not a deal intake notes file. The deal-intake analyzer is trying to extract `inScope` from a formal SOW PDF and failing badly.

The SOW analyzer returned the correct single deliverable:
```
"10 structured sessions (6 live workshops + 4 recorded modules)"
```

But deal_intake wins because it has higher confidence (0.749 vs 0.659).

**Fix — lower deal_intake deliverables precedence for SOW docs**, or better, map SOW `deliverablesComposite` instead which is the structured field:

Update `mapping-matrix.yaml` SOW deliverables rule:

```yaml
  - canonicalPath: scope.deliverables
    sourceAnalyzer: sow
    sourceField: deliverablesComposite
    transform: as_is
    precedence: 6    # higher than deal_intake's 5
```

And lower deal_intake deliverables precedence:

```yaml
  - canonicalPath: scope.deliverables
    sourceAnalyzer: deal_intake
    sourceField: inScope
    transform: as_is
    precedence: 3    # was 5, now lower than SOW
```

---

## Problem 2 — `commercials.totalValue` is extracting missing clauses text

```
"1. Fixed Fee portion... 2. Estimated T&M hours... 3. Confirmation that rate card..."
```

This is the SOW analyzer's `missingRequiredClauses` output bleeding into `feesSummary`. The SOW PDF doesn't have explicit fee totals — it has a rate card instead. 

**Fix — map `rateCard` instead of `feesSummary`:**

```yaml
  - canonicalPath: commercials.totalValue
    sourceAnalyzer: sow
    sourceField: rateCard
    transform: as_is
    precedence: 4
```

---

## Problem 3 — `missingFields` still has `review.*` keys

Your `STRUCTURAL_KEYS` fix didn't apply. Confirm your `merge_engine.py` has exactly:

```python
STRUCTURAL_KEYS = {
    "missingFields", "conflicts", "provenance", "risks"
}
```

`"review"` must NOT be in that set.

---

## Problem 4 — `scope.deliverables` unwrap is still broken

The deal_intake `inScope` field for this SOW document is returning fragments like `"Migration of source systems\" (per` — these are truncated because the SOW's missingClauses text is bleeding into the inScope field.

The real fix is to **not run deal_intake's inScope mapping when the document is a pure SOW**. Add a source document type check in `handle_pdf`:

```python
# Tag results with document context
deal_result["_docContext"] = contract_type  # will be "both" or "sow"
```

Then in `map_to_canonical` skip deal_intake deliverables mapping when context is pure SOW. But this is complex — for now the precedence fix (Problem 1) is enough.

---

## Make these two changes now

**In `mapping-matrix.yaml`:**

```yaml
  # Deal intake deliverables — lower precedence so SOW wins
  - canonicalPath: scope.deliverables
    sourceAnalyzer: deal_intake
    sourceField: inScope
    transform: as_is
    precedence: 3    # changed from 5

  # SOW deliverables — use composite structured field, highest precedence
  - canonicalPath: scope.deliverables
    sourceAnalyzer: sow
    sourceField: deliverablesComposite
    transform: as_is
    precedence: 6    # highest

  # SOW commercials — use rateCard not feesSummary
  - canonicalPath: commercials.totalValue
    sourceAnalyzer: sow
    sourceField: rateCard
    transform: as_is
    precedence: 4
```

Run again and the deliverables conflict should resolve to the SOW's clean structured output, and commercials will show the actual rate card instead of missing clauses text.
