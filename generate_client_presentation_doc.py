import os
from PIL import Image, ImageDraw, ImageFont
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# Paths
DOC_OUTPUT_PATH = "NECO_MCS_Voting_System_Client_Presentation.docx"
IMG_DIR = "presentation_assets"
os.makedirs(IMG_DIR, exist_ok=True)

# Fonts for Pillow
FONT_BOLD = "C:\\Windows\\Fonts\\segoeuib.ttf"
FONT_REGULAR = "C:\\Windows\\Fonts\\segoeui.ttf"
FONT_SEMI = "C:\\Windows\\Fonts\\segoeui.ttf"
FONT_MONO = "C:\\Windows\\Fonts\\consola.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# -------------------------------------------------------------
# IMAGE 1: Contact Update Portal (Obscured Data)
# -------------------------------------------------------------
def create_contact_update_img():
    width, height = 1100, 680
    img = Image.new("RGB", (width, height), color="#0F172A")
    d = ImageDraw.Draw(img)

    f_title = get_font(FONT_BOLD, 30)
    f_sub = get_font(FONT_REGULAR, 18)
    f_badge = get_font(FONT_BOLD, 15)
    f_label = get_font(FONT_BOLD, 16)
    f_val = get_font(FONT_MONO, 18)
    f_btn = get_font(FONT_BOLD, 17)
    f_note = get_font(FONT_REGULAR, 15)

    # Header Card
    d.rounded_rectangle([(40, 30), (1060, 110)], radius=14, fill="#1E293B", outline="#334155", width=2)
    d.text((65, 45), "NECO MCS - Official Voter Contact Registry", font=f_title, fill="#38BDF8")
    d.text((65, 80), "Self-service contact verification and record locking system", font=f_sub, fill="#94A3B8")

    # Main Card
    d.rounded_rectangle([(40, 130), (1060, 640)], radius=16, fill="#1E293B", outline="#334155", width=2)

    # MCS Number Looked Up
    d.text((70, 160), "Voter Identification (MCS Number)", font=f_label, fill="#CBD5E1")
    d.rounded_rectangle([(70, 190), (520, 245)], radius=10, fill="#0F172A", outline="#475569", width=1)
    d.text((90, 205), "MCS-2668  [VERIFIED RECORD]", font=f_val, fill="#4ADE80")

    # Full Name (Obscured)
    d.text((560, 160), "Official Full Name (Obscured for Privacy)", font=f_label, fill="#CBD5E1")
    d.rounded_rectangle([(560, 190), (1020, 245)], radius=10, fill="#0F172A", outline="#475569", width=1)
    d.text((580, 205), "A*******  O******* (Read-Only)", font=f_val, fill="#E2E8F0")

    # Registered Email (Masked / Read Only)
    d.text((70, 270), "Registered Email Address", font=f_label, fill="#CBD5E1")
    d.rounded_rectangle([(70, 300), (520, 355)], radius=10, fill="#0F172A", outline="#475569", width=1)
    d.text((90, 315), "t******@gmail.com  (LOCKED)", font=f_val, fill="#F59E0B")
    d.rounded_rectangle([(410, 310), (510, 345)], radius=6, fill="#312E81")
    d.text((425, 318), "LOCKED", font=f_badge, fill="#A5B4FC")

    # Registered Phone (Masked / Read Only)
    d.text((560, 270), "Registered Phone Number", font=f_label, fill="#CBD5E1")
    d.rounded_rectangle([(560, 300), (1020, 355)], radius=10, fill="#0F172A", outline="#475569", width=1)
    d.text((580, 315), "+234 803 *** 1234  (LOCKED)", font=f_val, fill="#F59E0B")
    d.rounded_rectangle([(910, 310), (1010, 345)], radius=6, fill="#312E81")
    d.text((925, 318), "LOCKED", font=f_badge, fill="#A5B4FC")

    # Security Alert Callout Box
    d.rounded_rectangle([(70, 385), (1020, 485)], radius=12, fill="#064E3B", outline="#059669", width=2)
    d.text((95, 400), "DATA INTEGRITY & SECURITY POLICY", font=f_label, fill="#34D399")
    d.text((95, 430), "• Existing voter contact records cannot be overwritten directly to prevent hijacking.", font=f_note, fill="#D1FAE5")
    d.text((95, 455), "• If your contact details have changed, click 'Raise Dispute' below for administrative review.", font=f_note, fill="#D1FAE5")

    # Action Buttons
    # Raise Dispute Button
    d.rounded_rectangle([(70, 520), (320, 580)], radius=12, fill="#B91C1C", outline="#DC2626", width=2)
    d.text((105, 538), "Raise Dispute / Inquiry", font=f_btn, fill="#FFFFFF")

    # Status: Confirmed & Accredited
    d.rounded_rectangle([(350, 520), (700, 580)], radius=12, fill="#4338CA", outline="#6366F1", width=2)
    d.text((375, 538), "Submit Details & Verify OTP", font=f_btn, fill="#FFFFFF")

    # Info footer
    d.text((70, 605), "Status: Verified via Transactional Google SMTP OTP  |  Uniqueness Constraint: Active", font=f_note, fill="#64748B")

    path = os.path.join(IMG_DIR, "contact_update_portal.png")
    img.save(path, quality=95)
    return path

