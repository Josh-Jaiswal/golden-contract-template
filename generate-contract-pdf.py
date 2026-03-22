"""
generate_contract_pdf.py
─────────────────────────
Enterprise-grade PDF contract generator.
Takes a canonical contract package JSON and produces a
professionally formatted NDA or SOW PDF document.

Usage:
    python generation/generate_contract_pdf.py \
        --input tests/output/canonical-result.json \
        --type nda \
        --output tests/output/generated-nda.pdf

    python generation/generate_contract_pdf.py \
        --input tests/output/canonical-result.json \
        --type sow \
        --output tests/output/generated-sow.pdf
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

log = logging.getLogger(__name__)

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0D1B2A")
SLATE      = colors.HexColor("#1B3A5C")
ACCENT     = colors.HexColor("#2D6DB5")
LIGHT_BLUE = colors.HexColor("#EBF3FB")
MID_GREY   = colors.HexColor("#6B7280")
LIGHT_GREY = colors.HexColor("#F3F4F6")
BORDER     = colors.HexColor("#D1D5DB")
WHITE      = colors.white
BLACK      = colors.HexColor("#111827")
AMBER      = colors.HexColor("#B45309")
AMBER_BG   = colors.HexColor("#FFFBEB")
RED        = colors.HexColor("#991B1B")
RED_BG     = colors.HexColor("#FEF2F2")
GREEN      = colors.HexColor("#065F46")
GREEN_BG   = colors.HexColor("#ECFDF5")

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm


# ── Style registry ────────────────────────────────────────────────────────────
def build_styles() -> dict:
    base = getSampleStyleSheet()

    def S(name, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, **kw)

    return {
        "cover_client": S("cover_client",
            fontName="Helvetica-Bold", fontSize=22,
            textColor=WHITE, leading=28, alignment=TA_CENTER),

        "cover_vendor": S("cover_vendor",
            fontName="Helvetica", fontSize=14,
            textColor=colors.HexColor("#BFD7ED"), leading=20,
            alignment=TA_CENTER),

        "cover_doctype": S("cover_doctype",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=colors.HexColor("#7FB3D3"), leading=14,
            alignment=TA_CENTER, spaceAfter=4),

        "cover_meta": S("cover_meta",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#9DC3D8"), leading=13,
            alignment=TA_CENTER),

        "cover_status_needs_review": S("cover_status_needs_review",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=AMBER, leading=12, alignment=TA_CENTER),

        "cover_status_auto": S("cover_status_auto",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=colors.HexColor("#86EFAC"), leading=12,
            alignment=TA_CENTER),

        "h1": S("h1",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=NAVY, leading=18,
            spaceBefore=18, spaceAfter=6),

        "h2": S("h2",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=SLATE, leading=14,
            spaceBefore=12, spaceAfter=4),

        "body": S("body",
            fontName="Helvetica", fontSize=9,
            textColor=BLACK, leading=14,
            spaceBefore=2, spaceAfter=2,
            alignment=TA_JUSTIFY),

        "body_bold": S("body_bold",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=BLACK, leading=14),

        "label": S("label",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=MID_GREY, leading=11,
            spaceAfter=1),

        "value": S("value",
            fontName="Helvetica", fontSize=9,
            textColor=BLACK, leading=13,
            spaceAfter=6),

        "bullet": S("bullet",
            fontName="Helvetica", fontSize=9,
            textColor=BLACK, leading=13,
            leftIndent=14, firstLineIndent=-8,
            spaceBefore=1, spaceAfter=1),

        "missing": S("missing",
            fontName="Helvetica-Oblique", fontSize=8,
            textColor=colors.HexColor("#9CA3AF"), leading=12),

        "footer": S("footer",
            fontName="Helvetica", fontSize=7,
            textColor=MID_GREY, leading=10,
            alignment=TA_CENTER),

        "table_header": S("table_header",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=WHITE, leading=11),

        "table_cell": S("table_cell",
            fontName="Helvetica", fontSize=8,
            textColor=BLACK, leading=11),

        "confidence_high": S("confidence_high",
            fontName="Helvetica-Bold", fontSize=7,
            textColor=GREEN, leading=10),

        "confidence_med": S("confidence_med",
            fontName="Helvetica-Bold", fontSize=7,
            textColor=AMBER, leading=10),

        "confidence_low": S("confidence_low",
            fontName="Helvetica-Bold", fontSize=7,
            textColor=RED, leading=10),

        "clause_number": S("clause_number",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=ACCENT, leading=13),

        "watermark_draft": S("watermark_draft",
            fontName="Helvetica-Bold", fontSize=52,
            textColor=colors.HexColor("#F3F4F6"),
            alignment=TA_CENTER),
    }


# ── Page template with header/footer ─────────────────────────────────────────
class ContractPageTemplate:
    """Adds header rule and footer to every page via onPage callback."""

    def __init__(self, doc_type: str, client: str, vendor: str,
                 generated_at: str, review_status: str):
        self.doc_type = doc_type
        self.client = client
        self.vendor = vendor
        self.generated_at = generated_at
        self.review_status = review_status

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        # ── Top rule ──
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(WHITE)
        canvas.drawString(MARGIN, h - 10*mm,
            f"{self.doc_type}  ·  {self.client}  ×  {self.vendor}")

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#9DC3D8"))
        canvas.drawRightString(w - MARGIN, h - 10*mm,
            f"CONFIDENTIAL  ·  Page {doc.page}")

        # ── Bottom rule ──
        canvas.setFillColor(BORDER)
        canvas.rect(0, 0, w, 8*mm, fill=1, stroke=0)

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MID_GREY)
        canvas.drawString(MARGIN, 2.5*mm,
            f"Generated: {self.generated_at}  ·  AI-Assisted Draft — Not Legal Advice")
        canvas.drawRightString(w - MARGIN, 2.5*mm,
            f"Review Status: {self.review_status.upper()}")

        canvas.restoreState()


# ── Helper flowables ──────────────────────────────────────────────────────────
def section_rule(styles) -> list:
    """Thin accent rule under a section heading."""
    return [HRFlowable(width="100%", thickness=0.5,
                       color=ACCENT, spaceAfter=6)]


def field_row(label: str, value: Any, styles: dict,
              provenance: list = None, missing_ok: bool = False) -> list:
    """
    Render a labelled field. If value is empty/None:
    - If missing_ok → render greyed placeholder
    - Otherwise → render amber MISSING badge
    """
    elems = [Paragraph(label.upper(), styles["label"])]

    conf_str = ""
    if provenance and value:
        # Find confidence for this field
        canon_path = label.lower().replace(" ", ".")
        for p in provenance:
            if label.lower() in p.get("canonicalPath", "").lower():
                c = p.get("confidence", 0)
                if c >= 0.8:
                    style_key = "confidence_high"
                    icon = "●"
                elif c >= 0.6:
                    style_key = "confidence_med"
                    icon = "●"
                else:
                    style_key = "confidence_low"
                    icon = "●"
                conf_str = f"  {icon} {c:.0%}"
                break

    if value and str(value).strip():
        text = str(value).strip()
        if conf_str:
            elems.append(Paragraph(
                f'{text}<font size="7" color="#9CA3AF">{conf_str}</font>',
                styles["value"]))
        else:
            elems.append(Paragraph(text, styles["value"]))
    elif missing_ok:
        elems.append(Paragraph("— Not specified in source document",
                                styles["missing"]))
    else:
        elems.append(Paragraph(
            '<font color="#B45309"><b>⚠ MISSING — Review Required</b></font>',
            styles["value"]))

    return elems


def info_box(content: str, styles: dict,
             bg=LIGHT_BLUE, border=ACCENT, title: str = "") -> Table:
    """Coloured info box for notes, risks, summaries."""
    inner = []
    if title:
        inner.append(Paragraph(f"<b>{title}</b>", styles["body_bold"]))
        inner.append(Spacer(1, 3))
    inner.append(Paragraph(content, styles["body"]))

    t = Table([[inner]], colWidths=[PAGE_W - 2*MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), bg),
        ("LINEAFTER",   (0,0), (0,-1), 3, border),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING",(0,0), (-1,-1), 10),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
    ]))
    return t


def bullet_list(items, styles: dict) -> list:
    """Render a list of strings as bullet paragraphs."""
    elems = []
    if not items:
        return [Paragraph("— None identified", styles["missing"])]
    if isinstance(items, str):
        items = [i.strip() for i in items.split("\n") if i.strip()]
    for item in items:
        if item.strip():
            elems.append(Paragraph(f"• {item.strip()}", styles["bullet"]))
    return elems


def two_col_table(rows: list[tuple], styles: dict) -> Table:
    """Two-column key-value table."""
    data = []
    for label, value in rows:
        v = str(value).strip() if value else "—"
        data.append([
            Paragraph(label, styles["label"]),
            Paragraph(v, styles["table_cell"]),
        ])

    t = Table(data, colWidths=[5*cm, PAGE_W - 2*MARGIN - 5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), WHITE),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID",         (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
    ]))
    return t


def conflict_table(conflicts: list, styles: dict) -> list:
    """Render conflict resolution table."""
    if not conflicts:
        return []

    elems = [
        Paragraph("CONFLICT RESOLUTION LOG", styles["h2"]),
        *section_rule(styles),
    ]

    data = [[
        Paragraph("Field", styles["table_header"]),
        Paragraph("Chosen Value", styles["table_header"]),
        Paragraph("Source", styles["table_header"]),
        Paragraph("Overridden", styles["table_header"]),
    ]]

    for c in conflicts:
        chosen_val = str(c.get("chosen", ""))[:80]
        alternatives = c.get("alternatives", [])
        alt_str = "; ".join(
            f"{a.get('source','?')}: {str(a.get('value',''))[:40]}"
            for a in alternatives
        )
        data.append([
            Paragraph(c.get("field", ""), styles["table_cell"]),
            Paragraph(chosen_val, styles["table_cell"]),
            Paragraph(c.get("chosenSource", ""), styles["table_cell"]),
            Paragraph(alt_str or "—", styles["table_cell"]),
        ])

    col_w = PAGE_W - 2*MARGIN
    t = Table(data, colWidths=[
        col_w * 0.22, col_w * 0.32, col_w * 0.16, col_w * 0.30
    ])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), SLATE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID",         (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 12))
    return elems


def provenance_table(provenance: list, styles: dict) -> list:
    """Render full provenance audit trail."""
    if not provenance:
        return []

    elems = [
        Paragraph("PROVENANCE AUDIT TRAIL", styles["h2"]),
        *section_rule(styles),
    ]

    data = [[
        Paragraph("Canonical Field", styles["table_header"]),
        Paragraph("Extracted Value", styles["table_header"]),
        Paragraph("Source Analyzer", styles["table_header"]),
        Paragraph("Confidence", styles["table_header"]),
    ]]

    for p in provenance:
        conf = p.get("confidence", 0)
        if conf >= 0.8:
            conf_text = f'<font color="#065F46"><b>{conf:.0%}</b></font>'
        elif conf >= 0.6:
            conf_text = f'<font color="#B45309"><b>{conf:.0%}</b></font>'
        else:
            conf_text = f'<font color="#991B1B"><b>{conf:.0%} ⚠</b></font>'

        val = str(p.get("value", ""))
        if len(val) > 80:
            val = val[:77] + "..."

        data.append([
            Paragraph(p.get("canonicalPath", ""), styles["table_cell"]),
            Paragraph(val, styles["table_cell"]),
            Paragraph(p.get("sourceField", ""), styles["table_cell"]),
            Paragraph(conf_text, styles["table_cell"]),
        ])

    col_w = PAGE_W - 2*MARGIN
    t = Table(data, colWidths=[
        col_w * 0.28, col_w * 0.38, col_w * 0.18, col_w * 0.16
    ])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID",         (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
    ]))
    elems.append(t)
    return elems


# ── Cover page ────────────────────────────────────────────────────────────────
class NavyCoverPage(Flowable):
    """Full-bleed navy cover page drawn directly on canvas."""

    def __init__(self, client, vendor, doc_label, eff_date,
                 generated_at, status):
        super().__init__()
        self.client      = client
        self.vendor      = vendor
        self.doc_label   = doc_label
        self.eff_date    = eff_date
        self.generated_at = generated_at
        self.status      = status
        self.width       = PAGE_W
        self._avail_w    = 0
        self._avail_h    = 0
        self.height      = PAGE_H

    def wrap(self, availWidth, availHeight):
        self._avail_w = availWidth
        self._avail_h = availHeight
        return (availWidth, availHeight)

    def draw(self):
        c = self.canv
        w, h = PAGE_W, PAGE_H

        # Navy background — full page
        c.setFillColor(NAVY)
        c.rect(-MARGIN, -MARGIN - 10*mm, w, h + MARGIN + 10*mm,
               fill=1, stroke=0)

        # Accent stripe
        c.setFillColor(ACCENT)
        c.rect(-MARGIN, h * 0.38, w, 3, fill=1, stroke=0)

        cy = h * 0.62

        # Doc type label
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor("#7FB3D3"))
        c.drawCentredString(w/2 - MARGIN, cy + 80, self.doc_label)

        # Client name
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(WHITE)
        # Truncate if too long
        client = self.client if len(self.client) < 45 else self.client[:42] + "…"
        c.drawCentredString(w/2 - MARGIN, cy + 40, client)

        # Times symbol
        c.setFont("Helvetica", 16)
        c.setFillColor(colors.HexColor("#7FB3D3"))
        c.drawCentredString(w/2 - MARGIN, cy + 10, "×")

        # Vendor name
        c.setFont("Helvetica", 16)
        c.setFillColor(colors.HexColor("#BFD7ED"))
        vendor = self.vendor if len(self.vendor) < 50 else self.vendor[:47] + "…"
        c.drawCentredString(w/2 - MARGIN, cy - 20, vendor)

        # Metadata
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#9DC3D8"))
        c.drawCentredString(w/2 - MARGIN, cy - 60,
            f"Effective Date: {self.eff_date or 'TBD'}    ·    Generated: {self.generated_at}")

        # Status badge
        badge_color = colors.HexColor("#B45309") \
            if self.status == "needs_review" \
            else colors.HexColor("#059669")
        badge_text = "⚠  REQUIRES REVIEW BEFORE USE" \
            if self.status == "needs_review" \
            else "✓  AUTO-EXTRACTED"

        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(badge_color)
        c.drawCentredString(w/2 - MARGIN, cy - 82, badge_text)

        # Confidential footer
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#4A6FA5"))
        c.drawCentredString(w/2 - MARGIN, 20,
            "CONFIDENTIAL  ·  AI-ASSISTED DRAFT  ·  NOT LEGAL ADVICE  ·  NOT EXECUTED")


def build_cover(canonical: dict, doc_type: str, styles: dict,
                generated_at: str) -> list:
    parties  = canonical.get("parties", {})
    client   = parties.get("client", {}).get("name", "CLIENT")
    vendor   = parties.get("vendor", {}).get("name", "VENDOR")
    status   = canonical.get("review", {}).get("status", "needs_review")
    eff_date = canonical.get("dates", {}).get("effectiveDate", "")
    doc_label = "NON-DISCLOSURE AGREEMENT" if doc_type == "nda" else "STATEMENT OF WORK"

    return [
        NavyCoverPage(client, vendor, doc_label,
                      eff_date, generated_at, status),
        PageBreak(),
    ]


# ── Review status banner ──────────────────────────────────────────────────────
def build_status_banner(canonical: dict, styles: dict) -> list:
    review  = canonical.get("review", {})
    status  = review.get("status", "needs_review")
    reasons = review.get("reviewReason", [])
    missing = canonical.get("missingFields", [])

    elems = []

    if status == "needs_review":
        content = "<b>⚠ REQUIRES HUMAN REVIEW BEFORE USE</b>"
        if reasons:
            content += "<br/>" + "  ·  ".join(reasons)
        elems.append(info_box(content, styles, bg=AMBER_BG, border=AMBER))
    else:
        elems.append(info_box(
            "<b>✓ Auto-extracted with no conflicts detected.</b>  "
            "Verify all fields before execution.",
            styles, bg=GREEN_BG, border=colors.HexColor("#059669")))

    if missing:
        critical = [f for f in missing if any(
            k in f for k in ("client.name", "vendor.name", "effectiveDate")
        )]
        if critical:
            elems.append(Spacer(1, 4))
            elems.append(info_box(
                "<b>Critical fields not found in source document:</b>  " +
                ",  ".join(critical),
                styles, bg=RED_BG, border=RED))

    elems.append(Spacer(1, 12))
    return elems


# ── NDA document body ─────────────────────────────────────────────────────────
def build_nda_body(canonical: dict, styles: dict) -> list:
    story = []
    parties   = canonical.get("parties", {})
    dates     = canonical.get("dates", {})
    conf      = canonical.get("confidentiality", {})
    legal     = canonical.get("legal", {})
    provenance = canonical.get("provenance", [])

    client = parties.get("client", {}).get("name", "")
    vendor = parties.get("vendor", {}).get("name", "")

    # ── 1. Parties ────────────────────────────────────────────────────────
    story.append(Paragraph("1. CONTRACTING PARTIES", styles["h1"]))
    story += section_rule(styles)

    rows = [
        ("Disclosing Party",  client or None),
        ("Receiving Party",   vendor or None),
        ("Effective Date",    dates.get("effectiveDate") or None),
        ("Expiration Date",   dates.get("expirationDate") or None),
        ("Execution Date",    dates.get("executionDate") or None),
    ]
    story.append(two_col_table(rows, styles))
    story.append(Spacer(1, 16))

    # ── 2. Confidentiality ────────────────────────────────────────────────
    story.append(Paragraph("2. CONFIDENTIALITY TERMS", styles["h1"]))
    story += section_rule(styles)

    story += field_row("Confidentiality Term",
                       conf.get("term"), styles, provenance)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Obligations", styles["h2"]))
    obligations = conf.get("obligations", [])
    if obligations:
        story += bullet_list(obligations, styles)
    else:
        story.append(Paragraph(
            "The Receiving Party shall: (a) hold all Confidential Information "
            "in strict confidence using no less than reasonable care; "
            "(b) not disclose Confidential Information to any third party "
            "without prior written consent; (c) use Confidential Information "
            "solely for the Purpose defined herein; and (d) limit access to "
            "those employees or advisers with a need to know.",
            styles["body"]))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Exceptions", styles["h2"]))
    exceptions = conf.get("exceptions", "")
    if exceptions:
        story += bullet_list(
            [e.strip() for e in str(exceptions).split(";") if e.strip()],
            styles)
    else:
        story += bullet_list([
            "Information already in the public domain through no fault of the Receiving Party",
            "Information independently developed by the Receiving Party",
            "Information received from a third party without restriction",
            "Disclosure required by law or court order (with prompt notice to Disclosing Party)",
        ], styles)

    story.append(Spacer(1, 16))

    # ── 3. Legal ──────────────────────────────────────────────────────────
    story.append(Paragraph("3. LEGAL & JURISDICTION", styles["h1"]))
    story += section_rule(styles)

    rows = [
        ("Governing Law",        legal.get("governingLaw") or None),
        ("Jurisdiction",         legal.get("jurisdiction") or None),
        ("Dispute Resolution",   legal.get("disputeResolution") or None),
    ]
    story.append(two_col_table(rows, styles))
    story.append(Spacer(1, 16))

    # ── 4. Standard NDA clauses ───────────────────────────────────────────
    story.append(Paragraph("4. STANDARD PROVISIONS", styles["h1"]))
    story += section_rule(styles)

    clauses = [
        ("4.1  No Licence",
         "Nothing in this Agreement grants the Receiving Party any intellectual "
         "property rights or licence in the Confidential Information beyond the "
         "limited Purpose stated herein."),
        ("4.2  Return or Destruction",
         "Upon written request by the Disclosing Party, the Receiving Party shall "
         "promptly return or destroy all Confidential Information and certify such "
         "destruction in writing."),
        ("4.3  Injunctive Relief",
         "The parties acknowledge that breach of this Agreement may cause "
         "irreparable harm for which monetary damages would be inadequate, and "
         "that the Disclosing Party shall be entitled to seek equitable relief "
         "without posting bond."),
        ("4.4  Entire Agreement",
         "This Agreement constitutes the entire understanding between the parties "
         "with respect to its subject matter and supersedes all prior discussions, "
         "representations, and undertakings."),
        ("4.5  Amendments",
         "No amendment to this Agreement shall be effective unless made in writing "
         "and signed by authorised representatives of both parties."),
        ("4.6  Severability",
         "If any provision of this Agreement is found to be unenforceable, the "
         "remaining provisions shall continue in full force and effect."),
    ]

    for number, text in clauses:
        story.append(KeepTogether([
            Paragraph(number, styles["clause_number"]),
            Paragraph(text, styles["body"]),
            Spacer(1, 6),
        ]))

    return story


# ── SOW document body ─────────────────────────────────────────────────────────
def build_sow_body(canonical: dict, styles: dict) -> list:
    story = []
    parties    = canonical.get("parties", {})
    dates      = canonical.get("dates", {})
    scope      = canonical.get("scope", {})
    commercials = canonical.get("commercials", {})
    legal      = canonical.get("legal", {})
    provenance = canonical.get("provenance", [])

    client = parties.get("client", {}).get("name", "")
    vendor = parties.get("vendor", {}).get("name", "")

    # ── 1. Parties & Dates ────────────────────────────────────────────────
    story.append(Paragraph("1. CONTRACTING PARTIES & DATES", styles["h1"]))
    story += section_rule(styles)

    rows = [
        ("Client",          client or None),
        ("Vendor / Supplier", vendor or None),
        ("Effective Date",  dates.get("effectiveDate") or None),
        ("Term / Expiry",   dates.get("expirationDate") or None),
        ("Execution Date",  dates.get("executionDate") or None),
    ]
    story.append(two_col_table(rows, styles))
    story.append(Spacer(1, 16))

    # ── 2. Scope ──────────────────────────────────────────────────────────
    story.append(Paragraph("2. SCOPE OF WORK", styles["h1"]))
    story += section_rule(styles)

    description = scope.get("description", "")
    if description:
        story.append(info_box(description, styles,
                              bg=LIGHT_BLUE, border=ACCENT,
                              title="Project Summary"))
        story.append(Spacer(1, 8))

    story.append(Paragraph("2.1  Deliverables", styles["h2"]))
    story += bullet_list(scope.get("deliverables", []), styles)

    story.append(Spacer(1, 8))
    story.append(Paragraph("2.2  Milestones", styles["h2"]))
    milestones = scope.get("milestones", [])
    if milestones:
        story += bullet_list(milestones, styles)
    else:
        story.append(Paragraph(
            "— Milestone schedule to be agreed and appended as Exhibit A",
            styles["missing"]))

    story.append(Spacer(1, 16))

    # ── 3. Commercial Terms ───────────────────────────────────────────────
    story.append(Paragraph("3. COMMERCIAL TERMS", styles["h1"]))
    story += section_rule(styles)

    rows = [
        ("Total / Fee Structure", commercials.get("totalValue") or None),
        ("Payment Terms",        commercials.get("paymentTerms") or None),
        ("Currency",             commercials.get("currency") or None),
    ]
    story.append(two_col_table(rows, styles))
    story.append(Spacer(1, 16))

    # ── 4. Legal ──────────────────────────────────────────────────────────
    story.append(Paragraph("4. LEGAL & JURISDICTION", styles["h1"]))
    story += section_rule(styles)

    rows = [
        ("Governing Law",       legal.get("governingLaw") or None),
        ("Jurisdiction",        legal.get("jurisdiction") or None),
        ("Dispute Resolution",  legal.get("disputeResolution") or None),
    ]
    story.append(two_col_table(rows, styles))
    story.append(Spacer(1, 16))

    # ── 5. Standard SOW clauses ───────────────────────────────────────────
    story.append(Paragraph("5. STANDARD PROVISIONS", styles["h1"]))
    story += section_rule(styles)

    clauses = [
        ("5.1  Change Control",
         "Any change to the scope, timeline, or fees must be agreed in writing "
         "via a Change Request signed by authorised representatives of both "
         "parties prior to implementation."),
        ("5.2  Acceptance",
         "Each deliverable shall be subject to a written acceptance period of "
         "10 business days. Silence shall not constitute acceptance. The Client "
         "shall provide written acceptance or a detailed list of defects within "
         "the acceptance period."),
        ("5.3  Intellectual Property",
         "Unless otherwise agreed in writing, all work product created by the "
         "Vendor under this SOW shall be owned by the Client upon full payment "
         "of all fees. Pre-existing IP of either party is not transferred."),
        ("5.4  Limitation of Liability",
         "Neither party shall be liable for indirect, incidental, or consequential "
         "damages. Each party's aggregate liability under this SOW shall not "
         "exceed the total fees paid or payable in the preceding twelve months."),
        ("5.5  Termination for Convenience",
         "Either party may terminate this SOW with 30 days written notice. "
         "Upon termination the Client shall pay for all work completed to the "
         "date of termination on a pro-rata basis."),
        ("5.6  Confidentiality",
         "Each party shall treat all non-public information received from the "
         "other party as confidential and shall not disclose it to any third "
         "party without prior written consent, for the duration of this SOW "
         "and for two years thereafter."),
    ]

    for number, text in clauses:
        story.append(KeepTogether([
            Paragraph(number, styles["clause_number"]),
            Paragraph(text, styles["body"]),
            Spacer(1, 6),
        ]))

    return story


# ── Signature block ───────────────────────────────────────────────────────────
def build_signature_block(canonical: dict, styles: dict) -> list:
    parties = canonical.get("parties", {})
    client  = parties.get("client", {}).get("name", "CLIENT")
    vendor  = parties.get("vendor", {}).get("name", "VENDOR")

    story = [
        PageBreak(),
        Paragraph("EXECUTION & SIGNATURES", styles["h1"]),
        HRFlowable(width="100%", thickness=0.5,
                   color=ACCENT, spaceAfter=16),
        Paragraph(
            "IN WITNESS WHEREOF the parties have executed this Agreement "
            "as of the Effective Date first written above.",
            styles["body"]),
        Spacer(1, 24),
    ]

    sig_data = [
        [
            Paragraph(f"<b>{client}</b>", styles["body_bold"]),
            Paragraph(f"<b>{vendor}</b>", styles["body_bold"]),
        ],
        [Spacer(1, 32), Spacer(1, 32)],
        [
            Paragraph("Signature: ___________________________", styles["body"]),
            Paragraph("Signature: ___________________________", styles["body"]),
        ],
        [
            Paragraph("Name: _______________________________", styles["body"]),
            Paragraph("Name: _______________________________", styles["body"]),
        ],
        [
            Paragraph("Title: _______________________________", styles["body"]),
            Paragraph("Title: _______________________________", styles["body"]),
        ],
        [
            Paragraph("Date:  _______________________________", styles["body"]),
            Paragraph("Date:  _______________________________", styles["body"]),
        ],
    ]

    col = (PAGE_W - 2*MARGIN - 1*cm) / 2
    t = Table(sig_data, colWidths=[col, col], spaceBefore=0)
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LINEAFTER",     (0,0), (0,-1), 0.5, BORDER),
        ("LEFTPADDING",   (1,0), (1,-1), 20),
    ]))
    story.append(t)
    return story


# ── Appendix: Pipeline metadata ───────────────────────────────────────────────
def build_appendix(canonical: dict, styles: dict) -> list:
    story = [
        PageBreak(),
        Paragraph("APPENDIX A — PIPELINE METADATA", styles["h1"]),
        HRFlowable(width="100%", thickness=0.5,
                   color=ACCENT, spaceAfter=12),
        Paragraph(
            "This appendix is generated automatically by the contract "
            "intelligence pipeline. It documents the AI extraction process "
            "for audit and review purposes and forms no part of the "
            "contractual terms above.",
            styles["body"]),
        Spacer(1, 12),
    ]

    # Missing fields summary
    missing = canonical.get("missingFields", [])
    if missing:
        story.append(Paragraph("Missing Fields", styles["h2"]))
        story += section_rule(styles)
        story += bullet_list(missing, styles)
        story.append(Spacer(1, 12))

    # Conflicts
    story += conflict_table(canonical.get("conflicts", []), styles)

    # Provenance
    story.append(Spacer(1, 8))
    story += provenance_table(canonical.get("provenance", []), styles)

    return story


# ── Main generator ────────────────────────────────────────────────────────────
def generate_pdf(canonical: dict, doc_type: str, output_path: str) -> str:
    """
    Generate an enterprise-grade contract PDF from canonical data.

    Args:
        canonical:   Canonical contract package dict.
        doc_type:    "nda" or "sow"
        output_path: Where to write the PDF.

    Returns:
        Absolute path to the generated PDF.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    parties = canonical.get("parties", {})
    client  = parties.get("client", {}).get("name", "CLIENT")
    vendor  = parties.get("vendor", {}).get("name", "VENDOR")
    status  = canonical.get("review", {}).get("status", "needs_review")

    doc_label = "NDA" if doc_type == "nda" else "SOW"

    # Build page template callback
    page_template = ContractPageTemplate(
        doc_type=doc_label,
        client=client,
        vendor=vendor,
        generated_at=generated_at,
        review_status=status,
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 10*mm,
        bottomMargin=MARGIN + 5*mm,
        title=f"{doc_label} — {client} × {vendor}",
        author="Contract Intelligence Pipeline",
        subject=f"AI-Assisted {doc_label} Draft",
        creator="contract-intelligence-platform",
    )

    story = []

    # Cover
    story += build_cover(canonical, doc_type, styles, generated_at)

    # Review banner
    story += build_status_banner(canonical, styles)

    # Document body
    if doc_type == "nda":
        story += build_nda_body(canonical, styles)
    else:
        story += build_sow_body(canonical, styles)

    # Risks section (if present)
    risks = canonical.get("risks")
    if risks:
        story.append(Spacer(1, 16))
        story.append(Paragraph(
            "IDENTIFIED RISKS & OPEN ITEMS", styles["h1"]))
        story += section_rule(styles)
        story.append(info_box(
            str(risks), styles,
            bg=AMBER_BG, border=AMBER,
            title="Risk Register"))

    # Signatures
    story += build_signature_block(canonical, styles)

    # Appendix
    story += build_appendix(canonical, styles)

    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)

    log.info(f"[Generator] PDF written: {output_path}")
    return str(Path(output_path).resolve())


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Generate enterprise contract PDF from canonical JSON")
    parser.add_argument("--input",  required=True,
                        help="Path to canonical JSON file")
    parser.add_argument("--type",   required=True,
                        choices=["nda", "sow"],
                        help="Contract type to generate")
    parser.add_argument("--output", required=True,
                        help="Output PDF path")
    args = parser.parse_args()

    with open(args.input) as f:
        canonical = json.load(f)

    out = generate_pdf(canonical, args.type, args.output)
    print(f"Generated: {out}")
