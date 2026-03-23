No — the missing fields list is too noisy now. Most of those are SOW-specific fields showing as missing on an NDA document, which makes no sense.

---

## The fix — filter missing fields by document type

In `merge_engine.py` in `_set_review_status`, add a filter so only genuinely relevant fields show as missing:

```python
def _set_review_status(merged: dict) -> None:
    reasons = []

    if merged["conflicts"]:
        reasons.append(f"{len(merged['conflicts'])} field conflict(s) found")

    critical_fields = [
        "parties.client.name",
        "parties.vendor.name",
        "dates.effectiveDate",
    ]
    missing_critical = [f for f in critical_fields if f in merged["missingFields"]]
    if missing_critical:
        reasons.append(f"Critical fields missing: {missing_critical}")

    if reasons:
        merged["review"]["status"] = "needs_review"
        merged["review"]["reviewReason"] = reasons
    else:
        merged["review"]["status"] = "auto"

    # Remove review.* — set programmatically
    merged["missingFields"] = [
        f for f in merged["missingFields"]
        if not f.startswith("review.")
    ]
```

But that alone doesn't fix the noise. The real fix is in `generate_contract_pdf.py` — filter what gets shown in Appendix A based on what's actually relevant:

In `build_appendix`, replace the missing fields section:

```python
    missing = canonical.get("missingFields", [])
    if missing:
        # Only show fields that are genuinely expected to be populated
        # Skip SOW-only fields when generating NDA and vice versa
        skip_always = {
            "parties.client.signatories",
            "parties.vendor.signatories",
            "dates.executionDate",
        }
        skip_sow_only = {
            "scope.sowReferenceId", "scope.locationAndTravel",
            "projectGovernance.acceptanceCriteria", "projectGovernance.acceptanceTimeline",
            "projectGovernance.changeControl", "projectGovernance.issueEscalation",
            "projectGovernance.governanceModel", "projectGovernance.keyPersonnel",
            "projectGovernance.dependencies", "projectGovernance.assumptions",
            "projectGovernance.constraints",
            "legal.warranties", "legal.indemnities", "legal.terminationForConvenience",
            "legal.terminationForCause", "legal.injunctiveRelief",
            "legal.licenseGrants", "legal.thirdPartySoftware",
            "legal.msaReference", "legal.serviceLevels",
            "commercials.expenses",
        }
        skip_nda_only = {
            "confidentiality.obligations",
        }

        # Filter to only genuinely missing important fields
        important_missing = [
            f for f in missing
            if f not in skip_always
            and f not in skip_sow_only
            and f not in skip_nda_only
        ]

        if important_missing:
            story.append(Paragraph("Missing Fields", styles["h2"]))
            story += section_rule(styles)
            story += bullet_list(important_missing, styles)
            story.append(Spacer(1, 12))
```

This way the missing fields list only shows things that actually matter — like `dates.effectiveDate`, `legal.governingLaw`, `commercials.totalValue` — not every optional SOW governance field that wasn't in the document.