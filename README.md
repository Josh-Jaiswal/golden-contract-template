I can see exactly what's wrong. The filters are inverted — SOW is showing NDA-only fields as missing, and NDA is showing SOW-only fields as missing. The `doc_type` parameter isn't being passed correctly, or the filter logic is backwards.

---

## Two problems visible

**SOW missing fields shows `confidentiality.obligations`** — that's an NDA field, shouldn't appear in SOW

**NDA missing fields shows all the SOW governance fields** — `projectGovernance.*`, `legal.warranties`, `scope.sowReferenceId` etc — none of these belong in an NDA

---

## Fix — update `skip_sow_only` and `skip_nda_only` and confirm `doc_type` is passed

Replace the entire filter block in `build_appendix`:

```python
def build_appendix(canonical, styles, doc_type="sow"):
    story = [
        PageBreak(),
        Paragraph("APPENDIX A — PIPELINE METADATA", styles["h1"]),
        HRFlowable(width="100%", thickness=0.5, color=YELLOW_ACCENT, spaceAfter=12),
        Paragraph(
            "This appendix is generated automatically by the contract "
            "intelligence pipeline. It documents the AI extraction process "
            "for audit and review purposes and forms no part of the "
            "contractual terms above.", styles["body"]),
        Spacer(1, 12),
    ]

    missing = canonical.get("missingFields", [])
    if missing:

        # Never show these regardless of doc type
        skip_always = {
            "parties.client.signatories",
            "parties.vendor.signatories",
            "parties.ndaType",
            "dates.executionDate",
            "commercials.invoicing",
            "scope.outOfScope",
        }

        # These only make sense in a SOW — hide from NDA appendix
        sow_only_fields = {
            "scope.sowReferenceId",
            "scope.locationAndTravel",
            "scope.deliverables",
            "scope.milestones",
            "scope.description",
            "commercials.pricingModel",
            "commercials.taxes",
            "commercials.expenses",
            "security.complianceStandards",
            "security.privacyRequirements",
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

        # These only make sense in an NDA — hide from SOW appendix
        nda_only_fields = {
            "confidentiality.term",
            "confidentiality.obligations",
            "confidentiality.exceptions",
        }

        important_missing = [
            f for f in missing
            if f not in skip_always
            and not (doc_type == "nda" and f in sow_only_fields)
            and not (doc_type == "sow" and f in nda_only_fields)
        ]

        if important_missing:
            story.append(Paragraph("Missing Fields", styles["h2"]))
            story += section_rule(styles)
            story += bullet_list(important_missing, styles)
            story.append(Spacer(1, 12))

    story += conflict_table(canonical.get("conflicts", []), styles)
    story.append(Spacer(1, 8))
    story += provenance_table(canonical.get("provenance", []), styles)
    return story
```

Then confirm in `generate_pdf` the call passes doc_type:

```python
story += build_appendix(canonical, styles, doc_type=doc_type)
```

---

After this fix:

**SOW missing fields** should show only:
- `dates.expirationDate` — genuinely missing
- `legal.disputeResolution` — genuinely missing

**NDA missing fields** should show only:
- `dates.expirationDate` — genuinely missing
- `legal.disputeResolution` — genuinely missing
- Anything else that's genuinely absent from the NDA

Both documents should now have clean, relevant missing field lists.