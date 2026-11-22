import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

IMG_DIR = r"G:\Projects\voting-app\voting-app-BE\manual_screenshots"
OUTPUT_DIR = r"G:\Projects\voting-app\voting-app-BE"
ROOT_OUTPUT_DIR = r"G:\Projects\voting-app"

# Color constants
PRIMARY_INDIGO = "4F46E5"
EMERALD_GREEN = "059669"
AMBER_WARNING = "D97706"
RED_DANGER = "DC2626"
SLATE_DARK = "0F172A"
SLATE_MUTED = "475569"
BG_LIGHT = "F8FAFC"
BORDER_LIGHT = "CBD5E1"

# -------------------------------------------------------------
# XML Formatting Helpers
# -------------------------------------------------------------
def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_callout(doc, title, text, border_color="4F46E5", bg_color="EEF2FF", prefix="NOTE"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)

    # Left colored accent border
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
    p.paragraph_format.space_after = Pt(2)
    
    r_icon = p.add_run(f"[{prefix}] {title}\n")
    r_icon.bold = True
    r_icon.font.size = Pt(10.5)
    r_icon.font.name = "Segoe UI"
    r_icon.font.color.rgb = RGBColor.from_string(border_color)

    r_body = p.add_run(text)
    r_body.font.size = Pt(9.5)
    r_body.font.name = "Segoe UI"
    r_body.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_after = Pt(4)

