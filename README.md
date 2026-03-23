The NDA is now correct — `dates.expirationDate`, `confidentiality.obligations`, `legal.disputeResolution`. Those are genuinely missing from the source document. ✅

The SOW is still showing all the optional governance fields. The issue is clear — `doc_type` isn't reaching `build_appendix` correctly for the SOW. The function is defaulting to `"sow"` but the filter logic for SOW isn't excluding those optional fields.

The problem is in the filter condition. Look at this line:

```python
and not (doc_type == "nda" and f in sow_only_fields)
```

This says "skip if generating NDA AND field is SOW-only". But for SOW it does nothing — it never skips anything from `sow_only_fields` when `doc_type == "sow"`. That's backwards from what you want.

Those fields in `sow_only_fields` aren't fields to hide from NDA — they're **optional SOW fields that are fine to be empty**. They shouldn't appear as "missing" in either document.

---

## The real fix — rename the sets properly

```python
        # Never show these — always optional or noise
        skip_always = {
            "parties.client.signatories",
            "parties.vendor.signatories",
            "parties.ndaType",
            "dates.executionDate",
            "commercials.invoicing",
            "scope.outOfScope",
            # SOW optional fields — only flag if CU specifically said missing
            "scope.sowReferenceId",
            "scope.locationAndTravel",
            "commercials.expenses",
            "legal.warranties",
            "legal.indemnities",
            "legal.terminationForConvenience",
            "legal.terminationForCause",
            "legal.injunctiveRelief",
            "legal.licenseGrants",
            "legal.thirdPartySoftware",
            "legal.msaReference",
            "legal.serviceLevels",
            "projectGovernance.acceptanceCriteria",
            "projectGovernance.acceptanceTimeline",
            "projectGovernance.changeControl",
            "projectGovernance.issueEscalation",
            "projectGovernance.governanceModel",
            "projectGovernance.keyPersonnel",
            "projectGovernance.dependencies",
            "projectGovernance.assumptions",
            "projectGovernance.constraints",
        }

        # Hide NDA-specific fields when generating SOW
        nda_only_fields = {
            "confidentiality.term",
            "confidentiality.obligations",
            "confidentiality.exceptions",
        }

        # Hide SOW-specific fields when generating NDA
        sow_only_fields = {
            "scope.deliverables",
            "scope.milestones",
            "scope.description",
            "commercials.pricingModel",
            "commercials.taxes",
            "security.complianceStandards",
            "security.privacyRequirements",
        }

        important_missing = [
            f for f in missing
            if f not in skip_always
            and not (doc_type == "sow" and f in nda_only_fields)
            and not (doc_type == "nda" and f in sow_only_fields)
        ]
```

The key change — **move all optional fields into `skip_always`** regardless of doc type. These fields are optional by design — warranties, governance, key personnel etc. They should only be flagged missing if your CU analyzer specifically returns them in `missingRequiredClauses`, not just because they weren't extracted.

After this both documents should show only genuinely important missing fields:

**SOW:** `dates.expirationDate`, `legal.disputeResolution`

**NDA:** `dates.expirationDate`, `confidentiality.obligations`, `legal.disputeResolution`