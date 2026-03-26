"""
generate_contract_pdf.py - Enterprise PDF contract generator.
All standard provisions dynamic. Uses extracted data where available,
falls back to standard boilerplate otherwise.
"""

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, 
    SimpleDocTemplate, Spacer, Table, TableStyle
)
from reportlab.platypus.flowables import Flowable

log = logging.getLogger(__name__)

# ==========================================
# SECTION 1: CONSTANTS & COLOR DEFINITIONS
# ==========================================

BLACK_PRIMARY = colors.HexColor("#111827")
BLACK_TEXT    = colors.HexColor("#1F2937")
YELLOW_ACCENT = colors.HexColor("#F59E0B")
YELLOW_LIGHT  = colors.HexColor("#FCD34D")
WHITE         = colors.white
LIGHT_GREY    = colors.HexColor("#F3F4F6")
MID_GREY      = colors.HexColor("#6B7280")
BORDER        = colors.HexColor("#D1D5DB")
AMBER         = colors.HexColor("#B45309")
AMBER_BG      = colors.HexColor("#FFFBEB")
RED           = colors.HexColor("#991B1B")
RED_BG        = colors.HexColor("#FEF2F2")
GREEN         = colors.HexColor("#065F46")
GREEN_BG      = colors.HexColor("#ECFDF5")

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm


# ==========================================
# SECTION 2: UTILITY & DATA PARSING FUNCTIONS
# ==========================================

def clean_date(v):
    if not v: 
        return ""
    v = str(v).strip().strip('"\')')
    m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4}', v, re.I)
    return m.group(0) if m else v

def clean_text(v):
    if not v: 
        return ""
    t = str(v).strip().replace("\\`", "`").replace("\\\\", "\\")
    return re.sub(r'\s+', ' ', t).strip()

def has_value(v):
    if v is None: 
        return False
    if isinstance(v, str): 
        return bool(v.strip())
    if isinstance(v, list): 
        return len(v) > 0
    return bool(v)

def normalise_term(t):
    if not t: 
        return ""
    s = str(t).strip()
    if any(u in s.lower() for u in ["year", "month", "day", "week"]): 
        return s
    if s.replace(".", ",", 1).replace(",", "", 1).isdigit():
        n = float(s.replace(",", "."))
        return f"{int(n)} months" if n > 10 else f"{int(n)} years"
    return s

def parse_milestones(raw):
    if not raw: 
        return []
    if isinstance(raw, list) and raw and isinstance(raw[0], dict): 
        return raw
    
    text = " ".join(str(i) for i in raw) if isinstance(raw, list) else str(raw)
    ms = []
    
    for lbl, dt in re.findall(r'([A-Za-z][^:]{3,60}):\s*(\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4})', text, re.I):
        ms.append({"milestone": lbl.strip(), "date": dt.strip(), "notes": ""})
    
    if ms: 
        return ms
        
    for part in re.split(r'(?<=[a-z0-9])\s+(?=[A-Z])|[;\n]', text):
        part = part.strip()
        if len(part) > 5:
            dm = re.search(r'(\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4}|\d{1,2}\s+weeks?)', part, re.I)
            if dm:
                d = dm.group(0)
                l = part.replace(d, "").strip(" :-")
                ms.append({"milestone": l or part, "date": d, "notes": ""})
            else:
                ms.append({"milestone": part, "date": "TBD", "notes": ""})
                
    return ms or [{"milestone": text, "date": "TBD", "notes": ""}]

def split_list(value):
    if isinstance(value, list): 
        return [str(i).strip() for i in value if str(i).strip()]
    if not value: 
        return []
    items = re.split(r';;|\n|;(?!\s*\d)', str(value))
    return [i.strip() for i in items if i.strip()]


# ==========================================
# SECTION 3: TYPOGRAPHY & STYLES
# ==========================================

