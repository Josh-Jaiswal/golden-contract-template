Let me compile everything outstanding into one clean list.

---

## File 1 — `generate_contract_pdf.py`

### In `build_sow_body` — 7 changes

**Change 1 — Term/Expiry cleanup** (top of function, replace expiry fallback block):
```python
expiry = dates.get("expirationDate", "")
if has_value(expiry) and not any(
    kw in str(expiry).lower()
    for kw in ["2026","2025","2027","month","year","extended","unless","expir"]
):
    expiry = ""  # raw milestone text leaked in — force fallback

if not has_value(expiry):
    dur_m = re.search(r'(\d+)\s*week', ms_str, re.IGNORECASE)
    if dur_m:
        expiry = (
            f"This SOW expires {dur_m.group(1)} weeks after Pilot Kickoff "
            f"unless extended by mutual written agreement"
        )
    else:
        expiry = "To be confirmed — duration to be agreed by both parties"
```

**Change 2 — Dispute resolution fallback cleans governing law text**:
```python
if not has_value(dispute):
    gov_law = legal.get("governingLaw", "")
    gov_law_clean = re.sub(
        r'^prefer\s+', '', gov_law, flags=re.IGNORECASE
    ).strip() or "the applicable jurisdiction"
    dispute = (
        f"Any disputes shall first be escalated to senior management of both "
        f"parties. If unresolved within 30 days, disputes shall be referred "
        f"to arbitration under the laws of {gov_law_clean}. "
        f"[Parties to confirm arbitration seat and rules before execution.]"
    )
```

**Change 3 — Data residency adds confirmation tag**:
```python
data_res = security.get("dataResidency", "")
data_res_display = data_res
if has_value(data_res) and "preferred" in str(data_res).lower():
    data_res_display = (
        re.sub(r'\s*preferred', '', str(data_res), flags=re.IGNORECASE).strip()
        + " [To be confirmed as binding requirement before execution]"
    )
```

Then use `data_res_display` in the security table instead of `data_res`.

**Change 4 — Personal data processing row improves DPA language**:
```python
("Personal Data Processing",
 "Yes — Data Processing Agreement (DPA) to be executed prior to data exchange"
 if str(personal_dp).lower() == "yes" else None),
```

**Change 5 — Out of scope force split**:
```python
oos = scope.get("outOfScope", [])
if has_value(oos):
    story.append(Spacer(1, 8))
    story.append(Paragraph("2.2  Out of Scope", styles["h2"]))
    if isinstance(oos, str):
        oos = [i.strip() for i in re.split(r'\n|;;', oos) if i.strip()]
    story += bullet_list(oos, styles)
```

**Change 6 — 2.4 Project Schedule splits into bullets**:
```python
project_timeline = gov.get("projectTimeline", "")
if has_value(project_timeline):
    story.append(Spacer(1, 8))
    story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
    tl_items = re.split(r'\s+(?=[A-Z][a-z])', clean_text(project_timeline))
    if len(tl_items) > 1:
        story += bullet_list(tl_items, styles)
    else:
        story.append(Paragraph(clean_text(project_timeline), styles["body"]))
elif ms_str and ms_str != "[]":
    duration_m   = re.search(r'(\d+)\s*week(?!s?\s*\d)', ms_str, re.IGNORECASE)
    checkpoint_m = re.search(r'week\s*(\d+)', ms_str, re.IGNORECASE)
    cadence_m    = re.search(
        r'(weekly|bi-weekly|fortnightly|monthly)\s*status', ms_str, re.IGNORECASE)
    timeline_notes = []
    if duration_m:
        timeline_notes.append(f"Total pilot duration: {duration_m.group(1)} weeks")
    if cadence_m:
        timeline_notes.append(f"Status cadence: {cadence_m.group(1).capitalize()} calls throughout pilot")
    if checkpoint_m:
        timeline_notes.append(f"Formal mid-pilot review: Week {checkpoint_m.group(1)}")
    if timeline_notes:
        story.append(Spacer(1, 8))
        story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
        story += bullet_list(timeline_notes, styles)
```

