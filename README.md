You're right to question it — they overlap but they're actually different things professionally:

---

## What they should contain

**2.4 Project Schedule** — *operational facts*
- Total duration (12 weeks)
- Key dates (kickoff, milestone dates)
- Phase breakdown if available
- This is a **factual reference** section — what dates/duration were agreed

**5.7 Project Governance & Reporting** — *process obligations*
- How the parties will communicate
- Meeting cadence (weekly calls)
- Escalation process
- Who reviews what and when
- This is a **behavioural clause** — what each party is obligated to do

---

## In practice they should use different source fields

**2.4 Project Schedule** should use:
- `scope.milestones` — the milestone table already there
- `projectTimeline` — the raw timeline extracted by CU

**5.7 Project Governance** should use:
- `governanceModel` — meeting cadence, steering committees
- `issueEscalation` — escalation paths
- NOT the timeline dates

---

## Fix — separate the sources

In `build_sow_body` for section 2.4 use only `projectTimeline`:

```python
    project_timeline = gov.get("projectTimeline", "")
    if has_value(project_timeline):
        story.append(Spacer(1, 8))
        story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
        story.append(Paragraph(clean_text(project_timeline), styles["body"]))
```

For clause 5.7 use only `governanceModel` and `issueEscalation`:

```python
    gov_model_text = gov.get("governanceModel", "")
    esc_text       = gov.get("issueEscalation", "")

    if has_value(gov_model_text) and has_value(esc_text):
        gov_clause_text = clean_text(gov_model_text) + " " + clean_text(esc_text)
        is_gov_dynamic = True
    elif has_value(gov_model_text):
        gov_clause_text = clean_text(gov_model_text)
        is_gov_dynamic = True
    else:
        gov_clause_text = None
        is_gov_dynamic = False
```

Now they're pulling from different extracted fields — no overlap. If neither has data, 2.4 simply doesn't render and 5.7 falls back to boilerplate. Clean separation.