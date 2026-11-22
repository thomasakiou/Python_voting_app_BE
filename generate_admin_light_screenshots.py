import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"G:\Projects\voting-app\voting-app-BE\manual_screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"

def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_top_nav(d, width, active_tab="Dashboard"):
    # Browser chrome header / Top App bar
    d.rectangle([(0, 0), (width, 68)], fill="#FFFFFF", outline="#E2E8F0", width=1)
    
    # Brand logo & title
    d.rounded_rectangle([(24, 14), (64, 54)], radius=12, fill="#4F46E5")
    d.text((36, 18), "🗳️", font=font(FONT_REG, 20), fill="#FFFFFF")
    
    d.text((78, 16), "NECO MCS", font=font(FONT_BOLD, 17), fill="#0F172A")
    d.text((78, 38), "ADMIN CONTROL PORTAL", font=font(FONT_BOLD, 11), fill="#6366F1")
    
    # Active portal status pill
    d.rounded_rectangle([(300, 20), (450, 48)], radius=20, fill="#ECFDF5", outline="#A7F3D0", width=1)
    d.ellipse([(315, 31), (323, 39)], fill="#10B981")
    d.text((332, 25), "PORTAL SECURE", font=font(FONT_BOLD, 12), fill="#065F46")
    
    # Navigation links
    tabs = ["Dashboard", "Voters Register", "Offices", "Candidates", "Live Results", "System"]
    start_x = 480
    for t in tabs:
        is_active = (t == active_tab)
        w_t = len(t) * 9 + 18
        if is_active:
            d.rounded_rectangle([(start_x, 18), (start_x + w_t, 50)], radius=10, fill="#EEF2FF", outline="#C7D2FE", width=1)
            d.text((start_x + 9, 25), t, font=font(FONT_BOLD, 13), fill="#4338CA")
        else:
            d.text((start_x + 9, 25), t, font=font(FONT_BOLD, 13), fill="#64748B")
        start_x += w_t + 12

    # Admin Profile Pill
    d.rounded_rectangle([(width - 240, 16), (width - 24, 52)], radius=18, fill="#F8FAFC", outline="#E2E8F0", width=1)
    d.ellipse([(width - 232, 22), (width - 204, 50)], fill="#4F46E5")
    d.text((width - 224, 27), "SA", font=font(FONT_BOLD, 12), fill="#FFFFFF")
    d.text((width - 194, 20), "Super Admin", font=font(FONT_BOLD, 13), fill="#0F172A")
    d.text((width - 194, 36), "1 Active Session", font=font(FONT_REG, 11), fill="#10B981")

