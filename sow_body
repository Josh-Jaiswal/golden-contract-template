def build_sow_body(canonical, styles):
    story = []
    parties     = canonical.get("parties", {})
    dates       = canonical.get("dates", {})
    scope       = canonical.get("scope", {})
    commercials = canonical.get("commercials", {})
    security    = canonical.get("security", {})
    legal       = canonical.get("legal", {})
    gov         = canonical.get("projectGovernance", {})

    client = parties.get("client", {}).get("name", "")
    vendor = parties.get("vendor", {}).get("name", "")

    # ── Pre-compute fallback values ───────────────────────────────────────
    ms_str = str(scope.get("milestones", ""))

    # Term / Expiry fallback — derive from milestone duration if blank
    expiry = dates.get("expirationDate", "")
    if not has_value(expiry):
        dur_m = re.search(r'(\d+)\s*week', ms_str, re.IGNORECASE)
        if dur_m:
            expiry = (
                f"This SOW expires {dur_m.group(1)} weeks after Pilot Kickoff "
                f"unless extended by mutual written agreement"
            )
        else:
            expiry = "To be confirmed — duration to be agreed by both parties"

    # Dispute Resolution fallback
    dispute = legal.get("disputeResolution", "")
    if not has_value(dispute):
        gov_law = legal.get("governingLaw", "") or "the governing jurisdiction"
        dispute = (
            f"Any disputes shall first be escalated to senior management of both parties. "
            f"If unresolved within 30 days, disputes shall be referred to arbitration "
            f"under the laws of {gov_law}."
        )

    # Service Levels fallback
    sla = legal.get("serviceLevels", "")
    if not has_value(sla):
        sla = (
            "No formal SLAs apply during the pilot phase. "
            "Support response targets to be agreed prior to production rollout."
        )

    # Expenses fallback
    expenses = commercials.get("expenses", "")
    if not has_value(expenses):
        expenses = "All expenses must be pre-approved in writing by the Client prior to being incurred"

    # Governance clause numbers derived from milestone data
    ck_week  = "6"
    wm = re.search(r'week\s*(\d+)', ms_str, re.I)
    if wm:
        ck_week = wm.group(1)

    pilot_dur = "the agreed"
    dm = re.search(r'(\d+)\s*week(?!s?\s*\d)', ms_str, re.I)
    if dm:
        pilot_dur = f"{dm.group(1)}-week"

    # ── 1. Contracting Parties & Dates ────────────────────────────────────
    story.append(Paragraph("1. CONTRACTING PARTIES & DATES", styles["h1"]))
    story += section_rule(styles)
    rows = [
        ("Client",            client or None),
        ("Vendor / Supplier", vendor or None),
        ("SOW Reference",     scope.get("sowReferenceId") or None),
        ("MSA Reference",     legal.get("msaReference") or None),
        ("Effective Date",    dates.get("effectiveDate") or None),
        ("Term / Expiry",     expiry),
        ("Execution Date",    dates.get("executionDate") or None),
    ]
    story.append(two_col_table(rows, styles))
    story.append(Spacer(1, 16))

    # ── 2. Scope of Work ──────────────────────────────────────────────────
    story.append(Paragraph("2. SCOPE OF WORK", styles["h1"]))
    story += section_rule(styles)

    desc = scope.get("description", "")
    if has_value(desc):
        story.append(info_box(desc, styles, bg=LIGHT_GREY,
                              border=YELLOW_ACCENT, title="Project Summary"))
        story.append(Spacer(1, 8))

    story.append(Paragraph("2.1  In-Scope Deliverables", styles["h2"]))
    story += bullet_list(scope.get("deliverables", []), styles)

    oos = scope.get("outOfScope", [])
    if has_value(oos):
        story.append(Spacer(1, 8))
        story.append(Paragraph("2.2  Out of Scope", styles["h2"]))
        story += bullet_list(oos, styles)

    story.append(Spacer(1, 8))
    story.append(Paragraph("2.3  Milestones", styles["h2"]))
    story += milestone_table(scope.get("milestones", []), styles)

    # 2.4 Project Schedule — extracted timeline first, then milestone-derived bullets
    project_timeline = gov.get("projectTimeline", "")
    if has_value(project_timeline):
        story.append(Spacer(1, 8))
        story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
        story.append(Paragraph(clean_text(project_timeline), styles["body"]))
    elif ms_str and ms_str != "[]":
        duration_m   = re.search(r'(\d+)\s*week(?!s?\s*\d)', ms_str, re.IGNORECASE)
        checkpoint_m = re.search(r'week\s*(\d+)', ms_str, re.IGNORECASE)
        cadence_m    = re.search(
            r'(weekly|bi-weekly|fortnightly|monthly)\s*status',
            ms_str, re.IGNORECASE)

        timeline_notes = []
        if duration_m:
            timeline_notes.append(
                f"Total pilot duration: {duration_m.group(1)} weeks")
        if cadence_m:
            timeline_notes.append(
                f"Status cadence: {cadence_m.group(1).capitalize()} calls throughout pilot")
        if checkpoint_m:
            timeline_notes.append(
                f"Formal mid-pilot review: Week {checkpoint_m.group(1)}")

        if timeline_notes:
            story.append(Spacer(1, 8))
            story.append(Paragraph("2.4  Project Schedule", styles["h2"]))
            story += bullet_list(timeline_notes, styles)

    # 2.5 Location & Delivery (conditional)
    loc = scope.get("locationAndTravel", "")
    if has_value(loc):
        story.append(Spacer(1, 8))
        story.append(Paragraph("2.5  Location & Delivery", styles["h2"]))
        story.append(Paragraph(clean_text(loc), styles["body"]))

    story.append(Spacer(1, 16))

    # ── 3. Commercial Terms ───────────────────────────────────────────────
    story.append(Paragraph("3. COMMERCIAL TERMS", styles["h1"]))
    story += section_rule(styles)
    story.append(two_col_table([
        ("Pricing Model",             commercials.get("pricingModel") or None),
        ("Fee Structure / Rate Card", commercials.get("totalValue") or None),
        ("Payment Terms",             commercials.get("paymentTerms") or None),
        ("Currency",                  commercials.get("currency") or None),
        ("Taxes & Duties",            commercials.get("taxes") or None),
        ("Expenses Policy",           expenses),
    ], styles))
    story.append(Spacer(1, 16))

    # ── 4. Security & Compliance (conditional) ────────────────────────────
    sec_req    = security.get("requirements", "")
    compliance = security.get("complianceStandards", "")
    privacy    = security.get("privacyRequirements", "")
    data_res   = security.get("dataResidency", "")
    personal_dp = security.get("personalDataProcessing", "")
    ns = 4

    if has_value(sec_req) or has_value(compliance) or has_value(privacy):
        story.append(Paragraph("4. SECURITY & COMPLIANCE", styles["h1"]))
        story += section_rule(styles)
        story.append(two_col_table([
            ("Security Requirements",    sec_req or None),
            ("Compliance Standards",     compliance or None),
            ("Data Residency",           data_res or None),
            ("Privacy & Data Types",     privacy or None),
            ("Personal Data Processing",
             "Yes — DPA may be required"
             if str(personal_dp).lower() == "yes" else None),
        ], styles))
        story.append(Spacer(1, 16))
        ns = 5

    # ── 5. Legal & Jurisdiction ───────────────────────────────────────────
    story.append(Paragraph(f"{ns}. LEGAL & JURISDICTION", styles["h1"]))
    story += section_rule(styles)
    story.append(two_col_table([
        ("Governing Law",      legal.get("governingLaw") or None),
        ("Jurisdiction",       legal.get("jurisdiction") or None),
        ("Dispute Resolution", dispute),
        ("Service Levels",     sla),
    ], styles))
    story.append(Spacer(1, 16))
    ns += 1

    # ── 6. Project Governance (conditional) ──────────────────────────────
    deps        = gov.get("dependencies", "")
    assumptions = gov.get("assumptions", "")
    constraints = gov.get("constraints", "")
    gov_model   = gov.get("governanceModel", "")
    key_people  = gov.get("keyPersonnel", "")
    issue_esc   = gov.get("issueEscalation", "")

    if has_value(deps) or has_value(assumptions) or has_value(constraints) \
            or has_value(gov_model) or has_value(key_people):
        story.append(Paragraph(f"{ns}. PROJECT GOVERNANCE", styles["h1"]))
        story += section_rule(styles)

        if has_value(gov_model):
            story.append(Paragraph("Governance Model", styles["h2"]))
            story.append(Paragraph(clean_text(gov_model), styles["body"]))
            story.append(Spacer(1, 8))
        if has_value(key_people):
            story.append(Paragraph("Key Personnel", styles["h2"]))
            story += bullet_list(split_list(key_people), styles)
            story.append(Spacer(1, 8))
        if has_value(issue_esc):
            story.append(Paragraph("Issue Escalation", styles["h2"]))
            story.append(Paragraph(clean_text(issue_esc), styles["body"]))
            story.append(Spacer(1, 8))
        if has_value(deps):
            story.append(Paragraph("Dependencies", styles["h2"]))
            story += bullet_list(split_list(deps), styles)
            story.append(Spacer(1, 8))
        if has_value(assumptions):
            story.append(Paragraph("Assumptions", styles["h2"]))
            story += bullet_list(split_list(assumptions), styles)
            story.append(Spacer(1, 8))
        if has_value(constraints):
            story.append(Paragraph("Constraints", styles["h2"]))
            story += bullet_list(split_list(constraints), styles)

        story.append(Spacer(1, 16))
        ns += 1

    # ── 7. Standard Provisions ────────────────────────────────────────────
    story.append(Paragraph(f"{ns}. STANDARD PROVISIONS", styles["h1"]))
    story += section_rule(styles)
    story.append(Paragraph(
        '<font size="7" color="#6B7280">- = populated from extracted contract data</font>',
        styles["section_tag"]))
    story.append(Spacer(1, 8))
    n = ns

    # 7.1 Change Control — dynamic if extracted
    story.append(dynamic_clause(
        f"{n}.1", "Change Control",
        gov.get("changeControl"),
        "Any change to the scope, timeline, or fees must be agreed in writing "
        "via a Change Request signed by authorised representatives of both parties "
        "prior to implementation. Each Change Request shall include impact assessment "
        "on cost, timeline, and deliverables.",
        styles, is_dynamic=True))

    # 7.2 Acceptance — dynamic if extracted
    acc    = gov.get("acceptanceCriteria", "")
    acc_tl = gov.get("acceptanceTimeline", "")
    acc_text = (
        clean_text(acc) + (" " + clean_text(acc_tl) if has_value(acc_tl) else "")
    ) if has_value(acc) else None
    story.append(dynamic_clause(
        f"{n}.2", "Acceptance",
        acc_text,
        "Each deliverable shall be subject to a written acceptance period of "
        "10 business days. Silence shall not constitute acceptance. The Client "
        "shall provide written acceptance or a detailed list of defects within "
        "the acceptance period.",
        styles, is_dynamic=True))

    # 7.3 Intellectual Property — dynamic if extracted
    story.append(dynamic_clause(
        f"{n}.3", "Intellectual Property",
        legal.get("ipOwnership"),
        "Unless otherwise agreed in writing, all work product created by the "
        "Vendor under this SOW shall be owned by the Client upon full payment "
        "of all fees. Pre-existing IP of either party is not transferred.",
        styles, is_dynamic=True))

    # 7.4 Limitation of Liability — dynamic if extracted
    story.append(dynamic_clause(
        f"{n}.4", "Limitation of Liability",
        legal.get("liabilityCap"),
        "Neither party shall be liable for indirect, incidental, or consequential "
        "damages. Each party's aggregate liability under this SOW shall not exceed "
        "the total fees paid or payable in the preceding twelve months.",
        styles, is_dynamic=True))

    # 7.5 Termination for Convenience — dynamic if extracted
    story.append(dynamic_clause(
        f"{n}.5", "Termination for Convenience",
        legal.get("terminationForConvenience"),
        "Either party may terminate this SOW with 30 days written notice. "
        "Upon termination the Client shall pay for all work completed to the "
        "date of termination on a pro-rata basis.",
        styles, is_dynamic=True))

    # 7.6 Confidentiality — always standard boilerplate
    story.append(dynamic_clause(
        f"{n}.6", "Confidentiality",
        None,
        "Each party shall treat all non-public information received from the "
        "other party as confidential and shall not disclose it to any third "
        "party without prior written consent, for the duration of this SOW "
        "and for two years thereafter.",
        styles))

    # 7.7 Subcontractors — always standard boilerplate
    story.append(dynamic_clause(
        f"{n}.7", "Subcontractors",
        None,
        "The Vendor shall not subcontract any part of the services under this "
        "SOW to a third party without prior written consent from the Client. "
        "Where subcontractors are approved, the Vendor remains fully liable "
        "for their performance and compliance with this SOW.",
        styles))

    # 7.8 Project Governance & Reporting — dynamic if extracted
    gov_model_text = gov.get("governanceModel", "")
    esc_text       = gov.get("issueEscalation", "")

    if has_value(gov_model_text) and has_value(esc_text):
        gov_clause_text = clean_text(gov_model_text) + " " + clean_text(esc_text)
        is_gov_dynamic  = True
    elif has_value(gov_model_text):
        gov_clause_text = clean_text(gov_model_text)
        is_gov_dynamic  = True
    else:
        gov_clause_text = None
        is_gov_dynamic  = False

    story.append(dynamic_clause(
        f"{n}.8", "Project Governance & Reporting",
        gov_clause_text,
        f"The parties shall conduct weekly status calls throughout the "
        f"{pilot_dur} project duration. A formal mid-project review shall "
        f"be conducted at the Week {ck_week} checkpoint to assess delivery "
        f"against milestones and agree any adjustments. Meeting minutes shall "
        f"be circulated within 2 business days of each session.",
        styles, is_dynamic=is_gov_dynamic))

    # Optional clauses — only rendered if extracted from document
    idx = 9
    if has_value(legal.get("warranties")):
        story.append(dynamic_clause(
            f"{n}.{idx}", "Warranties",
            legal.get("warranties"), "", styles, is_dynamic=True))
        idx += 1
    if has_value(legal.get("indemnities")):
        story.append(dynamic_clause(
            f"{n}.{idx}", "Indemnities",
            legal.get("indemnities"), "", styles, is_dynamic=True))
        idx += 1
    if has_value(legal.get("terminationForCause")):
        story.append(dynamic_clause(
            f"{n}.{idx}", "Termination for Cause",
            legal.get("terminationForCause"), "", styles, is_dynamic=True))
        idx += 1
    if has_value(legal.get("injunctiveRelief")):
        story.append(dynamic_clause(
            f"{n}.{idx}", "Injunctive Relief",
            legal.get("injunctiveRelief"), "", styles, is_dynamic=True))
        idx += 1
    if has_value(legal.get("licenseGrants")):
        story.append(dynamic_clause(
            f"{n}.{idx}", "License Grants",
            legal.get("licenseGrants"), "", styles, is_dynamic=True))
        idx += 1
    if has_value(legal.get("thirdPartySoftware")):
        story.append(dynamic_clause(
            f"{n}.{idx}", "Third Party Software",
            legal.get("thirdPartySoftware"), "", styles, is_dynamic=True))

    return story