def add_heading_1(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.bold = True
    r.font.size = Pt(18)
    r.font.name = "Segoe UI"
    r.font.color.rgb = RGBColor.from_string(PRIMARY_INDIGO)
    return h

def add_heading_2(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.bold = True
    r.font.size = Pt(14)
    r.font.name = "Segoe UI"
    r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    return h

def add_heading_3(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(3)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.name = "Segoe UI"
    r.font.color.rgb = RGBColor.from_string(EMERALD_GREEN)
    return h

def add_body_p(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.size = Pt(10.5)
        r_pre.font.name = "Segoe UI"
        r_pre.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    r = p.add_run(text)
    r.font.size = Pt(10.5)
    r.font.name = "Segoe UI"
    r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    return p

def add_bullet_point(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.size = Pt(10)
        r_pre.font.name = "Segoe UI"
        r_pre.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    r = p.add_run(text)
    r.font.size = Pt(10)
    r.font.name = "Segoe UI"
    r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    return p

def add_figure_image(doc, img_filename, caption_text, width_inches=6.2):
    img_path = os.path.join(IMG_DIR, img_filename)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_inches))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run(caption_text)
        r_cap.italic = True
        r_cap.font.size = Pt(9)
        r_cap.font.name = "Segoe UI"
        r_cap.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
    else:
        print(f"Warning: image {img_path} not found!")

def style_table_header(row, col_widths, headers):
    for i, cell in enumerate(row.cells):
        cell.width = Inches(col_widths[i])
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(headers[i])
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.name = "Segoe UI"
        r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

def add_table_row(row, col_widths, values, is_even=False):
    bg_color = "FFFFFF" if not is_even else "F8FAFC"
    for i, cell in enumerate(row.cells):
        cell.width = Inches(col_widths[i])
        set_cell_background(cell, bg_color)
        set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(str(values[i]))
        r.font.size = Pt(9)
        r.font.name = "Segoe UI"
        r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

# ==============================================================================
# DOCUMENT 1: VOTER USER MANUAL
# ==============================================================================
def build_voter_manual():
    print("Building voter_manual.docx...")
    doc = Document()
    
    # Page setup - 0.75 in margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)

    # Title Page / Cover Section
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(10)
    p_meta.paragraph_format.space_after = Pt(4)
    r_badge = p_meta.add_run("OFFICIAL ELECTORAL SENSITIZATION & USER GUIDE")
    r_badge.bold = True
    r_badge.font.size = Pt(11)
    r_badge.font.name = "Segoe UI"
    r_badge.font.color.rgb = RGBColor.from_string(PRIMARY_INDIGO)

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("NECO MULTIPURPOSE COOPERATIVE SOCIETY\nELECTRONIC VOTING PORTAL")
    r_title.bold = True
    r_title.font.size = Pt(24)
    r_title.font.name = "Segoe UI"
    r_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(16)
    r_sub = p_sub.add_run("Comprehensive Voter User Manual: Contact Registration, Strict Device Accreditation & Cryptographic Ballot Casting")
    r_sub.font.size = Pt(13)
    r_sub.font.name = "Segoe UI"
    r_sub.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    # Document Information Box
    info_tbl = doc.add_table(rows=4, cols=2)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w = [2.0, 4.5]
    info_data = [
        ("Application System", "NECO MCS Electronic Voting Web Application (v2.4)"),
        ("Official Portal URL", "https://www.onlinevoter.netlify.app"),
        ("Intended Audience", "All Accredited NECO Cooperative Members / Eligible Voters"),
        ("Published Version", "Official Release — Election Cycle 2026"),
    ]
    for row_idx, (k, v) in enumerate(info_data):
        row = info_tbl.rows[row_idx]
        style_table_header(row, col_w, [k, v]) if row_idx == 99 else add_table_row(row, col_w, [k, v], is_even=(row_idx % 2 == 1))
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string(PRIMARY_INDIGO)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --------------------------------------------------------------------------
    # 1. Introduction & Security Architecture
    # --------------------------------------------------------------------------
    add_heading_1(doc, "1. Introduction & System Overview")
    add_body_p(doc, "Welcome to the official NECO Multipurpose Cooperative Society (NECO MCS) Electronic Voting System. This portal has been engineered to deliver a modern, transparent, and cryptographically verified election process for all cooperative members.", "Welcome: ")
    add_body_p(doc, "The voting platform eliminates paper ballots and manual queueing by enabling secure digital voting from any smartphone or computer. To protect electoral integrity and eliminate vote tampering, the application employs a mandatory 3-step security framework:")
    
    add_bullet_point(doc, "Voters confirm their identity using their official 4-digit MCS code and register their official email and telephone number via 6-digit One-Time Password (OTP) validation.", "Step 1 (Contact Update): ")
    add_bullet_point(doc, "Voters bind their physical smartphone or laptop browser cryptographically to their account. Ballots can strictly only be submitted from this accredited device.", "Step 2 (Accreditation): ")
    add_bullet_point(doc, "Voters authenticate on election day with a single-use passcode, inspect verified candidate photos and manifestos, submit their choices, and receive an immutable SHA-256 digital audit receipt.", "Step 3 (Election Day Voting): ")

    add_callout(
        doc,
        "STRICT LIGHT THEME INTERFACE & MOBILE ACCESSIBILITY",
        "The entire application has been redesigned in a high-contrast Light Theme (crisp white cards, slate background, and large bold typography) for optimal legibility under sunlight or on smartphone screens.",
        border_color=PRIMARY_INDIGO,
        bg_color="EEF2FF",
        prefix="INTERFACE"
    )

    # --------------------------------------------------------------------------
    # 2. Step 1: Contact Update & Dispute Resolution
    # --------------------------------------------------------------------------
    add_heading_1(doc, "2. Step 1: Contact Update & Verification")
    add_body_p(doc, "The first step for every voter is to verify and update their official contact destinations on the portal. Because all authentication codes (OTPs) and election passcodes are delivered via email and SMS, your contact information must be validated in advance.", "Purpose: ")
    
    add_heading_2(doc, "2.1 Accessing the Contact Update Page")
    add_bullet_point(doc, "Open your preferred mobile or desktop browser (Google Chrome, Microsoft Edge, or Apple Safari).")
    add_bullet_point(doc, "Navigate to the official address: www.onlinevoter.netlify.app/#/contact-update")
    add_bullet_point(doc, "Enter your 4-digit NECO MCS Member Code (e.g. 0001) in the voter lookup field.")
    add_bullet_point(doc, "Click Find My Profile. The portal immediately queries the master cooperative register and retrieves your verified full name (e.g., John Doe).")

    add_figure_image(doc, "voter_contact_lookup.png", "Figure 1: Contact Update Portal — Voter Profile Lookup & Official MCS Verification")

    add_heading_2(doc, "2.2 Registering Contact Details & Entering OTP")
    add_body_p(doc, "If your profile does not yet have an email address or telephone number registered, the form fields will unlock for input:")
    add_bullet_point(doc, "Enter your official cooperative email address (e.g. john.doe@neco.gov.ng).", "Email Address: ")
    add_bullet_point(doc, "Enter your active mobile phone number with Nigerian country format (e.g. 0803 123 4567).", "Mobile Phone: ")
    add_bullet_point(doc, "Click Submit & Request OTP. A 6-digit verification passcode is instantly transmitted to your provided email address via secure Google SMTP.", "OTP Dispatch: ")
    add_bullet_point(doc, "Check your email inbox (and spam/junk folder). Type the 6 digits into the large glowing OTP input boxes. The system validates each digit in real-time.", "Passcode Entry: ")

    add_figure_image(doc, "voter_contact_otp.png", "Figure 2: Contact Verification — 6-Digit One-Time Passcode (OTP) Input Simulation")

    add_callout(
        doc,
        "RECORD LOCKING POLICY FOR VOTER PROTECTION",
        "Once your email and telephone number are confirmed with OTP, the records are permanently LOCKED on the portal. Neither the voter nor an unauthorized third party can edit these details directly. This tamper-proof safeguard prevents malicious account takeovers.",
        border_color=EMERALD_GREEN,
        bg_color="ECFDF5",
        prefix="SECURITY"
    )

    add_heading_2(doc, "2.3 What To Do If Your Details Are Locked or Incorrect (Raising a Dispute)")
    add_body_p(doc, "If you find that your email address is misspelled, your phone number has changed, or another person's details are associated with your MCS code, you cannot edit them on the form. Instead, use the built-in Dispute Resolution feature:")
    add_bullet_point(doc, "Locate the amber warning callout at the top of the contact card stating 'Need to update existing details?'")
    add_bullet_point(doc, "Click the red Raise Dispute button. An animated bottom-sheet modal will slide into view.")
    add_bullet_point(doc, "Select your dispute reason from the dropdown: Incorrect Email Address, Lost Phone Number / New Line, or Name Discrepancy.")
    add_bullet_point(doc, "Provide your requested correct destination and a brief explanation.")
    add_bullet_point(doc, "Click Submit Dispute. An official ticket (e.g. DISP-2026-0041) is dispatched to the Electoral Committee administrative queue for verification and override.", "Ticket Generation: ")

    add_figure_image(doc, "voter_dispute.png", "Figure 3: Raising a Contact Dispute — Administrative Inquiry & Resolution Modal")

    # --------------------------------------------------------------------------
    # 3. Step 2: Voter Accreditation & Strict Device Binding
    # --------------------------------------------------------------------------
    add_heading_1(doc, "3. Step 2: Voter Accreditation & Strict Device Binding")
    add_body_p(doc, "Accreditation is the mandatory legal confirmation that certifies you as an eligible voter and cryptographically binds your account to your physical hardware device.", "Overview: ")
    
    add_heading_2(doc, "3.1 Accreditation Procedure")
    add_bullet_point(doc, "Navigate to the Accreditation portal: www.onlinevoter.netlify.app/#/accreditation")
    add_bullet_point(doc, "Type your 4-digit MCS number (0001) and click Verify Record.")
    add_bullet_point(doc, "Your masked email destination (jo***e@neco.gov.ng) will appear. Confirm that this is your account.")
    add_bullet_point(doc, "Click Request Accreditation Passcode. A dedicated accreditation OTP is sent to your registered destinations.")
    add_bullet_point(doc, "Enter the 6-digit OTP passcode. Once verified, the system generates a cryptographic hardware fingerprint combining your browser runtime, OS architecture, and device entropy.")
    add_bullet_point(doc, "The portal displays the official confirmation message:", "Confirmation Message: ")

    add_callout(
        doc,
        "OFFICIAL SYSTEM ACCREDITATION CONFIRMATION",
        "\"you have been successfully accredited for the NECO MCS election, wait for further instruction for voting.\"\n\nYour account is now bound to this smartphone or computer. You must use this exact device on election day to cast your ballot.",
        border_color=EMERALD_GREEN,
        bg_color="ECFDF5",
        prefix="CONFIRMATION"
    )

    add_figure_image(doc, "voter_accreditation.png", "Figure 4: Voter Accreditation Complete — Hardware Device Bound & Verified")

    add_heading_2(doc, "3.2 Hardware Device Binding Protection")
    add_body_p(doc, "Why does NECO MCS enforce strict device binding? This protocol completely eliminates bulk voting fraud, proxy voting, and ballot stuffing:")
    add_bullet_point(doc, "Even if a third party obtains your MCS code and password, they CANNOT vote from their device because the hardware fingerprint will not match.", "Stolen Passcode Defense: ")
    add_bullet_point(doc, "An individual cannot collect multiple voter logins and cast 50 votes from a single laptop or phone.", "Anti-Bulk Stuffing: ")
    add_bullet_point(doc, "If an unauthorized device attempts to log into an accredited voter's ballot, the system immediately rejects the connection with a Device Mismatch Lock Alert.", "Hardware Enforcement: ")

    add_figure_image(doc, "voter_device_mismatch.png", "Figure 5: Security Enforcement — Hardware Device Mismatch Lockout")

    # --------------------------------------------------------------------------
    # 4. Step 3: Election Day Voting & Digital Ballot
    # --------------------------------------------------------------------------
    add_heading_1(doc, "4. Step 3: Election Day Voting & Cryptographic Receipt")
    add_body_p(doc, "When the Electoral Committee opens voting on election day, accredited voters can access their personalized digital ballot and cast their votes.", "Election Day: ")

    add_heading_2(doc, "4.1 Election Day Login")
    add_bullet_point(doc, "Ensure you are using your accredited smartphone or computer.")
    add_bullet_point(doc, "Visit: www.onlinevoter.netlify.app/#/election")
    add_bullet_point(doc, "Check that the header displays the green pulsing POLLS OPEN live badge.")
    add_bullet_point(doc, "Enter your MCS Number (0001) and request your voting passcode.")
    add_bullet_point(doc, "Type the 6-digit election OTP passcode delivered to your email/phone.")
    add_bullet_point(doc, "Your Voter Dashboard unlocks with a welcome banner: 'Welcome, John Doe (MCS #0001)'. Click Proceed to Ballot.", "Dashboard Unlock: ")

    add_figure_image(doc, "voter_mobile_otp.png", "Figure 6: Mobile Election Day Login — Live Polls Status & Voting Passcode Entry")

    add_heading_2(doc, "4.2 Ballot Navigation & Candidate Photo Lightbox Inspection")
    add_body_p(doc, "The ballot organizes contested positions into clean, executive categories (e.g., President, General Secretary, Financial Secretary):")
    add_bullet_point(doc, "Select a contested office category to reveal the standing candidates.")
    add_bullet_point(doc, "Each candidate displays their full legal name, department, candidate code (#PRES-01), and portrait photo.")
    add_bullet_point(doc, "Tap any candidate's photo card to open the Enlarged Photo Lightbox & Manifesto Modal. Here, you can review their high-resolution official portrait, key policy manifesto points, and election credentials.", "Candidate Lightbox: ")
    add_bullet_point(doc, "Click Vote for [Candidate Name]. The candidate card highlights in emerald green with a 'Selected' confirmation badge.")

    add_figure_image(doc, "voter_mobile_ballot.png", "Figure 7: Mobile Ballot Navigation — Candidate Selection & Enlarged Photo Lightbox Modal")

    add_heading_2(doc, "4.3 Ballot Submission & SHA-256 Cryptographic Receipt")
    add_body_p(doc, "After making your selections across all positions, navigate to the ballot confirmation screen:")
    add_bullet_point(doc, "Review your selections carefully on the summary screen.")
    add_bullet_point(doc, "Click the emerald Cast Ballot button to finalize your vote.")
    add_bullet_point(doc, "The category immediately locks permanently: VOTED — Category Locked. Votes cannot be edited or retracted once cast.", "Permanent Lock: ")
    add_bullet_point(doc, "The portal instantly calculates and displays your official SHA-256 Cryptographic Audit Receipt (e.g. 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069).", "Audit Receipt: ")
    add_bullet_point(doc, "Take a screenshot or copy this hash string. You can use it after the election to mathematically verify that your ballot was counted in the final tally.", "Voter Audit: ")

    add_figure_image(doc, "voter_receipt.png", "Figure 8: Ballot Confirmation — Permanent Category Lock & SHA-256 Cryptographic Receipt")

    # --------------------------------------------------------------------------
    # 5. Frequently Asked Questions (FAQ) & Support
    # --------------------------------------------------------------------------
    add_heading_1(doc, "5. Troubleshooting & Frequently Asked Questions")
    
    add_heading_3(doc, "Q1: What should I do if my One-Time Passcode (OTP) does not arrive?")
    add_body_p(doc, "First, check your email Spam, Junk, and Promotions folders. If the OTP is still missing after 60 seconds, click the 'Resend Code' button. Ensure that your phone number has cellular network reception.")

    add_heading_3(doc, "Q2: I lost my smartphone after accrediting. How can I vote on election day?")
    add_body_p(doc, "Because of Strict Device Binding, a new phone cannot vote on your account automatically. You must immediately contact the NECO MCS Electoral Committee with valid NECO staff identification. An administrator can execute an official 'Reverse Accreditation' on your profile, enabling you to accredit your new device safely.")

    add_heading_3(doc, "Q3: Can an administrator or returning officer see which candidate I voted for?")
    add_body_p(doc, "No. The system uses cryptographic zero-knowledge ballot separation. Your identity (MCS #0001) is recorded as 'HAS_VOTED = TRUE' to prevent duplicate voting, while the vote tokens are detached and encrypted into an anonymous Merkle tree.")

    add_heading_3(doc, "Q4: Official Electoral Support Contacts")
    add_bullet_point(doc, "e-voting-support@neco.gov.ng", "Helpdesk Email: ")
    add_bullet_point(doc, "+234 (0) 803 000 1234 / +234 (0) 802 000 5678", "Electoral Committee Hotlines: ")
    add_bullet_point(doc, "NECO Headquarters, Minna, Niger State, Nigeria", "Physical Location: ")

    # Save voter manual
    voter_path_be = os.path.join(OUTPUT_DIR, "voter_manual.docx")
    doc.save(voter_path_be)
    print(f"Saved: {voter_path_be}")
    return voter_path_be

# ==============================================================================
# DOCUMENT 2: ADMIN USER MANUAL
# ==============================================================================
def build_admin_manual():
    print("Building admin_manual.docx...")
    doc = Document()
    
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)

    # Title Page / Cover Section
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(10)
    p_meta.paragraph_format.space_after = Pt(4)
    r_badge = p_meta.add_run("OFFICIAL ELECTORAL COMMITTEE & SYSTEM OPERATIONS GUIDE")
    r_badge.bold = True
    r_badge.font.size = Pt(11)
    r_badge.font.name = "Segoe UI"
    r_badge.font.color.rgb = RGBColor.from_string(PRIMARY_INDIGO)

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("NECO MULTIPURPOSE COOPERATIVE SOCIETY\nADMINISTRATIVE OPERATIONS MANUAL")
    r_title.bold = True
    r_title.font.size = Pt(24)
    r_title.font.name = "Segoe UI"
    r_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(16)
    r_sub = p_sub.add_run("Standard Operating Procedures: Election Control, Single Session Security, URL Locks, Voter Register, Dispute Resolution & Live Tallies")
    r_sub.font.size = Pt(13)
    r_sub.font.name = "Segoe UI"
    r_sub.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    # Information Box
    info_tbl = doc.add_table(rows=4, cols=2)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w = [2.2, 4.3]
    info_data = [
        ("Administrative Console", "NECO MCS Admin Portal (Single-Session Protected)"),
        ("Admin Portal URL", "https://www.onlinevoter.netlify.app/#/admin/login"),
        ("Authorized Roles", "Super Admin, Electoral Committee Admin, Returning Officers"),
        ("Security Classification", "RESTRICTED — OFFICIAL ELECTORAL USE ONLY"),
    ]
    for row_idx, (k, v) in enumerate(info_data):
        row = info_tbl.rows[row_idx]
        add_table_row(row, col_w, [k, v], is_even=(row_idx % 2 == 1))
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string(PRIMARY_INDIGO)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --------------------------------------------------------------------------
    # 1. Governance & Single Session Security Policy
    # --------------------------------------------------------------------------
    add_heading_1(doc, "1. Admin Portal Access & Single Active Session Security")
    add_body_p(doc, "Access to the NECO MCS Administrative Console is strictly restricted to designated Electoral Committee officers and returning administrators. All administrative activities are tracked in an immutable, cryptographically sealed security audit log.", "Overview: ")

    add_heading_2(doc, "1.1 Single Active Session Enforcement")
    add_body_p(doc, "To prevent credential sharing, unauthorized takeover, and administrative conflicts during live elections, the backend enforces a Strict Single Active Session Policy:")
    add_bullet_point(doc, "Only ONE active administrator session is permitted in the system at any given moment.", "One Session Rule: ")
    add_bullet_point(doc, "When an administrator logs in, an exclusive cryptographically signed hardware session token is registered in the database.", "Exclusive Lock: ")
    add_bullet_point(doc, "If a second person attempts to visit the admin login page while an admin session is active, the portal displays a prominent security alert and automatically disables the 'Sign in to Admin Portal' button.", "Concurrent Lockout: ")
    add_bullet_point(doc, "Administrators MUST click 'Logout' in the top right profile menu when exiting to cleanly release the session lock for colleagues.", "Mandatory Logout: ")

    add_figure_image(doc, "admin_login_screen.png", "Figure 1: Admin Portal Login — Active Single Session Warning & Disabled Sign-In Button")

    add_callout(
        doc,
        "EMERGENCY SESSION OVERRIDE PROTOCOL",
        "If an administrator accidentally closes their browser tab without clicking Logout, or experiences a sudden computer crash, the active session will persist until its server-side TTL expiry (30 minutes). A Super Admin can initiate an authorized session flush via backend CLI if emergency takeover is required.",
        border_color=AMBER_WARNING,
        bg_color="FFFBEB",
        prefix="POLICY"
    )

    # --------------------------------------------------------------------------
    # 2. Admin Control Center & Dashboard
    # --------------------------------------------------------------------------
    add_heading_1(doc, "2. Admin Control Center & Dashboard Overview")
    add_body_p(doc, "Upon successful login, administrators arrive at the central Admin Control Center. This console provides a 360-degree real-time operational picture of the ongoing election cycle.", "Control Center: ")
    
    add_heading_2(doc, "2.1 Key Dashboard Metrics & Live Indicators")
    add_bullet_point(doc, "Displays the current number of registered cooperative members in the database (e.g. 4,850).", "All Registered Voters: ")
    add_bullet_point(doc, "Displays the count and percentage of voters who have completed Step 2 device binding (e.g. 3,920 voters / 80.8%).", "Accredited Voters: ")
    add_bullet_point(doc, "Shows the real-time count of ballots received across all positions.", "Ballots Cast: ")
    add_bullet_point(doc, "Calculates active turnout as a ratio of votes cast to accredited voters.", "Voter Turnout Rate: ")
    add_bullet_point(doc, "Instant one-click exports of the complete voter register in formatted CSV or signed PDF format for physical polling audit.", "Global Export Buttons: ")

    add_figure_image(doc, "admin_dashboard_screen.png", "Figure 2: Admin Control Center — Election Status, URL Locks Bar & Live Operational Metrics")

    # --------------------------------------------------------------------------
    # 3. Phased Lifecycle & Voter URL Locks
    # --------------------------------------------------------------------------
    add_heading_1(doc, "3. Election Phased Lifecycle & URL Locks Management")
    add_body_p(doc, "A critical responsibility of the Electoral Committee is regulating which portals voters can access at each stage of the election cycle. The NECO MCS platform features a Compact URL Locks Bar located at the top of the dashboard.", "URL Locks: ")
    
    # Table of phases
    phase_tbl = doc.add_table(rows=5, cols=4)
    phase_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w_p = [1.5, 1.5, 1.5, 2.0]
    headers_p = ["ELECTION PHASE", "CONTACT UPDATE", "ACCREDITATION", "ELECTION VOTING"]
    style_table_header(phase_tbl.rows[0], col_w_p, headers_p)
    
    phases_data = [
        ("Phase 1: Registration", "OPEN 🟢", "LOCKED 🔴", "LOCKED 🔴"),
        ("Phase 2: Accreditation", "OPEN 🟢", "OPEN 🟢", "LOCKED 🔴"),
        ("Phase 3: Election Day", "LOCKED 🔴", "LOCKED 🔴", "OPEN 🟢 (Live Polls)"),
        ("Phase 4: Concluded", "LOCKED 🔴", "LOCKED 🔴", "LOCKED 🔴 (Results Only)"),
    ]
    for row_idx, rdata in enumerate(phases_data):
        row = phase_tbl.rows[row_idx + 1]
        add_table_row(row, col_w_p, rdata, is_even=(row_idx % 2 == 1))

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_body_p(doc, "When an administrator clicks any URL lock button, a custom branded confirmation modal appears requiring explicit confirmation before the state changes. If a voter attempts to visit a locked URL, the portal informs them that the phase is closed.")

    # --------------------------------------------------------------------------
    # 4. Voters Register & User Management
    # --------------------------------------------------------------------------
    add_heading_1(doc, "4. Voters Register & User Management Console")
    add_body_p(doc, "The User Management module provides granular control over all voter accounts, administrator privileges, and accreditation statuses.", "Register Management: ")
    
    add_heading_2(doc, "4.1 Voter Record Operations")
    add_bullet_point(doc, "Query any voter instantly by MCS code (e.g. 0001), full legal name, email, or telephone number.", "Search & Filter: ")
    add_bullet_point(doc, "Click '+ Add Single Voter' to input an individual member's MCS number, full name, and role.", "Manual Voter Creation: ")
    add_bullet_point(doc, "Click 'Bulk Import CSV' to upload master staff spreadsheets. The system maps columns (mcs_number, full_name, email, phone) and automatically rejects duplicate MCS entries.", "Bulk CSV Ingestion: ")
    add_bullet_point(doc, "Upload a list of retired, resigned, or non-financial cooperative members to revoke voting privileges across the system in one click.", "Bulk Disqualification: ")

    add_heading_2(doc, "4.2 Reverse Accreditation Protocol (Device Recovery)")
    add_body_p(doc, "One of the most essential administrative workflows is Reversing Accreditation. If an accredited voter loses their phone, suffers hardware failure, or accidentally bound an unintended browser, they cannot vote from a new device because of strict device binding.")
    add_bullet_point(doc, "Locate the voter's record in the table using their MCS number.")
    add_bullet_point(doc, "Verify the voter's physical identity and official NECO staff credentials.")
    add_bullet_point(doc, "Click the red 'Reverse Accr.' button in the Actions column.")
    add_bullet_point(doc, "Confirm the prompt. The system purges the hardware UUID and resets the voter's status to 'PENDING 🟡'.", "Lock Release: ")
    add_bullet_point(doc, "The voter can now access /accreditation from their new device and complete accreditation fresh.", "Re-Accreditation: ")

    add_figure_image(doc, "admin_users_screen.png", "Figure 4: Voters Register & User Management Console — Search, Filters & Reverse Accreditation")

    # --------------------------------------------------------------------------
    # 5. Voter Disputes Queue & Resolution
    # --------------------------------------------------------------------------
    add_heading_1(doc, "5. Voter Contact Disputes Queue & Resolution")
    add_body_p(doc, "When voters raise a dispute from the contact update portal, the ticket arrives in the Admin Disputes Resolution Queue. This prevents unauthorized contact modifications while providing a clear administrative channel to resolve legitimate errors.", "Disputes: ")
    
    add_bullet_point(doc, "Review the ticket number (#DISP-2026-0041), voter name, and MCS code.")
    add_bullet_point(doc, "Examine the dispute category (e.g., Incorrect Email Address) and compare the existing locked record against the requested new destination.")
    add_bullet_point(doc, "Inspect the voter's written justification.")
    add_bullet_point(doc, "Click 'Approve & Update' to accept the change. The backend automatically overwrites the contact record with the verified destination and sends an alert email to the voter.", "Approval: ")
    add_bullet_point(doc, "Click 'Reject' if the request appears suspicious or unverified.", "Rejection: ")

    add_figure_image(doc, "admin_disputes_screen.png", "Figure 5: Voter Contact Disputes Queue — Inquiry Review, Verification & One-Click Overrides")

    # --------------------------------------------------------------------------
    # 6. Offices & Candidates Configuration
    # --------------------------------------------------------------------------
    add_heading_1(doc, "6. Contested Offices & Candidate Management")
    add_body_p(doc, "Administrators configure the structure of the election prior to opening the candidate nomination period.", "Offices & Candidates: ")

    add_heading_2(doc, "6.1 Contested Offices Setup")
    add_bullet_point(doc, "Create leadership positions: President (PRES), General Secretary (GSEC), Financial Secretary (FSEC), Treasurer (TREAS), etc.")
    add_bullet_point(doc, "Set 'Max Selections' (e.g., 1 for single-seat executive offices).")
    add_bullet_point(doc, "Configure ballot ordering so that higher executive offices appear at the top of the ballot.")

    add_figure_image(doc, "admin_offices_screen.png", "Figure 6: Contested Offices Management — Position Codes, Selection Limits & Ordering")

    add_heading_2(doc, "6.2 Candidate Nominations & Photo Lightbox Management")
    add_bullet_point(doc, "Register approved nominees under their respective offices.")
    add_bullet_point(doc, "Assign official candidate codes (e.g., #PRES-01 for Dr. Sarah Alabi, #PRES-02 for Mr. James Okafor).")
    add_bullet_point(doc, "Upload high-resolution official portraits. The portal automatically crops and optimizes images for crystal-clear display on both desktop and mobile screens.", "Photo Upload: ")
    add_bullet_point(doc, "Input candidate bios and election manifestos.")
    add_bullet_point(doc, "Click 'View Photo Lightbox' to inspect the exact modal preview that voters will see when clicking the candidate on their ballot.", "Preview Modal: ")

    add_figure_image(doc, "admin_candidates_screen.png", "Figure 7: Candidate Management — Verified Nominees, Manifesto Management & Photo Lightbox Modal")

    # --------------------------------------------------------------------------
    # 7. Live Results & Tally Monitoring
    # --------------------------------------------------------------------------
    add_heading_1(doc, "7. Live Election Monitoring & Results Tally")
    add_body_p(doc, "During the election window, returning officers can monitor live vote accumulation without compromising voter anonymity.", "Live Tallies: ")

    add_heading_2(doc, "7.1 Starting & Stopping the Election")
    add_bullet_point(doc, "When the appointed voting start time arrives, navigate to the Dashboard and click the emerald 'Start Voting Now' button.")
    add_bullet_point(doc, "Confirm the prompt. The election session status changes to 'ACTIVE 🟢', and accredited voters can immediately enter ballots.")
    add_bullet_point(doc, "When the scheduled closing time arrives, click the red 'Stop Voting Now' button. All active voting sessions terminate immediately, and further submissions are blocked.", "Closing Election: ")

    add_heading_2(doc, "7.2 Results Breakdown & Winner Declaration")
    add_bullet_point(doc, "Select any contested office from the dropdown selector (e.g., President).")
    add_bullet_point(doc, "Review candidate vote totals, percentage shares, and the leading winner badge.")
    add_bullet_point(doc, "The results are sealed with a cryptographic Merkle tree hash to guarantee that no votes were injected, deleted, or altered.", "Cryptographic Seal: ")
    add_bullet_point(doc, "Click 'Official Certificate (PDF)' to generate the formal NECO MCS Electoral Declaration Certificate for signing by returning officers.", "Official Certificate: ")

    add_figure_image(doc, "admin_results_screen.png", "Figure 8: Live Results Dashboard — Real-Time Vote Distribution & Winner Declaration")

    # --------------------------------------------------------------------------
    # 8. System Status & Security Audit Logs
    # --------------------------------------------------------------------------
    add_heading_1(doc, "8. System Status & Security Audit Trails")
    add_body_p(doc, "The System module monitors server infrastructure health and maintains an immutable audit record of every administrative action.", "System Health: ")

    add_bullet_point(doc, "FastAPI Backend API health status and response latency (typically under 30ms).", "API Health: ")
    add_bullet_point(doc, "PostgreSQL database connection pool health and query throughput.", "Database Cluster: ")
    add_bullet_point(doc, "Live status of the Single Active Session security policy.", "Session Monitor: ")
    add_bullet_point(doc, "Immutable audit trail recording operator usernames, client IP addresses, timestamps, event types (URL_LOCK_TOGGLE, DISPUTE_APPROVED, REVERSE_ACCREDITATION), and outcomes.", "Audit Log: ")

    add_figure_image(doc, "admin_system_screen.png", "Figure 9: System Status Monitor — Health Indicators & Immutable Security Audit Trail")

    # Save admin manual
    admin_path_be = os.path.join(OUTPUT_DIR, "admin_manual.docx")
    doc.save(admin_path_be)
    print(f"Saved: {admin_path_be}")
    return admin_path_be

if __name__ == "__main__":
    build_voter_manual()
    build_admin_manual()
    print("Both user manuals created successfully!")
