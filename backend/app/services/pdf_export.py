from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


def _safe_pdf_text(value: str) -> str:
    return escape(value.encode("latin-1", errors="replace").decode("latin-1"))


def create_summary_pdf(
    document_title: str,
    summary_type: str,
    summary_content: str,
    timezone_name: str = "UTC",
) -> bytes:
    """Create a clean summary PDF entirely in memory."""
    output = BytesIO()
    pdf = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"NEXUS AI Summary - {document_title}",
        author="NEXUS AI",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "NexusTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    metadata_style = ParagraphStyle(
        "NexusMetadata",
        parent=styles["Normal"],
        leading=15,
        textColor="#555555",
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "NexusBody",
        parent=styles["BodyText"],
        leading=16,
        spaceAfter=9,
    )

    try:
        user_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        user_timezone = ZoneInfo("UTC")
        timezone_name = "UTC"

    generated_at = datetime.now(user_timezone).strftime(
        "%Y-%m-%d %I:%M %p %Z"
    )
    story = [
        Paragraph("NEXUS AI Knowledge Summary", title_style),
        Paragraph(f"<b>Document:</b> {_safe_pdf_text(document_title)}", metadata_style),
        Paragraph(f"<b>Summary type:</b> {_safe_pdf_text(summary_type.replace('_', ' ').title())}", metadata_style),
        Paragraph(
            f"<b>Generated:</b> {generated_at} "
            f"({_safe_pdf_text(timezone_name)})",
            metadata_style,
        ),
        Spacer(1, 8),
    ]

    paragraphs = [part.strip() for part in summary_content.split("\n") if part.strip()]
    for paragraph in paragraphs:
        story.append(Paragraph(_safe_pdf_text(paragraph), body_style))

    story.extend(
        [
            Spacer(1, 12),
            Paragraph(
                "Generated locally by the NEXUS AI MVP extractive summarizer. "
                "Review important facts against the original document.",
                metadata_style,
            ),
        ]
    )

    pdf.build(story)
    return output.getvalue()