def build_styles():
    def S(n, **k): 
        return ParagraphStyle(n, **k)
        
    return {
        "cover_doctype":  S("cover_doctype", fontName="Helvetica-Bold", fontSize=10, textColor=YELLOW_LIGHT, leading=14, alignment=TA_CENTER),
        "cover_client":   S("cover_client", fontName="Helvetica-Bold", fontSize=22, textColor=WHITE, leading=28, alignment=TA_CENTER),
        "cover_vendor":   S("cover_vendor", fontName="Helvetica", fontSize=14, textColor=YELLOW_LIGHT, leading=20, alignment=TA_CENTER),
        "cover_meta":     S("cover_meta", fontName="Helvetica", fontSize=9, textColor=YELLOW_LIGHT, leading=13, alignment=TA_CENTER),
        "h1":             S("h1", fontName="Helvetica-Bold", fontSize=13, textColor=BLACK_PRIMARY, leading=18, spaceBefore=18, spaceAfter=6),
        "h2":             S("h2", fontName="Helvetica-Bold", fontSize=10, textColor=BLACK_PRIMARY, leading=14, spaceBefore=12, spaceAfter=4),
        "body":           S("body", fontName="Helvetica", fontSize=9, textColor=BLACK_TEXT, leading=14, spaceBefore=2, spaceAfter=2, alignment=TA_JUSTIFY),
        "body_bold":      S("body_bold", fontName="Helvetica-Bold", fontSize=9, textColor=BLACK_PRIMARY, leading=14),
        "label":          S("label", fontName="Helvetica-Bold", fontSize=8, textColor=MID_GREY, leading=11, spaceAfter=1),
        "value":          S("value", fontName="Helvetica", fontSize=9, textColor=BLACK_TEXT, leading=13, spaceAfter=6),
        "bullet":         S("bullet", fontName="Helvetica", fontSize=9, textColor=BLACK_TEXT, leading=13, leftIndent=14, firstLineIndent=-8, spaceBefore=1, spaceAfter=1),
        "missing":        S("missing", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor("#9CA3AF"), leading=12),
        "table_header":   S("table_header", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE, leading=11),
        "table_cell":     S("table_cell", fontName="Helvetica", fontSize=8, textColor=BLACK_TEXT, leading=11),
        "clause_number":  S("clause_number", fontName="Helvetica-Bold", fontSize=9, textColor=YELLOW_ACCENT, leading=13),
        "clause_dynamic": S("clause_dynamic", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#059669"), leading=13),
        "section_tag":    S("section_tag", fontName="Helvetica", fontSize=7, textColor=MID_GREY, leading=10),
    }


# ==========================================
# SECTION 4: PAGE TEMPLATES & CUSTOM FLOWABLES
# ==========================================

class ContractPageTemplate:
    def __init__(self, doc_type, client, vendor, generated_at, review_status):
        self.doc_type = doc_type
        self.client = client
        self.vendor = vendor
        self.generated_at = generated_at
        self.review_status = review_status
        
    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4
        
        canvas.setFillColor(BLACK_PRIMARY)
        canvas.rect(0, h - 18 * mm, w, 18 * mm, fill=1, stroke=0)
        
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(WHITE)
        canvas.drawString(MARGIN, h - 10 * mm, f"{self.doc_type}  ·  {self.client}  ×  {self.vendor}")
        
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(YELLOW_LIGHT)
        canvas.drawRightString(w - MARGIN, h - 10 * mm, f"CONFIDENTIAL  ·  Page {doc.page}")
        
        canvas.setFillColor(YELLOW_ACCENT)
        canvas.rect(0, 0, w, 8 * mm, fill=1, stroke=0)
        
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(BLACK_PRIMARY)
        canvas.drawString(MARGIN, 2.5 * mm, f"Generated: {self.generated_at}  ·  AI-Assisted Draft — Not Legal Advice")
        canvas.drawRightString(w - MARGIN, 2.5 * mm, f"Review Status: {self.review_status.upper()}")
        
        canvas.restoreState()

class NavyCoverPage(Flowable):
    def __init__(self, client, vendor, doc_label, eff_date, generated_at, status):
        super().__init__()
        self.client = client
        self.vendor = vendor
        self.doc_label = doc_label
        self.eff_date = eff_date
        self.generated_at = generated_at
        self.status = status
        self.width = PAGE_W
        self._avail_w = 0
        self._avail_h = 0
        self.height = PAGE_H
        
    def wrap(self, aw, ah):
        self._avail_w = aw
        self._avail_h = ah
        return (aw, ah)
        
    def draw(self):
        c = self.canv
        w, h = PAGE_W, PAGE_H
        
        c.setFillColor(BLACK_PRIMARY)
        c.rect(-MARGIN, -MARGIN - 10 * mm, w, h + MARGIN + 10 * mm, fill=1, stroke=0)
        
        c.setFillColor(YELLOW_ACCENT)
        c.rect(-MARGIN, h * 0.38, w, 3, fill=1, stroke=0)
        
        cy = h * 0.62
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(YELLOW_LIGHT)
        c.drawCentredString(w / 2 - MARGIN, cy + 80, self.doc_label)
        
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(WHITE)
        client_text = self.client if len(self.client) < 45 else self.client[:42] + "…"
        c.drawCentredString(w / 2 - MARGIN, cy + 40, client_text)
        
        c.setFont("Helvetica", 16)
        c.setFillColor(YELLOW_ACCENT)
        c.drawCentredString(w / 2 - MARGIN, cy + 10, "×")
        
        c.setFont("Helvetica", 16)
        c.setFillColor(YELLOW_LIGHT)
        vendor_text = self.vendor if len(self.vendor) < 50 else self.vendor[:47] + "…"
        c.drawCentredString(w / 2 - MARGIN, cy - 20, vendor_text)
        
        c.setFont("Helvetica", 8)
        c.setFillColor(YELLOW_LIGHT)
        c.drawCentredString(w / 2 - MARGIN, cy - 60, f"Effective Date: {self.eff_date or 'TBD'}    ·    Generated: {self.generated_at}")
        
        bc = colors.HexColor("#B45309") if self.status == "needs_review" else colors.HexColor("#059669")
        bt = "⚠  REQUIRES REVIEW BEFORE USE" if self.status == "needs_review" else "✓  AUTO-EXTRACTED"
        
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(bc)
        c.drawCentredString(w / 2 - MARGIN, cy - 82, bt)
        
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#4A6FA5"))
        c.drawCentredString(w / 2 - MARGIN, 20, "CONFIDENTIAL  ·  AI-ASSISTED DRAFT  ·  NOT LEGAL ADVICE  ·  NOT EXECUTED")


# ==========================================
# SECTION 5: REUSABLE UI COMPONENTS
# ==========================================

def build_cover(canonical, doc_type, styles, generated_at):
    p = canonical.get("parties", {})
    client = p.get("client", {}).get("name", "CLIENT")
    vendor = p.get("vendor", {}).get("name", "VENDOR")
    status = canonical.get("review", {}).get("status", "needs_review")
    eff_date = canonical.get("dates", {}).get("effectiveDate", "")
    
    doc_label = "NON-DISCLOSURE AGREEMENT" if doc_type == "nda" else "STATEMENT OF WORK"
    return [NavyCoverPage(client, vendor, doc_label, eff_date, generated_at, status), PageBreak()]

def section_rule(styles):
    return [HRFlowable(width="100%", thickness=0.5, color=YELLOW_ACCENT, spaceAfter=6)]

def info_box(content, styles, bg=LIGHT_GREY, border=YELLOW_ACCENT, title=""):
    inner = []
    if title: 
        inner.append(Paragraph(f"<b>{title}</b>", styles["body_bold"]))
        inner.append(Spacer(1, 3))
        
    inner.append(Paragraph(clean_text(str(content)), styles["body"]))
    t = Table([[inner]], colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEAFTER", (0, 0), (0, -1), 3, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))
    return t

def bullet_list(items, styles):
    elems = []
    if not items: 
        return [Paragraph("— None identified", styles["missing"])]
        
    if isinstance(items, str): 
        items = split_list(items)
        
    for item in items:
        text = clean_text(str(item)).lstrip(". ")
        if text: 
            elems.append(Paragraph(f"• {text}", styles["bullet"]))
            
    return elems or [Paragraph("— None identified", styles["missing"])]

def two_col_table(rows, styles):
    data = []
    for label, value in rows:
        if "date" in label.lower() and value: 
            value = clean_date(value)
        v = clean_text(str(value)) if value else "—"
        data.append([Paragraph(label, styles["label"]), Paragraph(v, styles["table_cell"])])
        
    t = Table(data, colWidths=[5 * cm, PAGE_W - 2 * MARGIN - 5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))
    return t

def milestone_table(milestones_raw, styles):
    rows = parse_milestones(milestones_raw)
    if not rows: 
        return [Paragraph("— Milestone schedule to be agreed and appended as Exhibit A", styles["missing"])]
        
    data = [[
        Paragraph("Milestone", styles["table_header"]),
        Paragraph("Target Date", styles["table_header"]),
        Paragraph("Notes", styles["table_header"])
    ]]
    
    row_colors = []
    for i, row in enumerate(rows):
        data.append([
            Paragraph(clean_text(row.get("milestone", "")), styles["table_cell"]),
            Paragraph(row.get("date", "TBD"), styles["table_cell"]),
            Paragraph(row.get("notes", "") or "—", styles["table_cell"])
        ])
        row_colors.append(WHITE if i % 2 == 0 else LIGHT_GREY)
        
    col_w = PAGE_W - 2 * MARGIN
    t = Table(data, colWidths=[col_w * 0.45, col_w * 0.25, col_w * 0.30], repeatRows=1)
    
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), BLACK_PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBEFORE", (0, 1), (0, -1), 2, YELLOW_ACCENT)
    ]
    
    for i, color in enumerate(row_colors): 
        cmds.append(("BACKGROUND", (0, i + 1), (-1, i + 1), color))
        
    t.setStyle(TableStyle(cmds))
    return [t]