# -------------------------------------------------------------
# IMAGE 2: Accreditation & Device Binding (Success)
# -------------------------------------------------------------
def create_accreditation_img():
    width, height = 1100, 680
    img = Image.new("RGB", (width, height), color="#0F172A")
    d = ImageDraw.Draw(img)

    f_title = get_font(FONT_BOLD, 30)
    f_sub = get_font(FONT_REGULAR, 18)
    f_h2 = get_font(FONT_BOLD, 24)
    f_msg = get_font(FONT_BOLD, 19)
    f_label = get_font(FONT_BOLD, 16)
    f_val = get_font(FONT_MONO, 17)
    f_badge = get_font(FONT_BOLD, 15)
    f_note = get_font(FONT_REGULAR, 15)

    # Header Card
    d.rounded_rectangle([(40, 30), (1060, 110)], radius=14, fill="#1E293B", outline="#334155", width=2)
    d.text((65, 45), "NECO MCS - Official Voter Accreditation Portal", font=f_title, fill="#38BDF8")
    d.text((65, 80), "Pre-election identity verification and exclusive device binding", font=f_sub, fill="#94A3B8")

    # Main Success Card
    d.rounded_rectangle([(40, 130), (1060, 640)], radius=16, fill="#1E293B", outline="#334155", width=2)

    # Success Badge
    d.rounded_rectangle([(480, 150), (620, 210)], radius=12, fill="#065F46", outline="#10B981", width=2)
    d.text((505, 170), "ACCREDITED", font=f_badge, fill="#6EE7B7")

    # Success Heading
    d.text((360, 225), "Accreditation Confirmed!", font=f_h2, fill="#F8FAFC")
    
    # Specified Client Message Banner
    d.rounded_rectangle([(100, 270), (1000, 335)], radius=12, fill="#064E3B", outline="#059669", width=2)
    d.text((120, 292), "you have been successfully accredited for the NECO MCS election,", font=f_msg, fill="#A7F3D0")
    d.text((690, 292), "wait for further instruction for voting.", font=f_msg, fill="#FCD34D")

    # Credentials & Device Binding Summary Card
    d.rounded_rectangle([(100, 360), (1000, 560)], radius=12, fill="#0F172A", outline="#334155", width=1)

    # Row 1: MCS & Full Name
    d.text((130, 385), "MCS Username:", font=f_label, fill="#94A3B8")
    d.text((300, 385), "MCS-2668", font=f_val, fill="#FFFFFF")

    d.text((580, 385), "Full Name:", font=f_label, fill="#94A3B8")
    d.text((720, 385), "A*******  O******* (Accredited)", font=f_val, fill="#FFFFFF")

    # Row 2: Phone & Email
    d.text((130, 435), "Phone Number:", font=f_label, fill="#94A3B8")
    d.text((300, 435), "+234 803 *** 1234", font=f_val, fill="#FFFFFF")

    d.text((580, 435), "Registered Email:", font=f_label, fill="#94A3B8")
    d.text((720, 435), "t******@gmail.com", font=f_val, fill="#FFFFFF")

    # Row 3: Strict Device Binding (Highlighted)
    d.rounded_rectangle([(120, 480), (980, 540)], radius=8, fill="#1E1B4B", outline="#6366F1", width=1)
    d.text((140, 497), "Bound Voting Device:", font=f_label, fill="#A5B4FC")
    d.text((330, 497), "Chrome on Android (Hardware Fingerprint UUID: 8a4f...9c1d)", font=f_val, fill="#38BDF8")
    d.rounded_rectangle([(870, 490), (970, 530)], radius=6, fill="#4338CA")
    d.text((885, 500), "LOCKED", font=f_badge, fill="#FFFFFF")

    # Footer Notice
    d.text((100, 585), "Security Guarantee: Only this exact mobile device and browser can vote on election day.", font=f_note, fill="#38BDF8")
    d.text((100, 610), "Any attempt to vote from a desktop, another phone, or incognito window will be blocked automatically.", font=f_note, fill="#94A3B8")

    path = os.path.join(IMG_DIR, "accreditation_device_bound.png")
    img.save(path, quality=95)
    return path

