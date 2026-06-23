"""Convert an IC Memo markdown string to a PDF using reportlab."""

from io import BytesIO


def generate_pdf_bytes(memo_markdown: str) -> bytes:
    """
    Render memo_markdown as a formatted PDF and return the raw bytes.

    Handles: # titles, ## headings, ### sub-headings, | tables |,
    - bullets, > blockquotes, blank lines, and body paragraphs.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            HRFlowable,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as e:
        raise RuntimeError(f"reportlab not installed: {e}")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "ICTitle",
            parent=base["Title"],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.HexColor("#1a1a2e"),
        ),
        "h1": ParagraphStyle(
            "ICH1",
            parent=base["Heading1"],
            fontSize=14,
            spaceBefore=14,
            spaceAfter=4,
            textColor=colors.HexColor("#16213e"),
            borderPad=2,
        ),
        "h2": ParagraphStyle(
            "ICH2",
            parent=base["Heading2"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=3,
            textColor=colors.HexColor("#0f3460"),
        ),
        "body": ParagraphStyle(
            "ICBody",
            parent=base["Normal"],
            fontSize=10,
            spaceAfter=4,
            leading=14,
        ),
        "bullet": ParagraphStyle(
            "ICBullet",
            parent=base["Normal"],
            fontSize=10,
            spaceAfter=3,
            leftIndent=16,
            leading=14,
            bulletIndent=6,
        ),
        "quote": ParagraphStyle(
            "ICQuote",
            parent=base["Normal"],
            fontSize=10,
            spaceAfter=4,
            leftIndent=20,
            leading=14,
            textColor=colors.HexColor("#555555"),
        ),
        "caption": ParagraphStyle(
            "ICCaption",
            parent=base["Normal"],
            fontSize=8,
            spaceAfter=4,
            textColor=colors.grey,
            fontName="Helvetica-Oblique",
        ),
        "th": ParagraphStyle(
            "ICTH",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        ),
        "td": ParagraphStyle(
            "ICTD",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
        ),
    }

    story = []
    lines = memo_markdown.split("\n")
    i = 0

    def _safe(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("**", "")
            .replace("*", "")
            .replace("`", "")
        )

    def _flush_table(table_lines: list) -> list:
        rows = []
        for tl in table_lines:
            if all(c in "-| :" for c in tl.replace(" ", "")):
                continue
            cells = [c.strip() for c in tl.strip().strip("|").split("|")]
            rows.append(cells)
        if not rows:
            return []
        max_cols = max(len(r) for r in rows)
        for r in rows:
            while len(r) < max_cols:
                r.append("")

        header_row = [[Paragraph(_safe(c), styles["th"]) for c in rows[0]]]
        body_rows = [[Paragraph(_safe(c), styles["td"]) for c in r] for r in rows[1:]]
        all_rows = header_row + body_rows

        col_width = (6.5 * inch) / max_cols
        t = Table(all_rows, colWidths=[col_width] * max_cols, repeatRows=1)
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        return [t, Spacer(1, 8)]

    pending_table: list = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Table row: collect until non-table line
        if stripped.startswith("|"):
            pending_table.append(stripped)
            i += 1
            continue

        # Flush any pending table
        if pending_table:
            story.extend(_flush_table(pending_table))
            pending_table = []

        if stripped.startswith("# "):
            story.append(Paragraph(_safe(stripped[2:]), styles["title"]))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#16213e")))
            story.append(Spacer(1, 6))

        elif stripped.startswith("## "):
            story.append(Paragraph(_safe(stripped[3:]), styles["h1"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6")))

        elif stripped.startswith("### "):
            story.append(Paragraph(_safe(stripped[4:]), styles["h2"]))

        elif stripped.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 4))

        elif stripped.startswith(("- ", "* ")):
            text = _safe(stripped[2:])
            story.append(Paragraph(f"• &nbsp;{text}", styles["bullet"]))

        elif stripped.startswith("> "):
            story.append(Paragraph(_safe(stripped[2:]), styles["quote"]))

        elif stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4:
            bold_text = _safe(stripped[2:-2])
            story.append(Paragraph(f"<b>{bold_text}</b>", styles["body"]))

        elif stripped == "":
            story.append(Spacer(1, 6))

        else:
            story.append(Paragraph(_safe(stripped), styles["body"]))

        i += 1

    if pending_table:
        story.extend(_flush_table(pending_table))

    doc.build(story)
    return buf.getvalue()