def dynamic_clause(number, title, extracted, fallback, styles, is_dynamic=False):
    text = clean_text(str(extracted)) if has_value(extracted) else fallback
    sk = "clause_dynamic" if (has_value(extracted) and is_dynamic) else "clause_number"
    tag = " ◆" if has_value(extracted) else ""
    return KeepTogether([
        Paragraph(f"{number}  {title}{tag}", styles[sk]),
        Paragraph(text, styles["body"]),
        Spacer(1, 6)
    ])


# ==========================================
# SECTION 6: DOCUMENT BODY GENERATORS
# ==========================================

def build_status_banner(canonical, styles):
    # ── Always recompute from live data — never trust stale reviewReason strings ──
    # reviewReason is written once at extraction time and becomes stale after
    # the user resolves conflicts or fills missing fields via regeneration.
    conflicts = canonical.get("conflicts", [])
    missing   = canonical.get("missingFields", [])

    # Recompute critical missing fields from the current (pruned) missingFields list
    critical = [
        f for f in missing
        if any(k in (f if isinstance(f, str) else f.get("field", ""))
               for k in ("client.name", "vendor.name", "effectiveDate"))
    ]

    # Derive live status: only "needs_review" if there are still unresolved
    # conflicts OR critical fields still missing — otherwise mark clean.
    has_issues = bool(conflicts) or bool(critical)

    elems = []

    if has_issues:
        # Build reason line from live counts — never from the stale reviewReason field
        live_reasons = []
        if conflicts:
            live_reasons.append(f"{len(conflicts)} field conflict{'s' if len(conflicts) != 1 else ''} found")
        if critical:
            live_reasons.append(f"Critical fields missing: {critical}")

        content = "<b>⚠ REQUIRES HUMAN REVIEW BEFORE USE</b>"
        if live_reasons:
            content += "<br/>" + "  ·  ".join(live_reasons)
        elems.append(info_box(content, styles, bg=AMBER_BG, border=AMBER))
    else:
        elems.append(info_box(
            "<b>✓ All conflicts resolved and critical fields present.</b>  "
            "Verify all fields before execution.",
            styles, bg=GREEN_BG, border=colors.HexColor("#059669")))

    # Critical missing fields red callout box (shown in addition to banner)
    if critical:
        elems.append(Spacer(1, 4))
        elems.append(info_box(
            "<b>Critical fields not found:</b>  " + ",  ".join(critical),
            styles, bg=RED_BG, border=RED))

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

