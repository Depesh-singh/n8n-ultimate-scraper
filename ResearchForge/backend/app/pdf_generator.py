import os
import re
import html
import logging
from io import BytesIO
from typing import List, Dict
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

class NumberedCanvas(canvas.Canvas):
    """Canvas that adds page numbers, running header, and footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header rule & text on pages > 1
        if self._pageNumber > 1:
            self.drawString(54, 755, "L&T Technology Services • Techgium Official Problem Statements Compendium")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(54, 747, 558, 747)
            
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_text)
        self.drawString(54, 36, "Compiled by Personal Researcher AI Agent • Confidential Academic & Engineering Reference")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(54, 48, 558, 48)
        self.restoreState()


def sanitize_for_pdf(text: str) -> str:
    """Sanitizes text for safe rendering in ReportLab Flowables."""
    if not text:
        return ""
    
    # Normalize unicode quotes and dashes
    text = str(text)
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u2013', '-').replace('\u2014', '--')
    text = text.replace('\u2026', '...')
    # Replace broken or bullet unicode characters
    text = text.replace('\ufffd', '&bull; ')
    text = text.replace('\uf0b7', '&bull; ')
    text = text.replace('\u2022', '&bull; ')
    text = text.replace('\t', '    ')

    # Convert newlines to HTML break
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Convert leading bullet dash or bullet character
        if stripped.startswith(('•', '-', '*')) and not stripped.startswith('**'):
            stripped = f"&bull; {stripped[1:].strip()}"
        cleaned_lines.append(stripped)

    joined = "<br/>".join(cleaned_lines)
    # Ensure ampersands that aren't entities are escaped
    joined = re.sub(r'&(?!(?:amp|lt|gt|bull|quot|apos|#\d+);)', '&amp;', joined)
    return joined


def generate_problem_statements_pdf(challenges: List[Dict], output_path: str = None) -> bytes:
    """
    Generates a professional multi-page PDF compilation of Techgium problem statements.
    Returns bytes and optionally writes to output_path.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=20
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=8
    )
    
    challenge_title = ParagraphStyle(
        'ChallengeTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155")
    )

    body_lead = ParagraphStyle(
        'CustomBodyLead',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b")
    )
    
    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a")
    )
    
    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#ffffff"),
        alignment=1
    )

    story = []

    # ==================== COVER / HEADER ====================
    story.append(Spacer(1, 25))
    story.append(Paragraph("TECHGIUM OFFICIAL PROBLEM STATEMENTS", title_style))
    story.append(Paragraph(
        f"L&T Technology Services Engineering Innovation Challenge Compendium<br/>"
        f"<b>{len(challenges)} Problem Statements</b> Across All Competition Tracks • Generated: {datetime.now().strftime('%B %d, %Y')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=15))

    # ==================== DOMAIN BREAKDOWN SUMMARY ====================
    domains_count = {}
    for c in challenges:
        d = str(c.get("domain") or c.get("category") or "General").strip()
        domains_count[d] = domains_count.get(d, 0) + 1

    summary_rows = [["Engineering Track / Domain", "Challenge Count", "% of Total"]]
    total_count = len(challenges) if challenges else 1
    for d, cnt in sorted(domains_count.items(), key=lambda x: x[1], reverse=True):
        pct = f"{(cnt / total_count) * 100:.1f}%"
        summary_rows.append([d, str(cnt), pct])
    summary_rows.append(["Total Official Problem Statements", str(len(challenges)), "100.0%"])

    summary_table = Table(summary_rows, colWidths=[260, 120, 124])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor("#f8fafc"), colors.white]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # ==================== TABLE OF CONTENTS / SUMMARY ====================
    story.append(Paragraph("Index of Challenges", section_heading))
    
    toc_data = [["#", "Domain", "Problem Statement Title"]]
    for idx, c in enumerate(challenges):
        title = str(c.get("title") or c.get("challengeTitle") or "Untitled Challenge").strip()
        domain = str(c.get("domain") or c.get("category") or "General").strip()
        toc_data.append([
            str(idx + 1),
            Paragraph(f"<b>{domain}</b>", body_style),
            Paragraph(sanitize_for_pdf(title), body_style)
        ])

    toc_table = Table(toc_data, colWidths=[28, 136, 340])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # ==================== DETAILED PROBLEM STATEMENTS ====================
    domain_color_map = {
        "Manufacturing": "#0284c7",
        "AI": "#7c3aed",
        "MedTech": "#059669",
        "Energy": "#d97706",
        "Cyber Security": "#dc2626",
        "Mobility": "#ea580c",
        "Digital Platforms": "#4f46e5",
        "Robotics & Autonomous Systems": "#0891b2",
        "Sustainability": "#16a34a"
    }

    for idx, c in enumerate(challenges):
        cid = str(c.get("_id") or c.get("challengeId") or f"TECH-{idx+1:02d}")
        title = str(c.get("title") or c.get("challengeTitle") or "Untitled Challenge").strip()
        domain = str(c.get("domain") or c.get("category") or "Engineering").strip()
        
        # Primary content fields
        background = str(c.get("background") or "").strip()
        challenge_desc = str(c.get("challenge") or c.get("description") or c.get("problemStatement") or "").strip()
        deliverables = str(c.get("deliverables") or c.get("expectedOutput") or "").strip()
        constraints = str(c.get("constraints") or "").strip()

        badge_color = domain_color_map.get(domain, "#2563eb")

        challenge_block = []

        # Top Bar: ID and Domain Badge
        header_table = Table(
            [[
                Paragraph(f"<b>PROBLEM STATEMENT #{idx+1} &bull; REF: {cid[:16]}</b>", label_style),
                Paragraph(f"<b>{domain.upper()}</b>", badge_style)
            ]],
            colWidths=[360, 144]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#f8fafc")),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor(badge_color)),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        challenge_block.append(header_table)
        challenge_block.append(Spacer(1, 6))

        # Title
        challenge_block.append(Paragraph(sanitize_for_pdf(title), challenge_title))
        challenge_block.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        # 1. Background & Context
        if background:
            challenge_block.append(Paragraph("<b>1. Background & Industrial Context:</b>", label_style))
            challenge_block.append(Spacer(1, 3))
            challenge_block.append(Paragraph(sanitize_for_pdf(background), body_lead))
            challenge_block.append(Spacer(1, 8))

        # 2. Challenge Statement
        if challenge_desc:
            challenge_block.append(Paragraph("<b>2. Challenge Statement:</b>", label_style))
            challenge_block.append(Spacer(1, 3))
            challenge_block.append(Paragraph(sanitize_for_pdf(challenge_desc), body_style))
            challenge_block.append(Spacer(1, 8))

        # 3. Expected Deliverables
        if deliverables:
            challenge_block.append(Paragraph("<b>3. Expected Deliverables & Outcomes:</b>", label_style))
            challenge_block.append(Spacer(1, 3))
            challenge_block.append(Paragraph(sanitize_for_pdf(deliverables), body_style))
            challenge_block.append(Spacer(1, 8))

        # 4. Constraints if present
        if constraints:
            challenge_block.append(Paragraph("<b>4. Scope & Technical Constraints:</b>", label_style))
            challenge_block.append(Spacer(1, 3))
            challenge_block.append(Paragraph(sanitize_for_pdf(constraints), body_style))
            challenge_block.append(Spacer(1, 8))

        story.append(KeepTogether(challenge_block))
        
        # Divider between challenges
        if idx < len(challenges) - 1:
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceBefore=8, spaceAfter=16))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"Generated problem statements PDF saved to: {output_path}")

    return pdf_bytes
