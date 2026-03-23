You're right. The hardcoded "12 weeks", "Week 6", "weekly" detection is brittle — it only works for this specific document. Here's how to make it properly dynamic.

---

## The root cause

The timeline/governance data exists in your CU extraction but it's buried in fields you're not fully using:

- `projectTimeline` — SOW analyzer extracts this
- `governanceModel` — SOW analyzer extracts cadence info
- `milestones` — already mapped but parsed for display only

These need to be mapped and rendered properly instead of regex-guessing from milestone strings.

---

## Fix 1 — Map `projectTimeline` in `mapping-matrix.yaml`

Add this mapping:

```yaml
  - canonicalPath: projectGovernance.projectTimeline
    sourceAnalyzer: sow
    sourceField: projectTimeline
    transform: as_is
    precedence: 5
```

Then add `projectTimeline` to `build_empty_canonical` in `map_to_canonical.py`:

```python
"projectGovernance": {
    "acceptanceCriteria":  "",
    "acceptanceTimeline":  "",
    "changeControl":       "",
    "issueEscalation":     "",
    "governanceModel":     "",
    "projectTimeline":     "",    # ADD THIS
    "keyPersonnel":        "",
    "dependencies":        "",
    "assumptions":         "",
    "constraints":         "",
},
```

---

## Fix 2 — Replace hardcoded timeline extraction with extracted data

In `build_sow_body` replace the hardcoded timeline block entirely:

```python
    # Project timeline — use extracted data, not regex guessing
    project_timeline = gov.get("projectTimeline", "")
    governance_model = gov.get("governanceModel", "")

    # Build timeline notes from actual extracted fields
    timeline_notes = []

    if has_value(project_timeline):
        # CU extracted a timeline — use it directly
        story.append(Spacer(1, 8))
        story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
        story.append(Paragraph(clean_text(project_timeline), styles["body"]))
    elif has_value(governance_model):
        # Governance model has schedule info
        story.append(Spacer(1, 8))
        story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
        story.append(Paragraph(clean_text(governance_model), styles["body"]))
    else:
        # Nothing extracted — build from milestones if available
        ms_str = str(scope.get("milestones", ""))
        if ms_str and ms_str != "[]":
            # Extract any duration/cadence mentions from milestone text
            duration_m = re.search(r'(\d+)\s*week', ms_str, re.IGNORECASE)
            checkpoint_m = re.search(r'week\s*(\d+)', ms_str, re.IGNORECASE)
            cadence_m = re.search(r'(weekly|bi-weekly|fortnightly|monthly)\s*status', ms_str, re.IGNORECASE)

            if duration_m or checkpoint_m or cadence_m:
                story.append(Spacer(1, 8))
                story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
                if duration_m:
                    timeline_notes.append(f"Total duration: {duration_m.group(1)} weeks")
                if cadence_m:
                    timeline_notes.append(f"Status cadence: {cadence_m.group(1).capitalize()} calls")
                if checkpoint_m:
                    timeline_notes.append(f"Mid-project review: Week {checkpoint_m.group(1)}")
                if timeline_notes:
                    story += bullet_list(timeline_notes, styles)
```

---

## Fix 3 — Replace hardcoded governance clause with extracted data

In the standard provisions, clause 5.7 is currently doing regex on milestone strings. Replace with extracted data:

```python
    # 5.7 Project Governance — use extracted governanceModel if available
    # fall back to milestone-derived schedule if not
    gov_model_text = gov.get("governanceModel", "")
    project_tl     = gov.get("projectTimeline", "")

    if has_value(gov_model_text):
        # CU extracted governance model — use directly
        gov_clause_text = clean_text(gov_model_text)
        is_gov_dynamic = True
    elif has_value(project_tl):
        # Use project timeline text
        gov_clause_text = clean_text(project_tl)
        is_gov_dynamic = True
    else:
        # Build from whatever milestone data exists
        ms_str = str(scope.get("milestones", ""))
        dur_m = re.search(r'(\d+)\s*week', ms_str, re.IGNORECASE)
        ck_m  = re.search(r'week\s*(\d+)', ms_str, re.IGNORECASE)
        dur   = f"{dur_m.group(1)}-week" if dur_m else "the agreed"
        ck    = ck_m.group(1) if ck_m else "6"
        gov_clause_text = None  # triggers fallback boilerplate with dynamic numbers
        is_gov_dynamic = False
        # Override boilerplate variables
        pilot_dur = dur
        ck_week   = ck

    story.append(dynamic_clause(
        f"{n}.7", "Project Governance & Reporting",
        gov_clause_text if has_value(gov_clause_text) else None,
        f"The parties shall conduct weekly status calls throughout the "
        f"{pilot_dur} project duration. A formal mid-project review shall "
        f"be conducted at the Week {ck_week} checkpoint. Meeting minutes "
        f"shall be circulated within 2 business days of each session.",
        styles, is_dynamic=is_gov_dynamic))
```

---

## Fix 4 — Data types processed dynamically

Instead of hardcoding the data types string, map the `privacyRequirements` field which your SOW analyzer already extracts and contains this information:

In the security table replace the hardcoded row with:

```python
    privacy_reqs = security.get("privacyRequirements", "")
    personal_dp  = security.get("personalDataProcessing", "")

    rows = [
        ("Security Requirements",  sec_req or None),
        ("Compliance Standards",   compliance or None),
        ("Data Residency",         data_res or None),
        # Use extracted privacy requirements if available
        ("Privacy & Data Types",   privacy_reqs or None),
        ("Personal Data Processing", "Yes — DPA may be required" if personal_dp == "yes" else None),
    ]
```

`privacyRequirements` from your SOW analyzer already says: `"Procurement documents may include personal data (names, emails), vendor bank details, and contract terms"` — that's exactly the data types info, extracted dynamically.

---

## Summary of what becomes dynamic

| Was hardcoded | Now uses |
|---|---|
| `"12 weeks"` | `projectTimeline` field from SOW analyzer |
| `"Week 6"` | `governanceModel` or milestone regex fallback |
| `"weekly"` | `governanceModel` extracted text |
| Data types string | `privacyRequirements` from SOW analyzer |
| SLA/pen-test notes | Not added — flagged in review banner instead |

Make these 4 fixes — the timeline and governance sections will now use whatever the SOW analyzer actually extracted, with regex as a last resort fallback only when nothing was extracted.