def build_nda_body(canonical, styles):
    story = []
    parties = canonical.get("parties", {})
    dates = canonical.get("dates", {})
    conf = canonical.get("confidentiality", {})
    legal = canonical.get("legal", {})
    security = canonical.get("security", {})
    
    client = parties.get("client", {}).get("name", "")
    vendor = parties.get("vendor", {}).get("name", "")
    nda_type = parties.get("ndaType", "")

    # Contracting Parties
    story.append(Paragraph("1. CONTRACTING PARTIES", styles["h1"]))
    story += section_rule(styles)
    rows = [
        ("Disclosing Party", client or None),
        ("Receiving Party", vendor or None),
        ("NDA Type", nda_type.capitalize() if nda_type else None),
        ("Effective Date", dates.get("effectiveDate") or None),
        ("Expiration Date", dates.get("expirationDate") or None),
        ("Execution Date", dates.get("executionDate") or None)
    ]
    story.append(two_col_table(rows, styles))
    story.append(Spacer(1, 16))

    # Confidentiality Terms
    story.append(Paragraph("2. CONFIDENTIALITY TERMS", styles["h1"]))
    story += section_rule(styles)
    term = normalise_term(conf.get("term"))
    story.append(Paragraph("CONFIDENTIALITY TERM", styles["label"]))
    story.append(Paragraph(term if term else '<font color="#B45309"><b>⚠ MISSING — Review Required</b></font>', styles["value"]))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("Obligations", styles["h2"]))
    obligations = conf.get("obligations", [])
    if has_value(obligations): 
        story += bullet_list(obligations, styles)
    else: 
        story.append(Paragraph("The Receiving Party shall: (a) hold all Confidential Information in strict confidence using no less than reasonable care; (b) not disclose Confidential Information to any third party without prior written consent; (c) use Confidential Information solely for the Purpose defined herein; and (d) limit access to those employees or advisers with a need to know.", styles["body"]))
        
    story.append(Spacer(1, 8))
    story.append(Paragraph("Exceptions", styles["h2"]))
    exceptions = conf.get("exceptions", "")
    if has_value(exceptions): 
        story += bullet_list([e.strip() for e in str(exceptions).split(";") if e.strip()], styles)
    else: 
        story += bullet_list([
            "Information already in the public domain through no fault of the Receiving Party",
            "Information independently developed by the Receiving Party",
            "Information received from a third party without restriction",
            "Disclosure required by law or court order (with prompt notice to Disclosing Party)"
        ], styles)
    story.append(Spacer(1, 16))

    # Data Security & Privacy
    sec_req = security.get("requirements", "")
    data_res = security.get("dataResidency", "")
    personal = security.get("personalDataProcessing", "")
    ns = 3
    if has_value(sec_req) or has_value(data_res) or has_value(personal):
        story.append(Paragraph("3. DATA SECURITY & PRIVACY", styles["h1"]))
        story += section_rule(styles)
        story.append(two_col_table([
            ("Security Requirements", sec_req or None),
            ("Data Residency", data_res or None),
            ("Personal Data Processing", personal or None)
        ], styles))
        story.append(Spacer(1, 16))
        ns = 4

    # Legal & Jurisdiction
    story.append(Paragraph(f"{ns}. LEGAL & JURISDICTION", styles["h1"]))
    story += section_rule(styles)
    story.append(two_col_table([
        ("Governing Law", legal.get("governingLaw") or None),
        ("Jurisdiction", legal.get("jurisdiction") or None),
        ("Dispute Resolution", legal.get("disputeResolution") or None),
        ("MSA Reference", legal.get("msaReference") or None)
    ], styles))
    story.append(Spacer(1, 16))
    ns += 1

    # Standard Provisions
    story.append(Paragraph(f"{ns}. STANDARD PROVISIONS", styles["h1"]))
    story += section_rule(styles)
    story.append(Paragraph('<font size="7" color="#6B7280">◆ = populated from extracted contract data</font>', styles["section_tag"]))
    story.append(Spacer(1, 8))
    n = ns
    
    story.append(dynamic_clause(f"{n}.1", "Intellectual Property", legal.get("ipOwnership"), "Nothing in this Agreement grants the Receiving Party any intellectual property rights or licence in the Confidential Information beyond the limited Purpose stated herein. Pre-existing IP of each party remains solely owned by that party.", styles, is_dynamic=True))
    story.append(dynamic_clause(f"{n}.2", "Limitation of Liability", legal.get("liabilityCap"), "Neither party shall be liable to the other for any indirect, incidental, special, or consequential damages arising out of or in connection with this Agreement, even if advised of the possibility of such damages.", styles, is_dynamic=True))
    story.append(dynamic_clause(f"{n}.3", "Return or Destruction", None, "Upon written request by the Disclosing Party, the Receiving Party shall promptly return or destroy all Confidential Information and certify such destruction in writing within 10 business days.", styles))
    story.append(dynamic_clause(f"{n}.4", "Injunctive Relief", legal.get("injunctiveRelief"), "The parties acknowledge that breach of this Agreement may cause irreparable harm for which monetary damages would be inadequate, and that the Disclosing Party shall be entitled to seek equitable relief without posting bond or other security.", styles, is_dynamic=True))
    story.append(dynamic_clause(f"{n}.5", "Entire Agreement", None, "This Agreement constitutes the entire understanding between the parties with respect to its subject matter and supersedes all prior discussions, representations, and undertakings.", styles))
    story.append(dynamic_clause(f"{n}.6", "Amendments", None, "No amendment to this Agreement shall be effective unless made in writing and signed by authorised representatives of both parties.", styles))
    story.append(dynamic_clause(f"{n}.7", "Severability", None, "If any provision of this Agreement is found to be unenforceable, the remaining provisions shall continue in full force and effect.", styles))
    
    if has_value(legal.get("indemnities")): 
        story.append(dynamic_clause(f"{n}.8", "Indemnities", legal.get("indemnities"), "", styles, is_dynamic=True))
        
    return story

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

    # Dispute Resolution fallback
    dispute = legal.get("disputeResolution", "")
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
        if isinstance(oos, str):
            oos = [i.strip() for i in re.split(r'\n|;;', oos) if i.strip()]
        story += bullet_list(oos, styles)

    story.append(Spacer(1, 8))
    story.append(Paragraph("2.3  Milestones", styles["h2"]))
    story += milestone_table(scope.get("milestones", []), styles)

    # 2.4 Project Schedule — extracted timeline first, then milestone-derived bullets
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
    data_res_display = data_res
    if has_value(data_res) and "preferred" in str(data_res).lower():
        data_res_display = (
            re.sub(r'\s*preferred', '', str(data_res), flags=re.IGNORECASE).strip()
            + " [To be confirmed as binding requirement before execution]"
        )
    personal_dp = security.get("personalDataProcessing", "")
    ns = 4

    if has_value(sec_req) or has_value(compliance) or has_value(privacy):
        story.append(Paragraph("4. SECURITY & COMPLIANCE", styles["h1"]))
        story += section_rule(styles)
        story.append(two_col_table([
            ("Security Requirements",    sec_req or None),
            ("Compliance Standards",     compliance or None),
            ("Data Residency",           data_res_display or None),
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
    story.append(Spacer(1, 4))
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

def build_signature_block(canonical, styles):
    parties = canonical.get("parties", {})
    client = parties.get("client", {}).get("name", "CLIENT")
    vendor = parties.get("vendor", {}).get("name", "VENDOR")
    signers = parties.get("client", {}).get("signatories", [])
    
    story = [
        PageBreak(),
        Paragraph("EXECUTION & SIGNATURES", styles["h1"]),
        HRFlowable(width="100%", thickness=0.5, color=YELLOW_ACCENT, spaceAfter=16),
        Paragraph("IN WITNESS WHEREOF the parties have executed this Agreement as of the Effective Date first written above.", styles["body"]),
        Spacer(1, 24)
    ]
    
    cn = signers[0].get("name", "") if signers else ""
    ct = signers[0].get("title", "") if signers else ""
    vs = signers[1] if len(signers) > 1 else {}
    
    def sl(label, prefill=""): 
        return Paragraph(f"{label}: {prefill if prefill else '___________________________'}", styles["body"])
        
    sig_data = [
        [Paragraph(f"<b>{client}</b>", styles["body_bold"]), Paragraph(f"<b>{vendor}</b>", styles["body_bold"])],
        [Spacer(1, 32), Spacer(1, 32)],
        [sl("Signature"), sl("Signature")],
        [sl("Name", cn), sl("Name", vs.get("name", ""))],
        [sl("Title", ct), sl("Title", vs.get("title", ""))],
        [sl("Date"), sl("Date")]
    ]
    
    col = (PAGE_W - 2 * MARGIN - 1 * cm) / 2
    t = Table(sig_data, colWidths=[col, col])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, BORDER),
        ("LEFTPADDING", (1, 0), (1, -1), 20)
    ]))
    
    story.append(t)
    return story