# -------------------------------------------------------------
# IMAGE 3: Election Day Device Mismatch Security Protection
# -------------------------------------------------------------
def create_device_lock_img():
    width, height = 1100, 650
    img = Image.new("RGB", (width, height), color="#0F172A")
    d = ImageDraw.Draw(img)

    f_title = get_font(FONT_BOLD, 30)
    f_sub = get_font(FONT_REGULAR, 18)
    f_h2 = get_font(FONT_BOLD, 22)
    f_label = get_font(FONT_BOLD, 16)
    f_val = get_font(FONT_MONO, 17)
    f_badge = get_font(FONT_BOLD, 15)
    f_note = get_font(FONT_REGULAR, 16)

    # Header Card
    d.rounded_rectangle([(40, 30), (1060, 110)], radius=14, fill="#1E293B", outline="#334155", width=2)
    d.text((65, 45), "NECO MCS - Election Day Security Enforcement", font=f_title, fill="#38BDF8")
    d.text((65, 80), "Zero-Trust Physical Device Verification & Anti-Proxy Protection", font=f_sub, fill="#94A3B8")

    # Main Card
    d.rounded_rectangle([(40, 130), (1060, 610)], radius=16, fill="#1E293B", outline="#334155", width=2)

    # Warning Box
    d.rounded_rectangle([(70, 160), (1030, 320)], radius=14, fill="#451A03", outline="#F59E0B", width=2)
    d.rounded_rectangle([(95, 180), (320, 225)], radius=8, fill="#B45309")
    d.text((110, 192), "DEVICE SECURITY LOCK", font=f_badge, fill="#FFFFFF")

    d.text((95, 240), "HTTP 403 Forbidden: Device Mismatch Detected", font=f_h2, fill="#FDE68A")
    d.text((95, 275), "This voter account was accredited on another device (Chrome on Android).", font=f_note, fill="#FEF3C7")
    d.text((95, 298), "You are currently attempting to vote from Windows Desktop (Edge). Access is strictly denied.", font=f_note, fill="#FCA5A5")

    # Explanatory Architecture Box
    d.rounded_rectangle([(70, 345), (1030, 520)], radius=12, fill="#0F172A", outline="#334155", width=1)
    d.text((95, 365), "HOW DEVICE BINDING PREVENTS ELECTION FRAUD:", font=f_label, fill="#38BDF8")
    
    d.text((95, 400), "1. Prevents Stolen OTP Voting: Even if an adversary intercepts a voter's OTP, they cannot vote", font=f_note, fill="#E2E8F0")
    d.text((115, 425), "without physical custody of the voter's accredited phone.", font=f_note, fill="#94A3B8")

    d.text((95, 455), "2. Prevents Bulk Ballot Stuffing: One person cannot gather multiple logins and vote on one computer.", font=f_note, fill="#E2E8F0")

    d.text((95, 485), "3. Administrative Device Recovery: If a phone is lost or damaged, an administrator can safely reverse", font=f_note, fill="#E2E8F0")
    d.text((115, 510), "accreditation, releasing the device lock so the voter can re-accredit with a replacement device.", font=f_note, fill="#94A3B8")

    d.text((70, 555), "Election Portal Protected by NECO MCS Dual-Token & Hardware Binding Protocol", font=f_note, fill="#64748B")

    path = os.path.join(IMG_DIR, "device_mismatch_lock.png")
    img.save(path, quality=95)
    return path

