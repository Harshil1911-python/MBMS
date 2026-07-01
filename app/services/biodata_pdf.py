import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import current_app

PRIMARY_BLUE = colors.HexColor("#0b3d91")
LIGHT_BLUE = colors.HexColor("#e8f0fe")
WHITE = colors.white


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="OrgTitle", fontSize=18, textColor=PRIMARY_BLUE,
                           alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=2))
    ss.add(ParagraphStyle(name="OrgSub", fontSize=10, textColor=colors.grey,
                           alignment=TA_CENTER, spaceAfter=8))
    ss.add(ParagraphStyle(name="SectionHead", fontSize=12, textColor=WHITE,
                           fontName="Helvetica-Bold", backColor=PRIMARY_BLUE,
                           leftIndent=6, spaceBefore=10, spaceAfter=6, borderPadding=4))
    ss.add(ParagraphStyle(name="NameHead", fontSize=16, textColor=PRIMARY_BLUE,
                           fontName="Helvetica-Bold", alignment=TA_CENTER, spaceBefore=6, spaceAfter=2))
    ss.add(ParagraphStyle(name="Small", fontSize=8, textColor=colors.grey, alignment=TA_CENTER))
    ss.add(ParagraphStyle(name="Body", fontSize=9.5, leading=13))
    return ss


def _field_table(rows, col_widths=(45 * mm, 130 * mm)):
    data = []
    for label, value in rows:
        data.append([Paragraph(f"<b>{label}</b>", ParagraphStyle(name="lbl", fontSize=9, textColor=PRIMARY_BLUE)),
                     Paragraph(str(value) if value not in (None, "") else "-",
                               ParagraphStyle(name="val", fontSize=9))])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
    ]))
    return t