def conflict_table(conflicts, styles):
    if not conflicts: 
        return []
        
    elems = [Paragraph("CONFLICT RESOLUTION LOG", styles["h2"]), *section_rule(styles)]
    data = [[
        Paragraph("Field", styles["table_header"]),
        Paragraph("Chosen Value", styles["table_header"]),
        Paragraph("Source", styles["table_header"]),
        Paragraph("Overridden", styles["table_header"])
    ]]
    
    for c in conflicts:
        alt_str = "; ".join(f"{a.get('source', '?')}: {str(a.get('value', ''))[:40]}" for a in c.get("alternatives", []))
        data.append([
            Paragraph(c.get("field", ""), styles["table_cell"]),
            Paragraph(str(c.get("chosen", ""))[:80], styles["table_cell"]),
            Paragraph(c.get("chosenSource", ""), styles["table_cell"]),
            Paragraph(alt_str or "—", styles["table_cell"])
        ])
        
    col_w = PAGE_W - 2 * MARGIN
    t = Table(data, colWidths=[col_w * 0.22, col_w * 0.32, col_w * 0.16, col_w * 0.30])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK_PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))
    
    elems.append(t)
    elems.append(Spacer(1, 12))
    return elems

def provenance_table(provenance, styles):
    if not provenance: 
        return []
        
    elems = [Paragraph("PROVENANCE AUDIT TRAIL", styles["h2"]), *section_rule(styles)]
    data = [[
        Paragraph("Canonical Field", styles["table_header"]),
        Paragraph("Extracted Value", styles["table_header"]),
        Paragraph("Source Analyzer", styles["table_header"]),
        Paragraph("Confidence", styles["table_header"])
    ]]
    
    for p in provenance:
        conf = p.get("confidence", 0)
        if conf >= 0.8: 
            ct = f'<font color="#065F46"><b>{conf:.0%}</b></font>'
        elif conf >= 0.6: 
            ct = f'<font color="#B45309"><b>{conf:.0%}</b></font>'
        else: 
            ct = f'<font color="#991B1B"><b>{conf:.0%} ⚠</b></font>'
            
        val = str(p.get("value", ""))
        if len(val) > 80: 
            val = val[:77] + "..."
            
        data.append([
            Paragraph(p.get("canonicalPath", ""), styles["table_cell"]),
            Paragraph(val, styles["table_cell"]),
            Paragraph(p.get("sourceField", ""), styles["table_cell"]),
            Paragraph(ct, styles["table_cell"])
        ])
        
    col_w = PAGE_W - 2 * MARGIN
    t = Table(data, colWidths=[col_w * 0.25, col_w * 0.40, col_w * 0.20, col_w * 0.15], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK_PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))
    
    elems.append(t)
    return elems

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

        if important_missing:
            story.append(Paragraph("Missing Fields", styles["h2"]))
            story += section_rule(styles)
            story += bullet_list(important_missing, styles)
            story.append(Spacer(1, 12))

    story += conflict_table(canonical.get("conflicts", []), styles)
    story.append(Spacer(1, 8))
    story += provenance_table(canonical.get("provenance", []), styles)
    return story