**Change 7 — Spacer before section tag to stop it merging with header**:
```python
story.append(Paragraph(f"{ns}. STANDARD PROVISIONS", styles["h1"]))
story += section_rule(styles)
story.append(Spacer(1, 4))  # ADD THIS LINE
story.append(Paragraph(
    '<font size="7" color="#6B7280">- = populated from extracted contract data</font>',
    styles["section_tag"]))
story.append(Spacer(1, 8))
```

---

### In `build_status_banner` — 1 change

Add India DPDP flag when personal data is detected. Find the end of `build_status_banner` before `elems.append(Spacer(1, 12))` and add:

```python
    # Flag India data protection requirement if personal data present
    security = canonical.get("security", {})
    if str(security.get("personalDataProcessing", "")).lower() == "yes":
        elems.append(Spacer(1, 4))
        elems.append(info_box(
            "<b>Data Protection Notice:</b> Personal data processing identified. "
            "Confirm DPA requirement and DPDP Act (India) compliance before execution.",
            styles, bg=AMBER_BG, border=AMBER))

    elems.append(Spacer(1, 12))
    return elems
```

---

### In `build_appendix` — 1 change

Add these to `skip_always` since fallbacks are already shown in the document:

```python
skip_always = {
    "parties.client.signatories",
    "parties.vendor.signatories",
    "parties.ndaType",
    "dates.executionDate",
    "commercials.invoicing",
    "scope.outOfScope",
    "legal.disputeResolution",    # fallback always shown
    "legal.serviceLevels",        # fallback always shown
    "commercials.expenses",       # fallback always shown
}
```

---

### In `bullet_list` function — 1 change

Replace `•` with `-` to fix encoding glitch:

```python
def bullet_list(items, styles):
    elems = []
    if not items:
        return [Paragraph("- None identified", styles["missing"])]
    if isinstance(items, str):
        items = split_list(items)
    for item in items:
        text = clean_text(str(item)).lstrip(". ")
        if text:
            elems.append(Paragraph(f"- {text}", styles["bullet"]))
    return elems or [Paragraph("- None identified", styles["missing"])]
```

---

## File 2 — `map_to_canonical.py`

### In `build_empty_canonical` — 1 change

Add `projectTimeline` to `projectGovernance`:

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

## File 3 — `mapping-matrix.yaml`

### Add one new mapping rule at the end of the SOW section:

```yaml
  - canonicalPath: projectGovernance.projectTimeline
    sourceAnalyzer: sow
    sourceField: projectTimeline
    transform: as_is
    precedence: 5
```

---

## Summary table

| File | Where | What |
|---|---|---|
| `generate_contract_pdf.py` | `build_sow_body` — top expiry block | Fix Term/Expiry leaking milestone text |
| `generate_contract_pdf.py` | `build_sow_body` — dispute fallback | Clean "Prefer" from governing law |
| `generate_contract_pdf.py` | `build_sow_body` — security table | Data residency confirmation tag |
| `generate_contract_pdf.py` | `build_sow_body` — security table | DPA language for personal data |
| `generate_contract_pdf.py` | `build_sow_body` — section 2.2 | Out of scope force split |
| `generate_contract_pdf.py` | `build_sow_body` — section 2.4 | Project schedule split into bullets |
| `generate_contract_pdf.py` | `build_sow_body` — standard provisions | Spacer before section tag |
| `generate_contract_pdf.py` | `build_status_banner` | DPDP Act flag when personal data present |
| `generate_contract_pdf.py` | `build_appendix` | Add resolved fields to skip_always |
| `generate_contract_pdf.py` | `bullet_list` function | Replace `•` with `-` |
| `map_to_canonical.py` | `build_empty_canonical` | Add `projectTimeline` field |
| `mapping-matrix.yaml` | SOW section | Map `projectTimeline` field |

That's everything. All in 3 files, 12 targeted changes.