def generate_biodata_pdf(profile, org_name="CITYLIGHT SINDHI SAMAJ SURAT"):
    """Generates a professional blue/white biodata PDF for a profile. Returns relative path."""
    folder = current_app.config["PDF_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    filename = f"biodata_{profile.public_id}.pdf"
    full_path = os.path.join(folder, filename)

    doc = SimpleDocTemplate(full_path, pagesize=A4,
                             topMargin=14 * mm, bottomMargin=14 * mm,
                             leftMargin=16 * mm, rightMargin=16 * mm)
    styles = _styles()
    story = []

    # Header
    story.append(Paragraph(org_name, styles["OrgTitle"]))
    story.append(Paragraph("Marriage Biodata", styles["OrgSub"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=PRIMARY_BLUE, spaceAfter=8))

    # Photo + Name header row
    photo_flowable = None
    static_folder = current_app.static_folder
    if profile.featured_photo_path:
        photo_full = os.path.join(static_folder, profile.featured_photo_path)
        if os.path.exists(photo_full):
            photo_flowable = Image(photo_full, width=38 * mm, height=45 * mm)

    qr_flowable = None
    if profile.qr_path:
        qr_full = os.path.join(static_folder, profile.qr_path)
        if os.path.exists(qr_full):
            qr_flowable = Image(qr_full, width=24 * mm, height=24 * mm)

    name_block = [
        Paragraph(profile.full_name, styles["NameHead"]),
        Paragraph(f"{profile.candidate_type.title()} &nbsp;|&nbsp; Profile Code: {profile.profile_code}",
                  ParagraphStyle(name="sub2", fontSize=10, alignment=TA_CENTER, textColor=colors.grey)),
        Paragraph(f"Age: {profile.age or '-'} &nbsp;|&nbsp; Height: {profile.height_display} &nbsp;|&nbsp; "
                  f"{profile.current_city or '-'}",
                  ParagraphStyle(name="sub3", fontSize=10, alignment=TA_CENTER)),
    ]

    header_row = [
        photo_flowable if photo_flowable else Paragraph("Photo", styles["Small"]),
        name_block,
        qr_flowable if qr_flowable else Paragraph("", styles["Small"]),
    ]
    header_table = Table([header_row], colWidths=[42 * mm, 106 * mm, 30 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # Personal Details
    story.append(Paragraph("PERSONAL DETAILS", styles["SectionHead"]))
    story.append(_field_table([
        ("Date of Birth", profile.date_of_birth.strftime("%d %b %Y") if profile.date_of_birth else "-"),
        ("Time / Place of Birth", f"{profile.time_of_birth or '-'} / {profile.place_of_birth or '-'}"),
        ("Father's Name", profile.father_name),
        ("Mother's Name", profile.mother_name),
        ("Height / Weight", f"{profile.height_display} / {profile.weight_kg or '-'} kg"),
        ("Blood Group", profile.blood_group),
        ("Complexion / Body Type", f"{profile.complexion or '-'} / {profile.body_type or '-'}"),
        ("Marital Status", profile.marital_status),
        ("Community / Caste", f"{profile.community or '-'} / {profile.sindhi_caste or '-'} "
                               f"({profile.sub_caste or '-'})"),
        ("Mother Tongue", profile.mother_tongue),
    ]))

    # Education & Career
    story.append(Paragraph("EDUCATION & CAREER", styles["SectionHead"]))
    story.append(_field_table([
        ("Qualification", profile.qualification),
        ("College / University", f"{profile.college or '-'} / {profile.university or '-'}"),
        ("Occupation", f"{profile.occupation or '-'} ({profile.designation or '-'})"),
        ("Company / Business", profile.company_business),
        ("Annual Income", f"₹ {profile.income_yearly:,}" if profile.income_yearly else "-"),
    ]))

    # Contact & Address
    story.append(Paragraph("CONTACT & ADDRESS", styles["SectionHead"]))
    story.append(_field_table([
        ("Current City", f"{profile.current_city or '-'}, {profile.current_state or '-'}"),
        ("Native Place", profile.native_place),
        ("Permanent Address", profile.permanent_address),
        ("Phone / WhatsApp", f"{profile.phone or '-'} / {profile.whatsapp or '-'}"),
        ("Email", profile.email),
    ]))

    # Astrology
    story.append(Paragraph("ASTROLOGICAL DETAILS", styles["SectionHead"]))
    story.append(_field_table([
        ("Rashi", profile.rashi),
        ("Nakshatra", profile.nakshatra),
        ("Manglik", profile.manglik),
        ("Mulank", profile.mulank),
        ("Kundli Available", "Yes" if profile.kundli_available else "No"),
    ]))

    # Lifestyle
    story.append(Paragraph("LIFESTYLE", styles["SectionHead"]))
    story.append(_field_table([
        ("Food Preference", profile.food_preference),
        ("Smoking / Drinking", f"{profile.smoking or '-'} / {profile.drinking or '-'}"),
        ("Hobbies", profile.hobbies),
        ("Languages Known", profile.languages_known),
    ]))

    if profile.about_yourself:
        story.append(Paragraph("ABOUT", styles["SectionHead"]))
        story.append(Paragraph(profile.about_yourself, styles["Body"]))

    # Partner Preference
    story.append(Paragraph("PARTNER PREFERENCE", styles["SectionHead"]))
    story.append(_field_table([
        ("Expected Age", f"{profile.pref_age_min or '-'} - {profile.pref_age_max or '-'} yrs"),
        ("Expected Height", f"{profile.pref_height_min or '-'} - {profile.pref_height_max or '-'} cm"),
        ("Expected Education", profile.pref_education),
        ("Expected Profession", profile.pref_profession),
        ("Expected Location", profile.pref_location),
    ]))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%d %b %Y')} — {org_name}", styles["Small"]))
    story.append(Paragraph("Powered by SERENIA UPTIME", styles["Small"]))
    story.append(Paragraph("TECH SERENIA", styles["Small"]))

    doc.build(story)
    return f"generated_pdf/{filename}"
