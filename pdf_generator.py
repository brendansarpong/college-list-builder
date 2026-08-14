import io
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

styles = getSampleStyleSheet()

title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=22, spaceAfter=4)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=11, textColor=colors.grey, spaceAfter=20)
section_style = ParagraphStyle("Section", parent=styles["Heading2"], spaceBefore=18, spaceAfter=6, textColor=colors.HexColor("#1a3c6e"))
college_name_style = ParagraphStyle("CollegeName", parent=styles["Heading3"], spaceBefore=10, spaceAfter=2)
facts_style = ParagraphStyle("Facts", parent=styles["Normal"], fontSize=9, textColor=colors.grey, spaceAfter=4)
blurb_style = ParagraphStyle("Blurb", parent=styles["Normal"], fontSize=10.5, leading=14, spaceAfter=6)

SECTION_LABELS = {
    "reach": "Reach Schools",
    "target": "Target Schools",
    "safety": "Safety Schools",
}


def _facts_line(college):
    lo, hi = college["sat_range"]
    return f'{college["state"]} &nbsp;|&nbsp; {college["setting"].title()}, {college["size"]} school &nbsp;|&nbsp; SAT range {lo}-{hi}'


def build_pdf(student_name, list_by_category, blurbs):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)

    elements = []
    elements.append(Paragraph(f"College List: {student_name}", title_style))
    elements.append(Paragraph(f"Prepared {date.today().strftime('%B %d, %Y')}", subtitle_style))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc")))

    for category in ["reach", "target", "safety"]:
        colleges = list_by_category.get(category, [])
        if not colleges:
            continue
        elements.append(Paragraph(SECTION_LABELS[category], section_style))
        for college in colleges:
            name = college["name"]
            elements.append(Paragraph(name, college_name_style))
            elements.append(Paragraph(_facts_line(college), facts_style))
            blurb_text = blurbs.get(name, "")
            if blurb_text:
                elements.append(Paragraph(blurb_text, blurb_style))

    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc")))
    elements.append(Paragraph(
        "This list is a starting point for research and conversation, not a final decision. "
        "Talk to your counselor about next steps.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, spaceBefore=8),
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