# ==============================================================================
# 1. ADMIN DASHBOARD OVERVIEW
# ==============================================================================
def create_admin_dashboard_screen():
    W, H = 1280, 850
    img = Image.new("RGB", (W, H), color="#F8FAFC")
    d = ImageDraw.Draw(img)
    draw_top_nav(d, W, "Dashboard")
    
    # Header Banner & Title
    d.text((40, 90), "Admin Control Center", font=font(FONT_BOLD, 28), fill="#0F172A")
    d.text((40, 130), "Real-time NECO MCS Election control, live voting stream, and voter turnout analysis.", font=font(FONT_REG, 15), fill="#64748B")
    
    # Export buttons
    d.rounded_rectangle([(870, 95), (1050, 140)], radius=12, fill="#FFFFFF", outline="#CBD5E1", width=1)
    d.text((885, 107), "📊 Export Voters (CSV)", font=font(FONT_BOLD, 13), fill="#0F172A")
    
    d.rounded_rectangle([(1065, 95), (1240, 140)], radius=12, fill="#FFFFFF", outline="#CBD5E1", width=1)
    d.text((1080, 107), "📑 Export Voters (PDF)", font=font(FONT_BOLD, 13), fill="#DC2626")
    
    # URL Locks Bar
    d.rounded_rectangle([(40, 165), (1240, 225)], radius=16, fill="#FFFFFF", outline="#E2E8F0", width=1)
    d.text((60, 185), "🔒 Voter URL Locks:", font=font(FONT_BOLD, 14), fill="#334155")
    
    # Lock pills
    # 1. Contact Update
    d.rounded_rectangle([(230, 178), (480, 212)], radius=10, fill="#ECFDF5", outline="#A7F3D0", width=1)
    d.ellipse([(242, 191), (250, 199)], fill="#10B981")
    d.text((258, 186), "Contact Update: Open (Unlocked)", font=font(FONT_BOLD, 12), fill="#065F46")
    
    # 2. Accreditation
    d.rounded_rectangle([(500, 178), (750, 212)], radius=10, fill="#ECFDF5", outline="#A7F3D0", width=1)
    d.ellipse([(512, 191), (520, 199)], fill="#10B981")
    d.text((528, 186), "Accreditation: Open (Unlocked)", font=font(FONT_BOLD, 12), fill="#065F46")
    
    # 3. Election Voting
    d.rounded_rectangle([(770, 178), (1020, 212)], radius=10, fill="#FEF2F2", outline="#FECACA", width=1)
    d.ellipse([(782, 191), (790, 199)], fill="#EF4444")
    d.text((798, 186), "Election Voting: Locked (Closed)", font=font(FONT_BOLD, 12), fill="#991B1B")
    
    d.rounded_rectangle([(1050, 178), (1220, 212)], radius=10, fill="#EEF2FF", outline="#C7D2FE", width=1)
    d.text((1065, 186), "Toggle URL Locks ⚙️", font=font(FONT_BOLD, 12), fill="#4338CA")

    # Election State Action Card
    d.rounded_rectangle([(40, 245), (1240, 395)], radius=24, fill="#1E293B")
    
    # Badge inside banner
    d.rounded_rectangle([(65, 270), (270, 300)], radius=15, fill="#334155")
    d.ellipse([(78, 281), (86, 289)], fill="#EF4444")
    d.text((95, 276), "ELECTION CLOSED / READY", font=font(FONT_BOLD, 11), fill="#F8FAFC")
    
    d.text((300, 276), "Live Total: 0 ballots cast", font=font(FONT_BOLD, 13), fill="#94A3B8")
    
    d.text((65, 315), "Election Session is Ready to Commence", font=font(FONT_BOLD, 26), fill="#FFFFFF")
    d.text((65, 355), "3,920 accredited voters are waiting. Click Start Voting Now to open the ballot portal and allow real-time voting.", font=font(FONT_REG, 15), fill="#CBD5E1")
    
    # Start Voting Emerald Button
    d.rounded_rectangle([(980, 285), (1210, 355)], radius=16, fill="#10B981")
    d.text((1010, 305), "▶ Start Voting Now", font=font(FONT_BOLD, 18), fill="#FFFFFF")

    # 4 Key Metrics Cards
    metrics = [
        ("TOTAL REGISTERED", "4,850", "All Eligible Voters", "#3B82F6", "#EFF6FF", "#BFDBFE"),
        ("ACCREDITED VOTERS", "3,920", "80.8% Accredited Rate", "#10B981", "#ECFDF5", "#A7F3D0"),
        ("BALLOTS CAST", "0", "Awaiting Start", "#6366F1", "#EEF2FF", "#C7D2FE"),
        ("VOTER TURNOUT", "0.0%", "Target: 90%+", "#F59E0B", "#FFFBEB", "#FDE68A"),
    ]
    
    card_w = 280
    start_x = 40
    for title, val, sub, col, bg_col, bdr_col in metrics:
        d.rounded_rectangle([(start_x, 415), (start_x + card_w, 535)], radius=20, fill="#FFFFFF", outline=bdr_col, width=2)
        # Colored left accent bar
        d.rounded_rectangle([(start_x, 415), (start_x + 8, 535)], radius=4, fill=col)
        
        d.text((start_x + 22, 430), title, font=font(FONT_BOLD, 12), fill=col)
        d.text((start_x + 22, 452), val, font=font(FONT_BOLD, 36), fill="#0F172A")
        d.text((start_x + 22, 502), sub, font=font(FONT_REG, 13), fill="#64748B")
        start_x += card_w + 26

    # Recent Live Ballots Activity Stream (Table card)
    d.rounded_rectangle([(40, 555), (1240, 820)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    
    d.text((65, 575), "Live Ballot Cast Feed", font=font(FONT_BOLD, 18), fill="#0F172A")
    d.text((65, 602), "Real-time feed showing voter usernames (MCS Code) and cast ballots across contested offices.", font=font(FONT_REG, 13), fill="#64748B")
    
    # Table header
    d.rectangle([(40, 635), (1240, 675)], fill="#F8FAFC")
    headers = [("TIMESTAMP", 65), ("USERNAME", 200), ("CONTESTED OFFICE", 380), ("CANDIDATE VOTED", 640), ("RECEIPT HASH", 920), ("STATUS", 1120)]
    for h, x in headers:
        d.text((x, 646), h, font=font(FONT_BOLD, 12), fill="#64748B")
        
    rows = [
        ("15:42:08", "0001", "President", "Dr. Sarah Alabi", "MCS-7F83B165", "VOTED 🟢"),
        ("15:41:45", "0002", "President", "Dr. Sarah Alabi", "MCS-A92E4C10", "VOTED 🟢"),
        ("15:40:12", "0004", "General Secretary", "Mrs. Amina Yusuf", "MCS-382BC791", "VOTED 🟢"),
        ("15:38:50", "0007", "President", "Mr. James Okafor", "MCS-5100E9F2", "VOTED 🟢"),
    ]
    
    y = 680
    for t, u, off, cand, rcpt, st in rows:
        d.line([(40, y + 35), (1240, y + 35)], fill="#F1F5F9", width=1)
        d.text((65, y + 8), t, font=font(FONT_MONO, 12), fill="#64748B")
        
        # Username badge
        d.rounded_rectangle([(195, y + 4), (275, y + 30)], radius=6, fill="#EEF2FF", outline="#C7D2FE", width=1)
        d.text((215, y + 9), u, font=font(FONT_MONO, 13), fill="#4338CA")
        
        d.text((380, y + 8), off, font=font(FONT_REG, 13), fill="#334155")
        d.text((640, y + 8), cand, font=font(FONT_BOLD, 13), fill="#4F46E5")
        d.text((920, y + 8), rcpt, font=font(FONT_MONO, 12), fill="#059669")
        d.text((1120, y + 8), st, font=font(FONT_BOLD, 12), fill="#065F46")
        y += 36

    out_path = os.path.join(OUTPUT_DIR, "admin_dashboard_screen.png")
    img.save(out_path, quality=95)
    print(f"Created {out_path}")
    return out_path

# ==============================================================================
# 2. ADMIN USER & VOTER REGISTER MANAGEMENT
# ==============================================================================
def create_admin_users_screen():
    W, H = 1280, 850
    img = Image.new("RGB", (W, H), color="#F8FAFC")
    d = ImageDraw.Draw(img)
    draw_top_nav(d, W, "Voters Register")
    
    # Header & Action buttons
    d.text((40, 90), "Voters Register & User Management", font=font(FONT_BOLD, 28), fill="#0F172A")
    d.text((40, 130), "Manage eligible voter accounts, verify accreditation statuses, and reverse device locks if required.", font=font(FONT_REG, 15), fill="#64748B")
    
    # Top Action buttons
    d.rounded_rectangle([(700, 95), (860, 140)], radius=12, fill="#4F46E5")
    d.text((720, 107), "+ Add Single Voter", font=font(FONT_BOLD, 13), fill="#FFFFFF")
    
    d.rounded_rectangle([(875, 95), (1050, 140)], radius=12, fill="#FFFFFF", outline="#10B981", width=2)
    d.text((890, 107), "📥 Bulk Import CSV", font=font(FONT_BOLD, 13), fill="#047857")
    
    d.rounded_rectangle([(1065, 95), (1240, 140)], radius=12, fill="#FEF2F2", outline="#EF4444", width=2)
    d.text((1080, 107), "🚫 Bulk Disqualify", font=font(FONT_BOLD, 13), fill="#B91C1C")

    # Search & Filter Bar Card
    d.rounded_rectangle([(40, 160), (1240, 235)], radius=16, fill="#FFFFFF", outline="#E2E8F0", width=1)
    
    # Search input box
    d.rounded_rectangle([(60, 175), (460, 220)], radius=10, fill="#F8FAFC", outline="#CBD5E1", width=1)
    d.text((80, 187), "🔍 Search MCS #, Full Name, Email, Phone...", font=font(FONT_REG, 13), fill="#94A3B8")
    
    # Dropdown 1: Role
    d.rounded_rectangle([(480, 175), (660, 220)], radius=10, fill="#F8FAFC", outline="#CBD5E1", width=1)
    d.text((500, 187), "Role: All Users ▾", font=font(FONT_BOLD, 13), fill="#334155")
    
    # Dropdown 2: Accreditation Status
    d.rounded_rectangle([(680, 175), (920, 220)], radius=10, fill="#F8FAFC", outline="#CBD5E1", width=1)
    d.text((700, 187), "Accreditation: Accredited ▾", font=font(FONT_BOLD, 13), fill="#334155")
    
    # Dropdown 3: Status
    d.rounded_rectangle([(940, 175), (1100, 220)], radius=10, fill="#F8FAFC", outline="#CBD5E1", width=1)
    d.text((960, 187), "Status: Active ▾", font=font(FONT_BOLD, 13), fill="#334155")
    
    # Clear filters
    d.text((1125, 187), "Reset Filters ✕", font=font(FONT_BOLD, 12), fill="#6366F1")

    # Main Voter Table Card
    d.rounded_rectangle([(40, 255), (1240, 810)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    
    # Table Header Row
    d.rectangle([(40, 255), (1240, 305)], fill="#F8FAFC")
    cols = [
        ("MCS CODE", 65),
        ("FULL NAME", 180),
        ("EMAIL DESTINATION", 370),
        ("PHONE NUMBER", 590),
        ("ACCREDITATION", 770),
        ("STATUS", 940),
        ("ACTIONS", 1060),
    ]
    for c, x in cols:
        d.text((x, 273), c, font=font(FONT_BOLD, 12), fill="#64748B")

    voters = [
        ("0001", "John Doe", "john.doe@neco.gov.ng", "+234 803 123 4567", "ACCREDITED 🟢", "Active", ["Edit", "Reverse Accr."]),
        ("0002", "Mary Ibrahim", "mary.i@neco.gov.ng", "+234 802 987 6543", "ACCREDITED 🟢", "Active", ["Edit", "Reverse Accr."]),
        ("0003", "Usman Bello", "usman.b@neco.gov.ng", "+234 814 555 1212", "PENDING 🟡", "Active", ["Edit", "Accredit"]),
        ("0004", "Chinedu Okeke", "chinedu.o@neco.gov.ng", "+234 809 333 4444", "ACCREDITED 🟢", "Active", ["Edit", "Reverse Accr."]),
        ("0005", "Fatima Aliyu", "fatima.a@neco.gov.ng", "+234 705 111 2222", "PENDING 🟡", "Active", ["Edit", "Accredit"]),
        ("0006", "Emmanuel Adeyemi", "emmanuel.a@neco.gov.ng", "+234 803 888 9999", "ACCREDITED 🟢", "Active", ["Edit", "Reverse Accr."]),
        ("0007", "Grace Danjuma", "grace.d@neco.gov.ng", "+234 818 777 6666", "ACCREDITED 🟢", "Active", ["Edit", "Reverse Accr."]),
        ("0008", "Babajide Sanusi", "babajide.s@neco.gov.ng", "+234 802 444 3333", "PENDING 🟡", "Active", ["Edit", "Accredit"]),
    ]

    y = 315
    for mcs, name, email, phone, accr, st, acts in voters:
        d.line([(40, y + 48), (1240, y + 48)], fill="#F1F5F9", width=1)
        
        # MCS pill
        d.rounded_rectangle([(65, y + 6), (145, y + 36)], radius=6, fill="#EEF2FF", outline="#C7D2FE", width=1)
        d.text((82, y + 12), f"#{mcs}", font=font(FONT_MONO, 13), fill="#4338CA")
        
        d.text((180, y + 12), name, font=font(FONT_BOLD, 14), fill="#0F172A")
        d.text((370, y + 13), email, font=font(FONT_REG, 13), fill="#334155")
        d.text((590, y + 13), phone, font=font(FONT_REG, 13), fill="#64748B")
        
        # Accreditation badge
        is_acc = "🟢" in accr
        bg_a = "#ECFDF5" if is_acc else "#FFFBEB"
        bd_a = "#A7F3D0" if is_acc else "#FDE68A"
        tx_a = "#065F46" if is_acc else "#92400E"
        d.rounded_rectangle([(765, y + 6), (905, y + 36)], radius=8, fill=bg_a, outline=bd_a, width=1)
        d.text((780, y + 12), accr, font=font(FONT_BOLD, 11), fill=tx_a)
        
        # Status
        d.text((940, y + 13), st, font=font(FONT_REG, 13), fill="#0F172A")
        
        # Action buttons
        d.rounded_rectangle([(1055, y + 6), (1110, y + 36)], radius=6, fill="#F1F5F9", outline="#CBD5E1", width=1)
        d.text((1068, y + 12), "Edit", font=font(FONT_BOLD, 11), fill="#334155")
        
        if "Reverse Accr." in acts:
            d.rounded_rectangle([(1120, y + 6), (1225, y + 36)], radius=6, fill="#FEF2F2", outline="#FECACA", width=1)
            d.text((1128, y + 12), "Reverse Accr.", font=font(FONT_BOLD, 11), fill="#B91C1C")
        else:
            d.rounded_rectangle([(1120, y + 6), (1200, y + 36)], radius=6, fill="#ECFDF5", outline="#A7F3D0", width=1)
            d.text((1130, y + 12), "Accredit", font=font(FONT_BOLD, 11), fill="#047857")
            
        y += 58

    # Table footer pagination
    d.text((65, 765), "Showing 1 to 8 of 4,850 registered voters", font=font(FONT_REG, 13), fill="#64748B")
    d.rounded_rectangle([(1050, 755), (1120, 788)], radius=8, fill="#FFFFFF", outline="#CBD5E1", width=1)
    d.text((1065, 764), "Previous", font=font(FONT_BOLD, 11), fill="#64748B")
    d.rounded_rectangle([(1135, 755), (1175, 788)], radius=8, fill="#4F46E5")
    d.text((1150, 764), "1", font=font(FONT_BOLD, 11), fill="#FFFFFF")
    d.rounded_rectangle([(1185, 755), (1225, 788)], radius=8, fill="#FFFFFF", outline="#CBD5E1", width=1)
    d.text((1200, 764), "2", font=font(FONT_BOLD, 11), fill="#334155")

    out_path = os.path.join(OUTPUT_DIR, "admin_users_screen.png")
    img.save(out_path, quality=95)
    print(f"Created {out_path}")
    return out_path

# ==============================================================================
# 3. ADMIN VOTER DISPUTES PANEL
# ==============================================================================
def create_admin_disputes_screen():
    W, H = 1280, 850
    img = Image.new("RGB", (W, H), color="#F8FAFC")
    d = ImageDraw.Draw(img)
    draw_top_nav(d, W, "Voters Register")
    
    d.text((40, 90), "Voter Contact Disputes & Resolution Queue", font=font(FONT_BOLD, 28), fill="#0F172A")
    d.text((40, 130), "Review and act on contact change inquiries submitted by voters whose records were locked.", font=font(FONT_REG, 15), fill="#64748B")
    
    # 2 Summary Stats Cards
    d.rounded_rectangle([(40, 160), (320, 240)], radius=16, fill="#FFFBEB", outline="#FDE68A", width=2)
    d.text((65, 175), "PENDING DISPUTES", font=font(FONT_BOLD, 12), fill="#B45309")
    d.text((65, 195), "3 Inquiries", font=font(FONT_BOLD, 26), fill="#78350F")
    
    d.rounded_rectangle([(345, 160), (625, 240)], radius=16, fill="#ECFDF5", outline="#A7F3D0", width=2)
    d.text((370, 175), "RESOLVED DISPUTES", font=font(FONT_BOLD, 12), fill="#047857")
    d.text((370, 195), "18 Resolved", font=font(FONT_BOLD, 26), fill="#065F46")

    # Main Card
    d.rounded_rectangle([(40, 260), (1240, 820)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    
    # Dispute Item 1 (Detailed Card)
    d.rounded_rectangle([(65, 285), (1215, 490)], radius=16, fill="#F8FAFC", outline="#E2E8F0", width=1)
    d.rounded_rectangle([(85, 305), (250, 335)], radius=8, fill="#EEF2FF", outline="#C7D2FE", width=1)
    d.text((100, 312), "TICKET #DISP-2026-0041", font=font(FONT_MONO, 12), fill="#4338CA")
    
    d.rounded_rectangle([(265, 305), (420, 335)], radius=8, fill="#FEF3C7", outline="#FDE68A", width=1)
    d.text((280, 312), "PENDING REVIEW 🟡", font=font(FONT_BOLD, 11), fill="#92400E")
    
    d.text((85, 350), "Voter: John Doe (MCS #0001)", font=font(FONT_BOLD, 18), fill="#0F172A")
    d.text((85, 380), "Dispute Category: Incorrect Email Address", font=font(FONT_BOLD, 14), fill="#334155")
    d.text((85, 405), "Requested Email Update: john.doe@neco.gov.ng  |  Existing: j***e@oldmail.com (Locked)", font=font(FONT_REG, 14), fill="#047857")
    d.text((85, 435), "Voter Statement: 'My official cooperative email was misspelled in the old registry. Requesting update to official government domain.'", font=font(FONT_REG, 13), fill="#64748B")
    
    # Action Buttons on item 1
    d.rounded_rectangle([(880, 320), (1030, 370)], radius=12, fill="#10B981")
    d.text((898, 335), "✓ Approve & Update", font=font(FONT_BOLD, 13), fill="#FFFFFF")
    
    d.rounded_rectangle([(1045, 320), (1190, 370)], radius=12, fill="#FEF2F2", outline="#EF4444", width=1)
    d.text((1075, 335), "✕ Reject", font=font(FONT_BOLD, 13), fill="#DC2626")

    # Dispute Item 2
    d.rounded_rectangle([(65, 515), (1215, 720)], radius=16, fill="#F8FAFC", outline="#E2E8F0", width=1)
    d.rounded_rectangle([(85, 535), (250, 565)], radius=8, fill="#EEF2FF", outline="#C7D2FE", width=1)
    d.text((100, 542), "TICKET #DISP-2026-0042", font=font(FONT_MONO, 12), fill="#4338CA")
    
    d.rounded_rectangle([(265, 535), (420, 565)], radius=8, fill="#FEF3C7", outline="#FDE68A", width=1)
    d.text((280, 542), "PENDING REVIEW 🟡", font=font(FONT_BOLD, 11), fill="#92400E")
    
    d.text((85, 580), "Voter: Mary Ibrahim (MCS #0002)", font=font(FONT_BOLD, 18), fill="#0F172A")
    d.text((85, 610), "Dispute Category: Lost Phone Number / New Line", font=font(FONT_BOLD, 14), fill="#334155")
    d.text((85, 635), "Requested Phone Update: +234 802 987 6543  |  Existing: +234 803 *** 0000 (Locked)", font=font(FONT_REG, 14), fill="#047857")
    d.text((85, 665), "Voter Statement: 'Phone line was compromised. Registered new MTN official line with NECO staff committee.'", font=font(FONT_REG, 13), fill="#64748B")
    
    # Action Buttons on item 2
    d.rounded_rectangle([(880, 550), (1030, 600)], radius=12, fill="#10B981")
    d.text((898, 565), "✓ Approve & Update", font=font(FONT_BOLD, 13), fill="#FFFFFF")
    
    d.rounded_rectangle([(1045, 550), (1190, 600)], radius=12, fill="#FEF2F2", outline="#EF4444", width=1)
    d.text((1075, 565), "✕ Reject", font=font(FONT_BOLD, 13), fill="#DC2626")

    out_path = os.path.join(OUTPUT_DIR, "admin_disputes_screen.png")
    img.save(out_path, quality=95)
    print(f"Created {out_path}")
    return out_path

# ==============================================================================
# 4. ADMIN OFFICES & CANDIDATE MANAGEMENT
# ==============================================================================
def create_admin_offices_screen():
    W, H = 1280, 850
    img = Image.new("RGB", (W, H), color="#F8FAFC")
    d = ImageDraw.Draw(img)
    draw_top_nav(d, W, "Offices")
    
    d.text((40, 90), "Contested Offices Management", font=font(FONT_BOLD, 28), fill="#0F172A")
    d.text((40, 130), "Configure executive leadership positions, candidate limits, ballot display ordering, and voting rules.", font=font(FONT_REG, 15), fill="#64748B")
    
    # Add Office Button
    d.rounded_rectangle([(1060, 95), (1240, 140)], radius=12, fill="#4F46E5")
    d.text((1085, 107), "+ Add New Office", font=font(FONT_BOLD, 13), fill="#FFFFFF")

    # Table Card
    d.rounded_rectangle([(40, 160), (1240, 810)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    
    # Header
    d.rectangle([(40, 160), (1240, 210)], fill="#F8FAFC")
    cols = [
        ("OFFICE CODE", 65),
        ("OFFICE TITLE / DESCRIPTION", 220),
        ("MAX SELECTIONS", 580),
        ("CANDIDATES", 760),
        ("STATUS", 940),
        ("ACTIONS", 1080),
    ]
    for c, x in cols:
        d.text((x, 178), c, font=font(FONT_BOLD, 12), fill="#64748B")

    offices = [
        ("PRES", "President", "1 Candidate per Ballot", "2 Nominees", "Active 🟢"),
        ("VPRES", "Vice President", "1 Candidate per Ballot", "3 Nominees", "Active 🟢"),
        ("GSEC", "General Secretary", "1 Candidate per Ballot", "2 Nominees", "Active 🟢"),
        ("AGSEC", "Assistant General Secretary", "1 Candidate per Ballot", "2 Nominees", "Active 🟢"),
        ("FSEC", "Financial Secretary", "1 Candidate per Ballot", "2 Nominees", "Active 🟢"),
        ("TREAS", "Treasurer", "1 Candidate per Ballot", "2 Nominees", "Active 🟢"),
        ("PRO", "Public Relations Officer", "1 Candidate per Ballot", "3 Nominees", "Active 🟢"),
    ]

    y = 220
    for code, desc, max_sel, cand, st in offices:
        d.line([(40, y + 54), (1240, y + 54)], fill="#F1F5F9", width=1)
        
        # Code badge
        d.rounded_rectangle([(65, y + 10), (160, y + 42)], radius=8, fill="#EEF2FF", outline="#C7D2FE", width=1)
        d.text((82, y + 17), code, font=font(FONT_MONO, 13), fill="#4338CA")
        
        d.text((220, y + 16), desc, font=font(FONT_BOLD, 15), fill="#0F172A")
        d.text((580, y + 17), max_sel, font=font(FONT_REG, 13), fill="#64748B")
        d.text((760, y + 17), cand, font=font(FONT_BOLD, 13), fill="#059669")
        d.text((940, y + 17), st, font=font(FONT_BOLD, 12), fill="#065F46")
        
        # Actions
        d.rounded_rectangle([(1075, y + 10), (1135, y + 42)], radius=8, fill="#F8FAFC", outline="#CBD5E1", width=1)
        d.text((1090, y + 17), "Edit", font=font(FONT_BOLD, 11), fill="#334155")
        
        d.rounded_rectangle([(1145, y + 10), (1215, y + 42)], radius=8, fill="#FEF2F2", outline="#FECACA", width=1)
        d.text((1158, y + 17), "Delete", font=font(FONT_BOLD, 11), fill="#DC2626")
        
        y += 66

    out_path = os.path.join(OUTPUT_DIR, "admin_offices_screen.png")
    img.save(out_path, quality=95)
    print(f"Created {out_path}")
    return out_path

# ==============================================================================
# 5. ADMIN CANDIDATES MANAGEMENT & PHOTO LIGHTBOX
# ==============================================================================
def create_admin_candidates_screen():
    W, H = 1280, 850
    img = Image.new("RGB", (W, H), color="#F8FAFC")
    d = ImageDraw.Draw(img)
    draw_top_nav(d, W, "Candidates")
    
    d.text((40, 90), "Candidate Management & Verification", font=font(FONT_BOLD, 28), fill="#0F172A")
    d.text((40, 130), "Review verified nominees, upload high-resolution portraits, and manage election manifestos.", font=font(FONT_REG, 15), fill="#64748B")
    
    d.rounded_rectangle([(1050, 95), (1240, 140)], radius=12, fill="#4F46E5")
    d.text((1075, 107), "+ Add Candidate", font=font(FONT_BOLD, 13), fill="#FFFFFF")

    # Main Grid of Candidates (Left 2/3) + Candidate Photo Inspection Lightbox Modal (Right 1/3)
    # Left: Candidates List
    d.rounded_rectangle([(40, 160), (740, 810)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    d.text((65, 185), "Approved Nominees for President", font=font(FONT_BOLD, 18), fill="#0F172A")
    
    # Candidate 1 Card
    d.rounded_rectangle([(65, 230), (715, 380)], radius=16, fill="#EEF2FF", outline="#C7D2FE", width=2)
    d.ellipse([(85, 255), (155, 325)], fill="#4F46E5")
    d.text((105, 275), "SA", font=font(FONT_BOLD, 24), fill="#FFFFFF")
    
    d.text((175, 250), "Dr. Sarah Alabi", font=font(FONT_BOLD, 20), fill="#0F172A")
    d.text((175, 280), "Candidate Code: #PRES-01  |  Office: President", font=font(FONT_BOLD, 13), fill="#4338CA")
    d.text((175, 305), "Department: Quality Assurance & Standards Division", font=font(FONT_REG, 13), fill="#64748B")
    d.text((175, 335), "Status: Approved Nominee 🟢  |  Photo: Verified High-Res", font=font(FONT_BOLD, 12), fill="#065F46")
    
    # Candidate 2 Card
    d.rounded_rectangle([(65, 400), (715, 550)], radius=16, fill="#FFFFFF", outline="#E2E8F0", width=1)
    d.ellipse([(85, 425), (155, 495)], fill="#10B981")
    d.text((105, 445), "JO", font=font(FONT_BOLD, 24), fill="#FFFFFF")
    
    d.text((175, 420), "Mr. James Okafor", font=font(FONT_BOLD, 20), fill="#0F172A")
    d.text((175, 450), "Candidate Code: #PRES-02  |  Office: President", font=font(FONT_BOLD, 13), fill="#065F46")
    d.text((175, 475), "Department: Finance & Accounts Directorate", font=font(FONT_REG, 13), fill="#64748B")
    d.text((175, 505), "Status: Approved Nominee 🟢  |  Photo: Verified High-Res", font=font(FONT_BOLD, 12), fill="#065F46")

    # Candidate 3 Card
    d.rounded_rectangle([(65, 570), (715, 720)], radius=16, fill="#FFFFFF", outline="#E2E8F0", width=1)
    d.ellipse([(85, 595), (155, 665)], fill="#F59E0B")
    d.text((105, 615), "AY", font=font(FONT_BOLD, 24), fill="#FFFFFF")
    
    d.text((175, 590), "Mrs. Amina Yusuf", font=font(FONT_BOLD, 20), fill="#0F172A")
    d.text((175, 620), "Candidate Code: #GSEC-01  |  Office: General Secretary", font=font(FONT_BOLD, 13), fill="#D97706")
    d.text((175, 645), "Department: Examination Administration", font=font(FONT_REG, 13), fill="#64748B")
    d.text((175, 675), "Status: Approved Nominee 🟢  |  Photo: Verified High-Res", font=font(FONT_BOLD, 12), fill="#065F46")

    # Right: Candidate Photo Lightbox & Manifesto Preview Modal (Right column)
    d.rounded_rectangle([(770, 160), (1240, 810)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    d.text((795, 185), "Photo Inspection & Manifesto Modal", font=font(FONT_BOLD, 17), fill="#0F172A")
    d.text((795, 210), "Enlarged modal preview displayed to voters on click.", font=font(FONT_REG, 12), fill="#64748B")
    
    # Large Portrait Frame
    d.rounded_rectangle([(840, 245), (1170, 500)], radius=20, fill="#EEF2FF", outline="#C7D2FE", width=2)
    d.ellipse([(935, 290), (1075, 430)], fill="#4F46E5")
    d.text((975, 335), "SA", font=font(FONT_BOLD, 48), fill="#FFFFFF")
    d.text((915, 455), "Dr. Sarah Alabi", font=font(FONT_BOLD, 18), fill="#0F172A")
    d.text((945, 480), "#PRES-01", font=font(FONT_MONO, 14), fill="#4338CA")

    # Manifesto Box
    d.rounded_rectangle([(795, 520), (1215, 730)], radius=14, fill="#F8FAFC", outline="#E2E8F0", width=1)
    d.text((815, 535), "Candidate Manifesto & Agenda:", font=font(FONT_BOLD, 13), fill="#0F172A")
    d.text((815, 560), "1. Transparent Dividends Distribution Model", font=font(FONT_REG, 12), fill="#334155")
    d.text((815, 585), "2. Automated Loan Disbursement within 48 Hours", font=font(FONT_REG, 12), fill="#334155")
    d.text((815, 610), "3. Digitized Cooperative Savings & Retirement Tracker", font=font(FONT_REG, 12), fill="#334155")
    d.text((815, 635), "4. Cooperative Housing & Land Scheme Revival", font=font(FONT_REG, 12), fill="#334155")
    d.text((815, 665), "Verification Hash: sha256:d8a9f3b2...", font=font(FONT_MONO, 11), fill="#64748B")

    d.rounded_rectangle([(795, 745), (1215, 795)], radius=12, fill="#10B981")
    d.text((930, 762), "Verified Nominee Approved ✓", font=font(FONT_BOLD, 13), fill="#FFFFFF")

    out_path = os.path.join(OUTPUT_DIR, "admin_candidates_screen.png")
    img.save(out_path, quality=95)
    print(f"Created {out_path}")
    return out_path

# ==============================================================================
# 6. ADMIN ELECTION RESULTS & TALLY
# ==============================================================================
def create_admin_results_screen():
    W, H = 1280, 850
    img = Image.new("RGB", (W, H), color="#F8FAFC")
    d = ImageDraw.Draw(img)
    draw_top_nav(d, W, "Live Results")
    
    d.text((40, 90), "Live Election Results & Vote Tallies", font=font(FONT_BOLD, 28), fill="#0F172A")
    d.text((40, 130), "Cryptographically verified, real-time vote distribution across all contested leadership offices.", font=font(FONT_REG, 15), fill="#64748B")
    
    # Export Results
    d.rounded_rectangle([(875, 95), (1050, 140)], radius=12, fill="#FFFFFF", outline="#10B981", width=2)
    d.text((895, 107), "📊 Export Results (CSV)", font=font(FONT_BOLD, 13), fill="#047857")
    
    d.rounded_rectangle([(1065, 95), (1240, 140)], radius=12, fill="#FFFFFF", outline="#EF4444", width=2)
    d.text((1085, 107), "📑 Official Certificate (PDF)", font=font(FONT_BOLD, 13), fill="#B91C1C")

    # Office Selector Dropdown Pill
    d.rounded_rectangle([(40, 160), (400, 215)], radius=14, fill="#FFFFFF", outline="#CBD5E1", width=1)
    d.text((60, 175), "Office: President (PRES) ▾", font=font(FONT_BOLD, 16), fill="#0F172A")
    d.text((60, 195), "Total Ballots Counted: 3,420 votes", font=font(FONT_REG, 12), fill="#64748B")

    # Main Results Card
    d.rounded_rectangle([(40, 235), (1240, 810)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    
    d.text((70, 260), "Official Results Breakdown: Office of the President", font=font(FONT_BOLD, 20), fill="#0F172A")
    d.text((70, 290), "Winner is declared by majority vote in accordance with the NECO MCS Constitution.", font=font(FONT_REG, 14), fill="#64748B")
    
    # Candidate 1: Dr. Sarah Alabi (WINNER)
    d.rounded_rectangle([(70, 325), (1210, 480)], radius=16, fill="#ECFDF5", outline="#A7F3D0", width=2)
    d.ellipse([(95, 350), (165, 420)], fill="#10B981")
    d.text((115, 370), "SA", font=font(FONT_BOLD, 24), fill="#FFFFFF")
    
    d.text((185, 345), "Dr. Sarah Alabi (#PRES-01)", font=font(FONT_BOLD, 22), fill="#065F46")
    
    # Winner Badge
    d.rounded_rectangle([(520, 345), (710, 380)], radius=16, fill="#10B981")
    d.text((540, 353), "🏆 WINNER / LEADING", font=font(FONT_BOLD, 12), fill="#FFFFFF")
    
    d.text((185, 385), "Total Votes: 2,190 ballots", font=font(FONT_BOLD, 16), fill="#0F172A")
    d.text((450, 385), "Vote Share: 64.0%", font=font(FONT_BOLD, 16), fill="#047857")
    
    # Progress Bar Background
    d.rounded_rectangle([(185, 420), (1180, 455)], radius=10, fill="#D1FAE5")
    # Progress Bar Fill (64%)
    d.rounded_rectangle([(185, 420), (185 + int((1180 - 185) * 0.64), 455)], radius=10, fill="#10B981")
    d.text((205, 428), "64.0% of total presidential ballots", font=font(FONT_BOLD, 12), fill="#FFFFFF")

    # Candidate 2: Mr. James Okafor
    d.rounded_rectangle([(70, 505), (1210, 660)], radius=16, fill="#F8FAFC", outline="#E2E8F0", width=1)
    d.ellipse([(95, 530), (165, 600)], fill="#3B82F6")
    d.text((115, 550), "JO", font=font(FONT_BOLD, 24), fill="#FFFFFF")
    
    d.text((185, 525), "Mr. James Okafor (#PRES-02)", font=font(FONT_BOLD, 22), fill="#0F172A")
    d.text((185, 565), "Total Votes: 1,230 ballots", font=font(FONT_BOLD, 16), fill="#0F172A")
    d.text((450, 565), "Vote Share: 36.0%", font=font(FONT_BOLD, 16), fill="#2563EB")
    
    # Progress Bar Background
    d.rounded_rectangle([(185, 600), (1180, 635)], radius=10, fill="#E2E8F0")
    # Progress Bar Fill (36%)
    d.rounded_rectangle([(185, 600), (185 + int((1180 - 185) * 0.36), 635)], radius=10, fill="#3B82F6")
    d.text((205, 608), "36.0% of total presidential ballots", font=font(FONT_BOLD, 12), fill="#FFFFFF")

    # Bottom Audit seal
    d.text((70, 735), "🔒 Results Cryptographically Sealed: Merkle Tree Hash Verified  |  Timestamp: 16:00:00", font=font(FONT_MONO, 12), fill="#64748B")

    out_path = os.path.join(OUTPUT_DIR, "admin_results_screen.png")
    img.save(out_path, quality=95)
    print(f"Created {out_path}")
    return out_path

# ==============================================================================
# 7. ADMIN SYSTEM & SECURITY AUDIT MONITOR
# ==============================================================================
def create_admin_system_screen():
    W, H = 1280, 850
    img = Image.new("RGB", (W, H), color="#F8FAFC")
    d = ImageDraw.Draw(img)
    draw_top_nav(d, W, "System")
    
    d.text((40, 90), "System Status & Security Audit Log", font=font(FONT_BOLD, 28), fill="#0F172A")
    d.text((40, 130), "Monitor API health, database clusters, single session enforcement, and security event logs.", font=font(FONT_REG, 15), fill="#64748B")
    
    # 3 Health Cards
    health_metrics = [
        ("FASTAPI BACKEND", "ONLINE 🟢", "28ms Latency  •  v2.4.0", "#10B981", "#ECFDF5", "#A7F3D0"),
        ("DATABASE CLUSTER", "HEALTHY 🟢", "PostgreSQL Pool Active", "#3B82F6", "#EFF6FF", "#BFDBFE"),
        ("SESSION POLICY", "STRICT LOCK 🔒", "1 Admin Session Max", "#6366F1", "#EEF2FF", "#C7D2FE"),
    ]
    
    x = 40
    for name, st, desc, col, bg, bdr in health_metrics:
        d.rounded_rectangle([(x, 160), (x + 380, 260)], radius=16, fill=bg, outline=bdr, width=2)
        d.text((x + 20, 178), name, font=font(FONT_BOLD, 12), fill=col)
        d.text((x + 20, 200), st, font=font(FONT_BOLD, 24), fill="#0F172A")
        d.text((x + 20, 235), desc, font=font(FONT_REG, 13), fill="#64748B")
        x += 410

    # Audit Logs Table Card
    d.rounded_rectangle([(40, 280), (1240, 810)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1)
    d.text((65, 305), "Immutable Security Audit Trail", font=font(FONT_BOLD, 18), fill="#0F172A")
    d.text((65, 330), "Comprehensive log of administrative sessions, locks toggles, dispute resolutions, and ballot tallies.", font=font(FONT_REG, 13), fill="#64748B")
    
    # Table Header
    d.rectangle([(40, 360), (1240, 405)], fill="#F8FAFC")
    cols = [
        ("TIMESTAMP", 65),
        ("OPERATOR / IP", 230),
        ("EVENT CLASSIFICATION", 460),
        ("DETAILS / TARGET", 760),
        ("RESULT", 1080),
    ]
    for c, xp in cols:
        d.text((xp, 375), c, font=font(FONT_BOLD, 12), fill="#64748B")

    logs = [
        ("2026-11-12 15:42:10", "admin (197.210.64.12)", "ADMIN_LOGIN_SUCCESS", "Admin session initialized", "SUCCESS 🟢"),
        ("2026-11-12 15:40:02", "admin (197.210.64.12)", "URL_LOCK_TOGGLE", "Contact Update URL -> OPEN", "SUCCESS 🟢"),
        ("2026-11-12 15:38:15", "admin (197.210.64.12)", "DISPUTE_APPROVED", "Voter John Doe (#0001) email updated", "SUCCESS 🟢"),
        ("2026-11-12 15:30:44", "voter-system (API)", "ACCREDITATION_OTP", "Device fingerprint sha256:7f3b... bound", "SUCCESS 🟢"),
        ("2026-11-12 15:25:00", "system-daemon", "HEALTH_HEARTBEAT", "DB pool integrity verified", "SUCCESS 🟢"),
        ("2026-11-12 15:15:22", "admin (197.210.64.12)", "CANDIDATE_PHOTO_UPLOAD", "Uploaded photo for Dr. Sarah Alabi", "SUCCESS 🟢"),
        ("2026-11-12 15:02:18", "system-daemon", "SINGLE_SESSION_CHECK", "Blocked duplicate concurrent login attempt", "ENFORCED 🔒"),
    ]

    y = 415
    for ts, op, ev, det, res in logs:
        d.line([(40, y + 44), (1240, y + 44)], fill="#F1F5F9", width=1)
        d.text((65, y + 12), ts, font=font(FONT_MONO, 12), fill="#64748B")
        d.text((230, y + 12), op, font=font(FONT_BOLD, 13), fill="#0F172A")
        d.text((460, y + 12), ev, font=font(FONT_MONO, 12), fill="#4338CA")
        d.text((760, y + 12), det, font=font(FONT_REG, 13), fill="#334155")
        
        col_res = "#065F46" if "🟢" in res else "#4338CA"
        d.text((1080, y + 12), res, font=font(FONT_BOLD, 12), fill=col_res)
        y += 50

    out_path = os.path.join(OUTPUT_DIR, "admin_system_screen.png")
    img.save(out_path, quality=95)
    print(f"Created {out_path}")
    return out_path

if __name__ == "__main__":
    create_admin_dashboard_screen()
    create_admin_users_screen()
    create_admin_disputes_screen()
    create_admin_offices_screen()
    create_admin_candidates_screen()
    create_admin_results_screen()
    create_admin_system_screen()
    print("All light-theme admin screenshots generated successfully!")
