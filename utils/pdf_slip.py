import json
import os
from functools import lru_cache
from io import BytesIO

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(APP_ROOT, "static", "GRACE_LOGISTICS_LOGO.png")
COMPANY_INFO_PATH = os.path.join(APP_ROOT, "static", "company_info.json")

BRAND_DARK = colors.HexColor("#4c3a8a")
BRAND_LIGHT = colors.HexColor("#667eea")
TEXT_MUTED = colors.HexColor("#6b7280")
ROW_ALT = colors.HexColor("#f8f9fa")
GREEN_ROW = colors.HexColor("#f0fdf4")
RED_TEXT = colors.HexColor("#dc2626")


@lru_cache(maxsize=1)
def _logo_reader():
    """Downscale the logo once (the source PNG is ~850KB) so it doesn't bloat every PDF."""
    if not os.path.isfile(LOGO_PATH):
        return None
    img = PILImage.open(LOGO_PATH).convert("RGB")
    img.thumbnail((260, 260), PILImage.LANCZOS)
    out = BytesIO()
    img.save(out, format="PNG", optimize=True)
    out.seek(0)
    return out.getvalue(), img.size


def _company_info():
    try:
        with open(COMPANY_INFO_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"name": "GRACE LOGISTICS", "slogan": "", "address": "", "phone": "", "email": ""}


def number_to_words(num):
    num = float(num)
    if num < 1000:
        return f"{int(num)} Rupees Only"
    elif num < 100000:
        thousands = int(num / 1000)
        remainder = int(num % 1000)
        if remainder > 0:
            return f"{thousands} Thousand {remainder} Rupees Only"
        return f"{thousands} Thousand Rupees Only"
    elif num < 10000000:
        lakhs = int(num / 100000)
        remainder = int(num % 100000)
        if remainder > 0:
            return f"{lakhs} Lakh {int(remainder / 1000)} Thousand {remainder % 1000} Rupees Only"
        return f"{lakhs} Lakh Rupees Only"
    else:
        crores = int(num / 10000000)
        remainder = int(num % 10000000)
        if remainder > 0:
            return f"{crores} Crore {int(remainder / 100000)} Lakh Rupees Only"
        return f"{crores} Crore Rupees Only"


def build_salary_pdf(salary, generated_date):
    """Render a branded, print-ready salary slip PDF for one driver and return it as bytes."""
    info = _company_info()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=f"Salary Slip - {salary['full_name']} - {salary['month']}",
    )
    styles = getSampleStyleSheet()
    elements = []

    company_name_style = ParagraphStyle(
        "CompanyName", parent=styles["Heading1"], fontSize=18, leading=21, textColor=colors.white, spaceAfter=0
    )
    slogan_style = ParagraphStyle(
        "Slogan", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#e0e0f5")
    )
    slip_title_style = ParagraphStyle(
        "SlipTitle", parent=styles["Normal"], fontSize=11, leading=14, textColor=colors.white, alignment=TA_RIGHT
    )

    company_block = [Paragraph(info.get("name", "GRACE LOGISTICS"), company_name_style)]
    if info.get("slogan"):
        company_block.append(Paragraph(info["slogan"].upper(), slogan_style))
    contact_bits = [v for v in (info.get("address"), info.get("phone"), info.get("email")) if v]
    if contact_bits:
        company_block.append(Paragraph(" &bull; ".join(contact_bits), slogan_style))

    logo_data = _logo_reader()
    if logo_data:
        logo_bytes, (logo_w, logo_h) = logo_data
        logo = Image(BytesIO(logo_bytes), width=22 * mm, height=22 * mm * (logo_h / logo_w))
    else:
        logo = Paragraph("", styles["Normal"])

    header_table = Table(
        [[logo, company_block, Paragraph("MONTHLY<br/>SALARY SLIP", slip_title_style)]],
        colWidths=[26 * mm, 105 * mm, 43 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (-1, 0), (-1, 0), 6),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 6 * mm))

    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9.5, leading=13)

    def cell(label, value):
        return Paragraph(f"<b>{label}:</b> {value}", label_style)

    details_table = Table(
        [
            [cell("Employee Name", salary["full_name"]), cell("License No", salary.get("license_no") or "N/A")],
            [
                cell("Assigned Vehicle", salary.get("assigned_vehicle") or "Not Assigned"),
                cell("Month", salary["month"]),
            ],
            [cell("Payment Date", salary["payment_date"]), cell("Payment Method", salary["payment_method"])],
        ],
        colWidths=[87 * mm, 87 * mm],
    )
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ROW_ALT),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(details_table)
    elements.append(Spacer(1, 6 * mm))

    def money(v):
        return f"{v:,.2f}"

    rows = [
        ["Description", "Amount (PKR)"],
        ["Base Salary", money(salary["base_salary"])],
        ["Bonus", f"+ {money(salary['bonus'])}"],
        ["Advance Deduction", f"- {money(salary['advance_deduction'])}"],
        ["Penalty", f"- {money(salary['penalty'])}"],
        ["Net Payable", f"{money(salary['net_payable'])} PKR"],
    ]
    salary_table = Table(rows, colWidths=[130 * mm, 44 * mm])
    salary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 2), (1, 2), colors.HexColor("#15803d")),
                ("TEXTCOLOR", (0, 3), (1, 3), RED_TEXT),
                ("TEXTCOLOR", (0, 4), (1, 4), RED_TEXT),
                ("BACKGROUND", (0, 5), (-1, 5), GREEN_ROW),
                ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
                ("FONTSIZE", (0, 5), (-1, 5), 11),
            ]
        )
    )
    elements.append(salary_table)
    elements.append(Spacer(1, 5 * mm))

    words_style = ParagraphStyle("Words", parent=styles["Normal"], fontSize=9.5, alignment=TA_RIGHT)
    elements.append(Paragraph(f"<b>Amount in Words:</b> {number_to_words(salary['net_payable'])}", words_style))
    elements.append(Spacer(1, 14 * mm))

    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=8, leading=11, textColor=TEXT_MUTED, alignment=TA_CENTER
    )
    elements.append(Paragraph("This is a computer generated salary slip. No signature required.", footer_style))
    elements.append(Paragraph(f"Generated on: {generated_date}", footer_style))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()