# -------------------------------------------------------------
# IMAGE 4: Admin Control Center & Reverse Accreditation
# -------------------------------------------------------------
def create_admin_dashboard_img():
    width, height = 1100, 680
    img = Image.new("RGB", (width, height), color="#0F172A")
    d = ImageDraw.Draw(img)

    f_title = get_font(FONT_BOLD, 28)
    f_sub = get_font(FONT_REGULAR, 17)
    f_stat_n = get_font(FONT_BOLD, 32)
    f_stat_l = get_font(FONT_REGULAR, 15)
    f_th = get_font(FONT_BOLD, 15)
    f_td = get_font(FONT_REGULAR, 15)
    f_td_mono = get_font(FONT_MONO, 15)
    f_badge = get_font(FONT_BOLD, 13)

    # Header Card
    d.rounded_rectangle([(40, 25), (1060, 95)], radius=12, fill="#1E293B", outline="#334155", width=2)
    d.text((65, 38), "NECO MCS - Electoral Management & Administration Console", font=f_title, fill="#38BDF8")
    d.text((65, 68), "Live Voter Register, Reverse Accreditation & Dispute Resolution", font=f_sub, fill="#94A3B8")

    # Metric Cards Row
    metrics = [
        ("Total Voters", "1,240", "#38BDF8", 40),
        ("Accredited", "1,118", "#4ADE80", 300),
        ("Bound Devices", "1,118", "#A78BFA", 560),
        ("Pending Disputes", "3", "#F87171", 820),
    ]
    for label, val, col, x in metrics:
        d.rounded_rectangle([(x, 115), (x + 240, 195)], radius=10, fill="#1E293B", outline="#334155", width=1)
        d.text((x + 20, 128), label, font=f_stat_l, fill="#94A3B8")
        d.text((x + 20, 150), val, font=f_stat_n, fill=col)

    # Voter Table Card
    d.rounded_rectangle([(40, 215), (1060, 650)], radius=14, fill="#1E293B", outline="#334155", width=2)
    d.text((65, 230), "Voter Accreditation & Device Security Register", font=get_font(FONT_BOLD, 19), fill="#F8FAFC")

    # Table Header Row
    d.rectangle([(60, 270), (1040, 305)], fill="#0F172A")
    d.text((75, 280), "MCS NO", font=f_th, fill="#94A3B8")
    d.text((180, 280), "VOTER NAME", font=f_th, fill="#94A3B8")
    d.text((360, 280), "STATUS", font=f_th, fill="#94A3B8")
    d.text((500, 280), "BOUND HARDWARE DEVICE", font=f_th, fill="#94A3B8")
    d.text((790, 280), "ADMINISTRATIVE ACTION", font=f_th, fill="#94A3B8")

    # Sample rows (obscured data)
    rows = [
        ("2668", "A******* O*******", "Accredited", "Chrome on Android (UUID: 8a4f...)", True, 320),
        ("1402", "B******* E*******", "Accredited", "Safari on iOS (UUID: e23b...)", True, 385),
        ("3150", "C******* M*******", "Pending Acc.", "No Device Bound Yet", False, 450),
        ("0884", "D******* S*******", "Dispute Raised", "Reviewing Email Change", False, 515),
        ("4012", "F******* K*******", "Accredited", "Chrome on Windows (UUID: 71cf...)", True, 580),
    ]

    for mcs, name, status, dev, has_reverse, y in rows:
        d.rectangle([(60, y - 5), (1040, y + 45)], fill="#172033" if (y // 60) % 2 == 0 else "#1E293B")
        d.text((75, y + 8), mcs, font=f_td_mono, fill="#38BDF8")
        d.text((180, y + 8), name, font=f_td, fill="#E2E8F0")

        # Status badge
        badge_col = "#065F46" if "Accredited" in status else ("#7F1D1D" if "Dispute" in status else "#312E81")
        badge_txt = "#34D399" if "Accredited" in status else ("#FCA5A5" if "Dispute" in status else "#A5B4FC")
        d.rounded_rectangle([(360, y + 5), (475, y + 33)], radius=6, fill=badge_col)
        d.text((370, y + 10), status, font=f_badge, fill=badge_txt)

        # Device info
        d.text((500, y + 8), dev, font=f_td_mono, fill="#94A3B8" if "No Device" in dev else "#FCD34D")

        # Reverse Accreditation Button
        if has_reverse:
            d.rounded_rectangle([(790, y + 4), (1020, y + 34)], radius=6, fill="#B91C1C", outline="#DC2626", width=1)
            d.text((805, y + 10), "Reverse Accreditation", font=f_badge, fill="#FFFFFF")
        elif "Dispute" in status:
            d.rounded_rectangle([(790, y + 4), (1020, y + 34)], radius=6, fill="#D97706", outline="#F59E0B", width=1)
            d.text((815, y + 10), "Investigate Dispute", font=f_badge, fill="#FFFFFF")
        else:
            d.text((815, y + 10), "Awaiting Voter", font=f_td, fill="#64748B")

    path = os.path.join(IMG_DIR, "admin_dashboard_register.png")
    img.save(path, quality=95)
    return path

# -------------------------------------------------------------
# XML Formatting Helpers for python-docx
# -------------------------------------------------------------
def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_callout(doc, title, text, border_color="1E3A8A", bg_color="F0F4F8"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=160, bottom=160, left=240, right=200)

    # Left border only
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    run_t = p.add_run(f"SECURITY POLICY: {title}\n")
    run_t.bold = True
    run_t.font.size = Pt(11)
    run_t.font.name = "Segoe UI"
    run_t.font.color.rgb = RGBColor.from_string(border_color)

    run_body = p.add_run(text)
    run_body.font.size = Pt(10)
    run_body.font.name = "Segoe UI"
    run_body.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# -------------------------------------------------------------
# BUILD WORD DOCUMENT
# -------------------------------------------------------------
def build_document():
    # 1. Generate screenshots
    p1 = create_contact_update_img()
    p2 = create_accreditation_img()
    p3 = create_device_lock_img()
    p4 = create_admin_dashboard_img()

    doc = Document()

    # Page Margins: 0.75 in for sleek executive report layout
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Document Header / Brand Banner
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(0)
    p_pre.paragraph_format.space_after = Pt(2)
    run_pre = p_pre.add_run("NECO MULTIPURPOSE COOPERATIVE SOCIETY (MCS)")
    run_pre.bold = True
    run_pre.font.size = Pt(10)
    run_pre.font.name = "Segoe UI"
    run_pre.font.color.rgb = RGBColor(0x43, 0x38, 0xCA)

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("Electronic Voting & Accreditation System")
    run_title.bold = True
    run_title.font.size = Pt(24)
    run_title.font.name = "Segoe UI Semibold"
    run_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    run_sub = p_sub.add_run("Executive Client Presentation & Technical Process Briefing")
    run_sub.font.size = Pt(13)
    run_sub.font.name = "Segoe UI"
    run_sub.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # Metadata Table
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    meta_table.columns[0].width = Inches(3.5)
    meta_table.columns[1].width = Inches(3.5)

    c00 = meta_table.cell(0, 0)
    c01 = meta_table.cell(0, 1)
    c10 = meta_table.cell(1, 0)
    c11 = meta_table.cell(1, 1)

    for c in [c00, c01, c10, c11]:
        set_cell_background(c, "F8FAFC")
        set_cell_margins(c, top=80, bottom=80, left=120, right=120)

    c00.paragraphs[0].add_run("Target Audience: ").bold = True
    c00.paragraphs[0].runs[0].font.name = "Segoe UI"
    c00.paragraphs[0].runs[0].font.size = Pt(9.5)
    c00.paragraphs[0].add_run("NECO MCS Electoral Committee & Executive Board").font.size = Pt(9.5)

    c01.paragraphs[0].add_run("Prepared Date: ").bold = True
    c01.paragraphs[0].runs[0].font.name = "Segoe UI"
    c01.paragraphs[0].runs[0].font.size = Pt(9.5)
    c01.paragraphs[0].add_run("November 2026").font.size = Pt(9.5)

    c10.paragraphs[0].add_run("System Architecture: ").bold = True
    c10.paragraphs[0].runs[0].font.name = "Segoe UI"
    c10.paragraphs[0].runs[0].font.size = Pt(9.5)
    c10.paragraphs[0].add_run("FastAPI Backend + React / Vite Single Page App").font.size = Pt(9.5)

    c11.paragraphs[0].add_run("Core Security: ").bold = True
    c11.paragraphs[0].runs[0].font.name = "Segoe UI"
    c11.paragraphs[0].runs[0].font.size = Pt(9.5)
    c11.paragraphs[0].add_run("Hardware Device Binding, 2-Stage OTP, Audit Logs").font.size = Pt(9.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Executive Summary
    h_exec = doc.add_heading(level=1)
    h_exec.paragraph_format.space_before = Pt(8)
    h_exec.paragraph_format.space_after = Pt(4)
    run_he = h_exec.add_run("Executive Overview")
    run_he.font.name = "Segoe UI Semibold"
    run_he.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    p_exec = doc.add_paragraph()
    p_exec.paragraph_format.space_after = Pt(10)
    p_exec.paragraph_format.line_spacing = 1.15
    run_pe = p_exec.add_run(
        "The NECO MCS Electronic Voting Platform is an enterprise-grade electoral solution engineered to guarantee "
        "absolute voting integrity, verifiable voter accreditation, and zero-trust device security. Built specifically "
        "for the NECO Multipurpose Cooperative Society elections, the application eliminates proxy voting, voter impersonation, "
        "and ballot tampering through cryptographic device binding, multi-stage OTP email verification, and immutable audit logs."
    )
    run_pe.font.name = "Segoe UI"
    run_pe.font.size = Pt(10.5)

    # SECTION 1: Contact Update Portal
    h1 = doc.add_heading(level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(4)
    run_h1 = h1.add_run("1. Voter Contact Registration & Verification (/contact-update)")
    run_h1.font.name = "Segoe UI Semibold"
    run_h1.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    p1_desc = doc.add_paragraph()
    p1_desc.paragraph_format.space_after = Pt(8)
    p1_desc.paragraph_format.line_spacing = 1.15
    p1_desc.add_run(
        "To ensure that all legitimate cooperative members receive their secure OTP passcodes seamlessly on election day, "
        "voters utilize the dedicated Contact Registration Portal. This gateway enables voters to register their verified email "
        "and phone number without compromising existing register integrity."
    ).font.name = "Segoe UI"

    # Bullet steps
    steps1 = [
        ("Voter Lookup via MCS Username: ", "The voter enters their 4-digit MCS number (e.g., 2668). The system matches the record against the official voter database."),
        ("Strict Read-Only Protection for Existing Data: ", "Any previously recorded phone number or email is automatically locked and uneditable. This prevents unauthorized overwriting or credential hijacking."),
        ("New Contact Addition: ", "If an email or phone number is missing, the respective input field unlocks, allowing the member to input their details."),
        ("Strict Global Uniqueness: ", "The database rejects duplicate phone numbers or email addresses across all accounts, guaranteeing that one person cannot control multiple voter records."),
        ("Dual-Stage OTP Confirmation: ", "Data is NEVER committed to the database immediately. A 6-digit confirmation OTP is dispatched to the supplied email via Google SMTP (necomcsvotes@gmail.com). The details are saved only after OTP verification."),
        ("Dispute Resolution Mechanism: ", "If an existing record contains outdated or erroneous information, voters cannot edit it directly; instead, they click 'Raise Dispute' to log an inquiry for the administrative team to investigate and resolve.")
    ]
    for b_title, b_desc in steps1:
        p_b = doc.add_paragraph(style='List Bullet')
        p_b.paragraph_format.space_before = Pt(2)
        p_b.paragraph_format.space_after = Pt(2)
        p_b.paragraph_format.line_spacing = 1.15
        r_bt = p_b.add_run(b_title)
        r_bt.bold = True
        r_bt.font.name = "Segoe UI"
        r_bt.font.size = Pt(10)
        r_bd = p_b.add_run(b_desc)
        r_bd.font.name = "Segoe UI"
        r_bd.font.size = Pt(10)

    # Insert Image 1
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    doc.add_picture(p1, width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap1 = doc.add_paragraph()
    p_cap1.paragraph_format.space_before = Pt(2)
    p_cap1.paragraph_format.space_after = Pt(12)
    p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap1 = p_cap1.add_run("Figure 1: Contact Update Portal showing read-only locked fields, privacy-obscured details, and Dispute action.")
    r_cap1.font.size = Pt(9)
    r_cap1.font.italic = True
    r_cap1.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # SECTION 2: Voter Accreditation & Device Binding
    h2 = doc.add_heading(level=1)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(4)
    run_h2 = h2.add_run("2. Mandatory Voter Accreditation & Exclusive Device Binding (/accreditation)")
    run_h2.font.name = "Segoe UI Semibold"
    run_h2.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    p2_desc = doc.add_paragraph()
    p2_desc.paragraph_format.space_after = Pt(8)
    p2_desc.paragraph_format.line_spacing = 1.15
    p2_desc.add_run(
        "Accreditation is a mandatory pre-election gate. Only voters who have completed electronic accreditation can access "
        "the ballot on election day. During accreditation, the system permanently binds the voter's profile to their physical device."
    ).font.name = "Segoe UI"

    steps2 = [
        ("Step 1 - MCS Validation: ", "Voter enters their MCS number to pull verified register credentials."),
        ("Step 2 - Identity & Device Notice: ", "Voter verifies their full name and masked email/phone. A prominent security warning explains that the current browser/device will be permanently locked as their sole voting terminal."),
        ("Step 3 - Accreditation OTP Verification: ", "An accreditation OTP is sent to the registered email. Upon typing the 6-digit code, the backend seals the accreditation."),
        ("Step 4 - Device Lock & Confirmation: ", "The system records accredited_device_id (a persistent UUID) and device_info (e.g., Chrome on Android) in the database and renders the official confirmation message: 'you have been successfully accredited for the NECO MCS election, wait for further instruction for voting.'")
    ]
    for b_title, b_desc in steps2:
        p_b = doc.add_paragraph(style='List Bullet')
        p_b.paragraph_format.space_before = Pt(2)
        p_b.paragraph_format.space_after = Pt(2)
        p_b.paragraph_format.line_spacing = 1.15
        r_bt = p_b.add_run(b_title)
        r_bt.bold = True
        r_bt.font.name = "Segoe UI"
        r_bt.font.size = Pt(10)
        r_bd = p_b.add_run(b_desc)
        r_bd.font.name = "Segoe UI"
        r_bd.font.size = Pt(10)

    # Insert Image 2
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    doc.add_picture(p2, width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap2 = doc.add_paragraph()
    p_cap2.paragraph_format.space_before = Pt(2)
    p_cap2.paragraph_format.space_after = Pt(12)
    p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap2 = p_cap2.add_run("Figure 2: Accreditation Confirmation Screen with official confirmation message and Bound Voting Device indicator.")
    r_cap2.font.size = Pt(9)
    r_cap2.font.italic = True
    r_cap2.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # SECTION 3: Election Day Voting & Security Enforcement
    h3 = doc.add_heading(level=1)
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(4)
    run_h3 = h3.add_run("3. Election Day Voting & Anti-Proxy Enforcement (/election & /login)")
    run_h3.font.name = "Segoe UI Semibold"
    run_h3.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    p3_desc = doc.add_paragraph()
    p3_desc.paragraph_format.space_after = Pt(8)
    p3_desc.paragraph_format.line_spacing = 1.15
    p3_desc.add_run(
        "On election day, the voting portal enforces zero-trust physical device verification to ensure that only the exact person "
        "who accredited can cast the ballot from the exact device they accredited with."
    ).font.name = "Segoe UI"

    steps3 = [
        ("Session Timing Check: ", "Voting can only occur while the administrator has officially opened the election window. Outside active hours, the portal remains securely locked."),
        ("Strict Device Check at Login: ", "When the voter submits their MCS number, the backend compares the incoming device_id against accredited_device_id. If a mismatch is detected (e.g. attempting to log in from a laptop when accredited on a phone), login is blocked with HTTP 403 Forbidden."),
        ("Voting OTP Generation: ", "If the device matches, an ephemeral 6-digit voting passcode is dispatched to their registered email address."),
        ("Ballot Access & Secret Ballot: ", "Once the OTP is confirmed, the voter enters the digital voting booth to cast votes across all contested executive offices."),
        ("Receipt Generation: ", "Upon submission, a cryptographic receipt hash is generated for end-to-end voter verification.")
    ]
    for b_title, b_desc in steps3:
        p_b = doc.add_paragraph(style='List Bullet')
        p_b.paragraph_format.space_before = Pt(2)
        p_b.paragraph_format.space_after = Pt(2)
        p_b.paragraph_format.line_spacing = 1.15
        r_bt = p_b.add_run(b_title)
        r_bt.bold = True
        r_bt.font.name = "Segoe UI"
        r_bt.font.size = Pt(10)
        r_bd = p_b.add_run(b_desc)
        r_bd.font.name = "Segoe UI"
        r_bd.font.size = Pt(10)

    # Insert Image 3
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    doc.add_picture(p3, width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap3 = doc.add_paragraph()
    p_cap3.paragraph_format.space_before = Pt(2)
    p_cap3.paragraph_format.space_after = Pt(12)
    p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap3 = p_cap3.add_run("Figure 3: Automatic Device Mismatch Lock protecting against unauthorized proxy voting.")
    r_cap3.font.size = Pt(9)
    r_cap3.font.italic = True
    r_cap3.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # SECTION 4: Administrative Management Console
    h4 = doc.add_heading(level=1)
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(4)
    run_h4 = h4.add_run("4. Administrative Command Center (/admin)")
    run_h4.font.name = "Segoe UI Semibold"
    run_h4.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    p4_desc = doc.add_paragraph()
    p4_desc.paragraph_format.space_after = Pt(8)
    p4_desc.paragraph_format.line_spacing = 1.15
    p4_desc.add_run(
        "Election officials manage the election through a dedicated, password-protected administrative interface with complete "
        "visibility over voter registers, accreditation statuses, and dispute queues."
    ).font.name = "Segoe UI"

    steps4 = [
        ("Real-Time Election Metrics: ", "Live counters for registered voters, completed accreditations, active bound devices, and turnout percentages."),
        ("Voter Register Management: ", "Full table of all cooperative members with search, filter, and pagination capabilities."),
        ("One-Click 'Reverse Accreditation': ", "If a voter loses their phone, their device is damaged, or an accreditation issue occurs, the admin can click 'Reverse Accreditation'. This immediately resets both is_accredited to false and clears accredited_device_id and device_info, enabling the voter to re-accredit cleanly with a replacement device."),
        ("Dispute Queue & Investigation: ", "Admins inspect flagged disputes submitted by voters requesting contact updates or reporting discrepancies."),
        ("Election Window Control: ", "Ability to start, pause, or conclude the voting window in real-time or schedule automated opening and closing times.")
    ]
    for b_title, b_desc in steps4:
        p_b = doc.add_paragraph(style='List Bullet')
        p_b.paragraph_format.space_before = Pt(2)
        p_b.paragraph_format.space_after = Pt(2)
        p_b.paragraph_format.line_spacing = 1.15
        r_bt = p_b.add_run(b_title)
        r_bt.bold = True
        r_bt.font.name = "Segoe UI"
        r_bt.font.size = Pt(10)
        r_bd = p_b.add_run(b_desc)
        r_bd.font.name = "Segoe UI"
        r_bd.font.size = Pt(10)

    # Insert Image 4
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    doc.add_picture(p4, width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap4 = doc.add_paragraph()
    p_cap4.paragraph_format.space_before = Pt(2)
    p_cap4.paragraph_format.space_after = Pt(12)
    p_cap4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap4 = p_cap4.add_run("Figure 4: Admin Console showing live voter register, bound device identifiers, and Reverse Accreditation controls.")
    r_cap4.font.size = Pt(9)
    r_cap4.font.italic = True
    r_cap4.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # SECTION 5: Comprehensive Security Matrix Table
    h5 = doc.add_heading(level=1)
    h5.paragraph_format.space_before = Pt(14)
    h5.paragraph_format.space_after = Pt(6)
    run_h5 = h5.add_run("5. Multi-Layer Security Architecture Matrix")
    run_h5.font.name = "Segoe UI Semibold"
    run_h5.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    # Security Matrix Table
    sec_table = doc.add_table(rows=6, cols=3)
    sec_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sec_table.autofit = False
    sec_table.columns[0].width = Inches(1.8)
    sec_table.columns[1].width = Inches(2.2)
    sec_table.columns[2].width = Inches(2.5)

    headers = ["Security Vector", "Implementation Mechanism", "Electoral Threat Mitigated"]
    for i, h_text in enumerate(headers):
        cell = sec_table.cell(0, i)
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Segoe UI Semibold"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    sec_data = [
        ("Device Binding (Hardware Lock)", "UUIDv4 & Browser Client Fingerprinting stored in accredited_device_id", "Stops proxy voting, ballot harvesting, and centralized voter hijacking across shared devices."),
        ("Mandatory Pre-Accreditation", "Gated voter status (is_accredited = True) required before election access", "Prevents unverified walk-ins or unvetted accounts from participating on election day."),
        ("Dual-Stage OTP Delivery", "Transactional Google SMTP (necomcsvotes@gmail.com) with 6-minute TTLs", "Guarantees reliable, instant OTP delivery to legitimate voter email addresses with zero spam drop."),
        ("Contact Immutability & Disputes", "Read-only existing records; admin-moderated dispute review queue", "Prevents unauthorized phone or email changes that could divert voting OTPs to hostile actors."),
        ("Audit Receipts & One-Vote Rule", "SHA-256 ballot hash generation + DB unique voter-office constraint", "Prevents double-voting and allows voters to mathematically verify their ballot was cast.")
    ]

    for row_idx, (v, m, t) in enumerate(sec_data, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate([v, m, t]):
            cell = sec_table.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.name = "Segoe UI"
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # Callout Box: Summary of Client Presentation Highlights
    add_callout(
        doc,
        "KEY PRESENTATION TALKING POINTS FOR CLIENT STAKEHOLDERS",
        "1. Fair, Transparent, and Non-Repudiable: Every voter can vote once and only once from their registered phone.\n"
        "2. Zero Compromise on Privacy: Member details are obscured across screens while preserving full administrative audit trails.\n"
        "3. High Resilience: Automated 'Reverse Accreditation' ensures voters facing technical device loss are never disenfranchised.\n"
        "4. Ready for Deployment: Successfully tested, built, and synchronized to the Contabo server infrastructure.",
        border_color="059669",
        bg_color="ECFDF5"
    )

    doc.save(DOC_OUTPUT_PATH)
    print(f"Document successfully created at: {os.path.abspath(DOC_OUTPUT_PATH)}")

if __name__ == "__main__":
    build_document()