# ==========================================
# SECTION 7: MAIN GENERATION ORCHESTRATION
# ==========================================

def generate_pdf(canonical: dict, doc_type: str, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    parties = canonical.get("parties", {})
    client = parties.get("client", {}).get("name", "CLIENT")
    vendor = parties.get("vendor", {}).get("name", "VENDOR")
    status = canonical.get("review", {}).get("status", "needs_review")
    doc_label = "NDA" if doc_type == "nda" else "SOW"
    
    pt = ContractPageTemplate(
        doc_type=doc_label, 
        client=client, 
        vendor=vendor, 
        generated_at=generated_at, 
        review_status=status
    )
    
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4, 
        leftMargin=MARGIN, 
        rightMargin=MARGIN,
        topMargin=MARGIN + 10 * mm, 
        bottomMargin=MARGIN + 5 * mm,
        title=f"{doc_label} — {client} × {vendor}", 
        author="Contract Intelligence Pipeline",
        subject=f"AI-Assisted {doc_label} Draft", 
        creator="contract-intelligence-platform"
    )
    
    story = []
    story += build_cover(canonical, doc_type, styles, generated_at)
    story += build_status_banner(canonical, styles)
    
    if doc_type == "nda": 
        story += build_nda_body(canonical, styles)
    else: 
        story += build_sow_body(canonical, styles)
        
    risks = canonical.get("risks")
    if has_value(risks):
        story.append(Spacer(1, 16))
        story.append(Paragraph("IDENTIFIED RISKS & OPEN ITEMS", styles["h1"]))
        story += section_rule(styles)
        risks_text = "\n".join(f"- {r}" for r in risks if str(r).strip()) if isinstance(risks, list) else str(risks)
        story.append(info_box(risks_text, styles, bg=AMBER_BG, border=AMBER, title="Risk Register"))
        
    story += build_signature_block(canonical, styles)
    story += build_appendix(canonical, styles, doc_type=doc_type)
    
    doc.build(story, onFirstPage=pt, onLaterPages=pt)
    log.info(f"[Generator] PDF written: {output_path}")
    
    return str(Path(output_path).resolve())


# ==========================================
# SECTION 8: CLI ENTRY POINT
# ==========================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Generate enterprise contract PDF from canonical JSON")
    parser.add_argument("--input", required=True)
    parser.add_argument("--type", required=True, choices=["nda", "sow"])
    parser.add_argument("--output", required=True)
    
    args = parser.parse_args()
    
    with open(args.input) as f: 
        canonical = json.load(f)
        
    print(f"Generated: {generate_pdf(canonical, args.type, args.output)}")