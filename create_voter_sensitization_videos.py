import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

OUTPUT_DIR = "sensitization_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font configurations
FONT_BOLD = "C:\\Windows\\Fonts\\segoeuib.ttf"
FONT_REGULAR = "C:\\Windows\\Fonts\\segoeui.ttf"
FONT_MONO = "C:\\Windows\\Fonts\\consola.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

WIDTH, HEIGHT = 1280, 720
FPS = 20

# Color Palette
BG_DARK = "#0B1120"
BG_CARD = "#1E293B"
BG_CARD_INNER = "#0F172A"
BORDER_COLOR = "#334155"
TEXT_WHITE = "#FFFFFF"
TEXT_SLATE = "#94A3B8"
ACCENT_BLUE = "#38BDF8"
ACCENT_INDIGO = "#6366F1"
ACCENT_GREEN = "#22C55E"
ACCENT_AMBER = "#F59E0B"
ACCENT_RED = "#EF4444"

# UI Helpers
def draw_browser_chrome(d, url):
    """Draw browser top bar with controls and URL."""
    d.rectangle([(0, 0), (WIDTH, 48)], fill="#1E293B")
    d.line([(0, 48), (WIDTH, 48)], fill="#334155", width=1)
    
    d.ellipse([(20, 18), (32, 30)], fill="#EF4444")
    d.ellipse([(40, 18), (52, 30)], fill="#F59E0B")
    d.ellipse([(60, 18), (72, 30)], fill="#22C55E")
    
    d.rounded_rectangle([(140, 10), (1000, 38)], radius=6, fill="#0F172A", outline="#475569", width=1)
    f_url = get_font(FONT_REGULAR, 14)
    d.text((155, 16), "🔒 https://", font=f_url, fill="#10B981")
    d.text((235, 16), url, font=f_url, fill="#E2E8F0")

def draw_cursor(d, x, y, clicking=False):
    """Draw realistic mouse cursor with click animation."""
    if clicking:
        d.ellipse([(x - 14, y - 14), (x + 14, y + 14)], fill=None, outline="#38BDF8", width=3)
    points = [(x, y), (x + 13, y + 13), (x + 6, y + 14), (x + 10, y + 23), (x + 6, y + 25), (x + 2, y + 16), (x - 1, y + 20)]
    d.polygon(points, fill="#FFFFFF", outline="#000000")

def draw_bottom_guide(d, step_label, title, description):
    """Draw educational guidance banner at bottom."""
    d.rounded_rectangle([(40, 630), (1240, 705)], radius=12, fill="#1E1B4B", outline="#4338CA", width=2)
    f_step = get_font(FONT_BOLD, 14)
    f_title = get_font(FONT_BOLD, 17)
    f_desc = get_font(FONT_REGULAR, 15)
    
    # Step badge
    d.rounded_rectangle([(55, 642), (160, 692)], radius=8, fill="#4338CA")
    d.text((70, 655), step_label, font=f_step, fill="#FFFFFF")
    
    d.text((180, 647), title, font=f_title, fill="#38BDF8")
    d.text((180, 672), description, font=f_desc, fill="#CBD5E1")

def make_title_card(title, subtitle, part_text):
    """Title slide."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color="#060913")
    d = ImageDraw.Draw(img)
    
    d.ellipse([(WIDTH//2 - 380, 70), (WIDTH//2 + 380, 390)], fill="#1E1B4B")
    d.ellipse([(WIDTH//2 - 260, 110), (WIDTH//2 + 260, 350)], fill="#312E81")
    
    f_pre = get_font(FONT_BOLD, 18)
    f_part = get_font(FONT_BOLD, 22)
    f_title = get_font(FONT_BOLD, 40)
    f_sub = get_font(FONT_REGULAR, 22)
    f_footer = get_font(FONT_REGULAR, 16)
    
    d.text((WIDTH//2 - 180, 150), "NECO MCS ELECTIONS 2026", font=f_pre, fill="#38BDF8")
    d.text((WIDTH//2 - 200, 200), part_text, font=f_part, fill="#A5B4FC")
    
    bbox = d.textbbox((0, 0), title, font=f_title)
    d.text(((WIDTH - (bbox[2] - bbox[0]))//2, 270), title, font=f_title, fill="#FFFFFF")
    
    bbox_s = d.textbbox((0, 0), subtitle, font=f_sub)
    d.text(((WIDTH - (bbox_s[2] - bbox_s[0]))//2, 345), subtitle, font=f_sub, fill="#94A3B8")
    
    d.rounded_rectangle([(WIDTH//2 - 180, 435), (WIDTH//2 + 180, 495)], radius=12, fill="#065F46", outline="#10B981", width=2)
    d.text((WIDTH//2 - 145, 452), "Official Voter Guide Video", font=get_font(FONT_BOLD, 20), fill="#6EE7B7")
    
    d.text((WIDTH//2 - 240, 620), "Protected by Device Binding Security & Google SMTP OTP", font=f_footer, fill="#64748B")
    return np.array(img)

def make_outro_card(title, tip):
    """Outro slide."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color="#060913")
    d = ImageDraw.Draw(img)
    
    f_title = get_font(FONT_BOLD, 36)
    f_tip_t = get_font(FONT_BOLD, 22)
    f_tip = get_font(FONT_REGULAR, 19)
    
    d.rounded_rectangle([(WIDTH//2 - 420, 170), (WIDTH//2 + 420, 480)], radius=20, fill="#1E293B", outline="#334155", width=2)
    d.ellipse([(WIDTH//2 - 35, 210), (WIDTH//2 + 35, 280)], fill="#065F46", outline="#10B981", width=3)
    d.text((WIDTH//2 - 14, 225), "✓", font=get_font(FONT_BOLD, 38), fill="#6EE7B7")
    
    bbox = d.textbbox((0, 0), title, font=f_title)
    d.text(((WIDTH - (bbox[2] - bbox[0]))//2, 305), title, font=f_title, fill="#FFFFFF")
    
    d.text((WIDTH//2 - 350, 375), "KEY TAKEAWAY FOR VOTERS:", font=f_tip_t, fill="#38BDF8")
    d.text((WIDTH//2 - 350, 410), tip, font=f_tip, fill="#E2E8F0")
    
    d.text((WIDTH//2 - 220, 620), "NECO MCS Electoral Committee  •  Integrity & Transparency", font=get_font(FONT_REGULAR, 16), fill="#64748B")
    return np.array(img)


# ==============================================================================
# VIDEO 1: CONTACT UPDATE PORTAL (/contact-update)
# ==============================================================================
def generate_video_1():
    print("Generating Video 1: Contact Update Portal...")
    video_path = os.path.join(OUTPUT_DIR, "video_1_contact_update.mp4")
    writer = imageio.get_writer(video_path, fps=FPS, codec="libx264", quality=8)
    
    # 1. Intro Card (2.5s = 50 frames)
    title_frame = make_title_card(
        "Voter Contact Registration",
        "How to add your email & phone or raise a dispute",
        "TUTORIAL PART 1 / 3"
    )
    for _ in range(50):
        writer.append_data(title_frame)
        
    url = "vmi2848672.contaboserver.net/contact-update"
    
    # Fonts
    f_page_h = get_font(FONT_BOLD, 26)
    f_page_s = get_font(FONT_REGULAR, 15)
    f_label = get_font(FONT_BOLD, 15)
    f_input = get_font(FONT_MONO, 18)
    f_btn = get_font(FONT_BOLD, 17)
    f_alert = get_font(FONT_REGULAR, 14)
    
    # 2. Scene: Enter MCS Number & Click Lookup (3.5s = 70 frames)
    mcs_seq = ["", "2", "26", "266", "2668", "2668", "2668"]
    for i in range(70):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        # Center Form Card
        d.rounded_rectangle([(WIDTH//2 - 280, 80), (WIDTH//2 + 280, 580)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        d.text((WIDTH//2 - 240, 110), "Voter Contact Registry", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 240, 148), "Enter your 4-digit MCS number to verify registration", font=f_page_s, fill=TEXT_SLATE)
        
        # Input Box
        d.text((WIDTH//2 - 240, 200), "MCS Number (4 Digits)", font=f_label, fill=TEXT_SLATE)
        d.rounded_rectangle([(WIDTH//2 - 240, 230), (WIDTH//2 + 240, 290)], radius=10, fill=BG_CARD_INNER, outline=ACCENT_INDIGO, width=2)
        
        mcs_text = mcs_seq[min(i // 10, len(mcs_seq) - 1)]
        cursor_blink = "|" if (i // 6) % 2 == 0 else ""
        d.text((WIDTH//2 - 215, 245), mcs_text + cursor_blink, font=f_input, fill="#38BDF8")
        
        # Button
        btn_fill = "#4338CA" if len(mcs_text) == 4 else "#334155"
        d.rounded_rectangle([(WIDTH//2 - 240, 320), (WIDTH//2 + 240, 380)], radius=12, fill=btn_fill)
        d.text((WIDTH//2 - 90, 338), "Lookup Profile →", font=f_btn, fill=TEXT_WHITE)
        
        # Educational Banner
        draw_bottom_guide(d, "STEP 1", "Enter Your 4-Digit MCS Number", "Your MCS number securely links to the official NECO MCS register.")
        
        # Cursor Animation
        cx = WIDTH//2 - 20 + int(min(i, 40) * 1.5)
        cy = 350
        draw_cursor(d, cx, cy, clicking=(i >= 50 and i <= 60))
        writer.append_data(np.array(img))
        
    # 3. Scene: Profile Display + Entering Missing Details (6s = 120 frames)
    email_seq = ["", "v", "vo", "vot", "voter", "voter.neco@gmail.com"]
    for i in range(120):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 320, 70), (WIDTH//2 + 320, 600)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        d.text((WIDTH//2 - 280, 95), "Verified Profile: A******* O*******", font=f_page_h, fill="#4ADE80")
        d.text((WIDTH//2 - 280, 130), "MCS-2668  •  Status: Eligible Member", font=f_page_s, fill=TEXT_SLATE)
        
        # Email Field (Active input)
        d.text((WIDTH//2 - 280, 170), "Register Email Address (For Voting OTP)", font=f_label, fill=TEXT_WHITE)
        d.rounded_rectangle([(WIDTH//2 - 280, 195), (WIDTH//2 + 280, 250)], radius=10, fill=BG_CARD_INNER, outline=ACCENT_INDIGO, width=1)
        em_text = email_seq[min(i // 20, len(email_seq) - 1)]
        d.text((WIDTH//2 - 260, 210), em_text, font=f_input, fill="#38BDF8")
        
        # Phone Field (Filled)
        d.text((WIDTH//2 - 280, 270), "Register Mobile Phone Number", font=f_label, fill=TEXT_WHITE)
        d.rounded_rectangle([(WIDTH//2 - 280, 295), (WIDTH//2 + 280, 350)], radius=10, fill=BG_CARD_INNER, outline="#475569", width=1)
        d.text((WIDTH//2 - 260, 310), "0803 123 4567", font=f_input, fill="#FCD34D")
        
        # Security Policy Notice
        d.rounded_rectangle([(WIDTH//2 - 280, 370), (WIDTH//2 + 280, 440)], radius=10, fill="#064E3B", outline="#059669", width=1)
        d.text((WIDTH//2 - 265, 382), "SECURITY POLICY: Anti-Hijacking Protection", font=get_font(FONT_BOLD, 14), fill="#34D399")
        d.text((WIDTH//2 - 265, 408), "Existing records cannot be modified directly. If details are incorrect, click 'Raise Dispute'.", font=f_alert, fill="#D1FAE5")
        
        # Action Buttons
        d.rounded_rectangle([(WIDTH//2 - 280, 465), (WIDTH//2 - 40, 520)], radius=10, fill="#B91C1C", outline="#DC2626", width=1)
        d.text((WIDTH//2 - 240, 483), "Raise Dispute", font=f_btn, fill=TEXT_WHITE)
        
        d.rounded_rectangle([(WIDTH//2 - 10, 465), (WIDTH//2 + 280, 520)], radius=10, fill="#4338CA", outline="#6366F1", width=1)
        d.text((WIDTH//2 + 30, 483), "Submit & Send OTP →", font=f_btn, fill=TEXT_WHITE)
        
        draw_bottom_guide(d, "STEP 2", "Enter Missing Contacts & Strict Immutability", "To protect your identity, pre-registered fields are locked. New data requires OTP verification.")
        
        # Cursor clicks Submit button
        draw_cursor(d, WIDTH//2 + 120, 490, clicking=(i >= 100))
        writer.append_data(np.array(img))
        
    # 4. Scene: Enter 6-Digit OTP (5s = 100 frames)
    digits = ["7", "4", "2", "9", "1", "8"]
    for i in range(100):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 280, 100), (WIDTH//2 + 280, 560)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        d.text((WIDTH//2 - 240, 140), "Enter 6-Digit Verification OTP", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 240, 180), "Dispatched to voter.neco@gmail.com via Google SMTP", font=f_page_s, fill=TEXT_SLATE)
        
        # 6 OTP boxes
        num_visible = min(i // 15, 6)
        for b_idx in range(6):
            bx = WIDTH//2 - 220 + b_idx * 75
            by = 240
            d.rounded_rectangle([(bx, by), (bx + 60, by + 70)], radius=10, fill=BG_CARD_INNER, outline=ACCENT_INDIGO, width=2)
            if b_idx < num_visible:
                d.text((bx + 20, by + 18), digits[b_idx], font=get_font(FONT_BOLD, 28), fill="#4ADE80")
                
        # Confirm Button
        d.rounded_rectangle([(WIDTH//2 - 240, 360), (WIDTH//2 + 240, 420)], radius=12, fill="#059669")
        d.text((WIDTH//2 - 120, 378), "Confirm & Save Contact ✓", font=f_btn, fill=TEXT_WHITE)
        
        draw_bottom_guide(d, "STEP 3", "Verify Transactional Email OTP", "No data is written to the database until verified through your personal email OTP.")
        
        draw_cursor(d, WIDTH//2, 390, clicking=(i >= 80))
        writer.append_data(np.array(img))
        
    # 5. Scene: Success State (3.5s = 70 frames)
    for i in range(70):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 300, 120), (WIDTH//2 + 300, 540)], radius=16, fill=BG_CARD, outline="#059669", width=2)
        d.ellipse([(WIDTH//2 - 40, 160), (WIDTH//2 + 40, 240)], fill="#065F46", outline="#10B981", width=3)
        d.text((WIDTH//2 - 15, 178), "✓", font=get_font(FONT_BOLD, 42), fill="#6EE7B7")
        
        d.text((WIDTH//2 - 230, 270), "Contact Details Successfully Saved!", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 250, 315), "Your email and phone have been securely bound to MCS-2668.", font=f_page_s, fill=TEXT_SLATE)
        
        d.rounded_rectangle([(WIDTH//2 - 250, 370), (WIDTH//2 + 250, 450)], radius=12, fill=BG_CARD_INNER, outline=BORDER_COLOR, width=1)
        d.text((WIDTH//2 - 220, 390), "Registered Email: v****@gmail.com  (Verified)", font=get_font(FONT_MONO, 16), fill="#38BDF8")
        d.text((WIDTH//2 - 220, 420), "Registered Phone: *******567  (Verified)", font=get_font(FONT_MONO, 16), fill="#FCD34D")
        
        draw_bottom_guide(d, "SUCCESS", "Profile Fully Prepared for Accreditation", "You are now eligible to complete Step 2: Voter Accreditation.")
        writer.append_data(np.array(img))
        
    # 6. Outro Card (2.5s = 50 frames)
    outro_frame = make_outro_card(
        "Contact Verification Complete!",
        "Every voter must register their unique email to receive accreditation and voting passcodes."
    )
    for _ in range(50):
        writer.append_data(outro_frame)
        
    writer.close()
    print(f"Video 1 generated: {video_path}")
    return video_path


# ==============================================================================
# VIDEO 2: VOTER ACCREDITATION & DEVICE BINDING (/accreditation)
# ==============================================================================
def generate_video_2():
    print("Generating Video 2: Voter Accreditation & Device Binding...")
    video_path = os.path.join(OUTPUT_DIR, "video_2_accreditation.mp4")
    writer = imageio.get_writer(video_path, fps=FPS, codec="libx264", quality=8)
    
    # 1. Intro Card (2.5s = 50 frames)
    title_frame = make_title_card(
        "Voter Accreditation & Device Lock",
        "Pre-election verification and exclusive device binding",
        "TUTORIAL PART 2 / 3"
    )
    for _ in range(50):
        writer.append_data(title_frame)
        
    url = "vmi2848672.contaboserver.net/accreditation"
    
    f_page_h = get_font(FONT_BOLD, 26)
    f_page_s = get_font(FONT_REGULAR, 15)
    f_label = get_font(FONT_BOLD, 15)
    f_input = get_font(FONT_MONO, 18)
    f_btn = get_font(FONT_BOLD, 17)
    f_note = get_font(FONT_REGULAR, 14)
    
    # 2. Scene: Validate MCS (3.5s = 70 frames)
    for i in range(70):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 280, 90), (WIDTH//2 + 280, 560)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        d.text((WIDTH//2 - 240, 120), "Official Voter Accreditation", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 240, 160), "Step 1: Validate 4-digit MCS Number", font=f_page_s, fill=TEXT_SLATE)
        
        d.text((WIDTH//2 - 240, 220), "MCS Number", font=f_label, fill=TEXT_SLATE)
        d.rounded_rectangle([(WIDTH//2 - 240, 250), (WIDTH//2 + 240, 310)], radius=10, fill=BG_CARD_INNER, outline=ACCENT_INDIGO, width=2)
        d.text((WIDTH//2 - 215, 268), "2668", font=f_input, fill="#38BDF8")
        
        d.rounded_rectangle([(WIDTH//2 - 240, 350), (WIDTH//2 + 240, 410)], radius=12, fill="#4338CA")
        d.text((WIDTH//2 - 80, 368), "Validate Voter →", font=f_btn, fill=TEXT_WHITE)
        
        draw_bottom_guide(d, "STEP 1", "Validate Accreditation Eligibility", "Unaccredited voters will not be allowed to enter the voting portal on election day.")
        draw_cursor(d, WIDTH//2 + 40, 380, clicking=(i >= 40))
        writer.append_data(np.array(img))
        
    # 3. Scene: Identity Confirmation & STRICT DEVICE BINDING NOTICE (7s = 140 frames)
    for i in range(140):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 320, 65), (WIDTH//2 + 320, 605)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        d.text((WIDTH//2 - 280, 90), "Confirm Your Identity & Device", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 280, 125), "Please confirm credentials before requesting accreditation OTP", font=f_page_s, fill=TEXT_SLATE)
        
        # Readonly Name
        d.text((WIDTH//2 - 280, 160), "Confirmed Full Name:", font=f_label, fill=TEXT_SLATE)
        d.rounded_rectangle([(WIDTH//2 - 280, 185), (WIDTH//2 + 280, 235)], radius=8, fill=BG_CARD_INNER)
        d.text((WIDTH//2 - 260, 198), "A******* O******* (Verified)", font=f_input, fill="#FFFFFF")
        
        # Readonly Email
        d.text((WIDTH//2 - 280, 250), "Registered Email (OTP Destination):", font=f_label, fill=TEXT_SLATE)
        d.rounded_rectangle([(WIDTH//2 - 280, 275), (WIDTH//2 + 280, 325)], radius=8, fill=BG_CARD_INNER)
        d.text((WIDTH//2 - 260, 288), "v****@gmail.com", font=f_input, fill="#38BDF8")
        
        # PROMINENT DEVICE BINDING NOTICE BOX
        pulse_border = ACCENT_AMBER if (i // 10) % 2 == 0 else "#6366F1"
        d.rounded_rectangle([(WIDTH//2 - 280, 345), (WIDTH//2 + 280, 450)], radius=12, fill="#1E1B4B", outline=pulse_border, width=2)
        d.text((WIDTH//2 - 260, 360), "🔒 STRICT DEVICE BINDING POLICY", font=get_font(FONT_BOLD, 15), fill="#A5B4FC")
        d.text((WIDTH//2 - 260, 388), "By completing accreditation, this device (Chrome on Android)", font=f_note, fill="#FCD34D")
        d.text((WIDTH//2 - 260, 412), "will be permanently locked as your sole voting terminal on election day.", font=f_note, fill="#E2E8F0")
        
        # Submit Button
        d.rounded_rectangle([(WIDTH//2 - 280, 475), (WIDTH//2 + 280, 535)], radius=12, fill="#4338CA")
        d.text((WIDTH//2 - 110, 493), "Submit & Request OTP →", font=f_btn, fill=TEXT_WHITE)
        
        draw_bottom_guide(d, "STEP 2", "Exclusive Device Binding Security", "You MUST perform accreditation on the exact smartphone/browser you intend to vote with.")
        draw_cursor(d, WIDTH//2, 505, clicking=(i >= 110))
        writer.append_data(np.array(img))
        
    # 4. Scene: Enter Accreditation OTP (5s = 100 frames)
    acc_digits = ["5", "1", "8", "3", "0", "4"]
    for i in range(100):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 280, 100), (WIDTH//2 + 280, 560)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        d.text((WIDTH//2 - 240, 140), "Enter Accreditation OTP", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 240, 180), "Enter the 6-digit passcode sent to your registered email", font=f_page_s, fill=TEXT_SLATE)
        
        num_visible = min(i // 15, 6)
        for b_idx in range(6):
            bx = WIDTH//2 - 220 + b_idx * 75
            by = 240
            d.rounded_rectangle([(bx, by), (bx + 60, by + 70)], radius=10, fill=BG_CARD_INNER, outline=ACCENT_INDIGO, width=2)
            if b_idx < num_visible:
                d.text((bx + 20, by + 18), acc_digits[b_idx], font=get_font(FONT_BOLD, 28), fill="#4ADE80")
                
        d.rounded_rectangle([(WIDTH//2 - 240, 360), (WIDTH//2 + 240, 420)], radius=12, fill="#059669")
        d.text((WIDTH//2 - 110, 378), "Confirm Accreditation ✓", font=f_btn, fill=TEXT_WHITE)
        
        draw_bottom_guide(d, "STEP 3", "Submit Authentication OTP", "Confirming the OTP permanently stores your device fingerprint in the election database.")
        draw_cursor(d, WIDTH//2, 390, clicking=(i >= 80))
        writer.append_data(np.array(img))
        
    # 5. Scene: Accreditation Confirmed Screen (Specified Client Message) (6s = 120 frames)
    for i in range(120):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 320, 65), (WIDTH//2 + 320, 605)], radius=16, fill=BG_CARD, outline="#059669", width=2)
        d.ellipse([(WIDTH//2 - 35, 95), (WIDTH//2 + 35, 165)], fill="#065F46", outline="#10B981", width=3)
        d.text((WIDTH//2 - 14, 110), "✓", font=get_font(FONT_BOLD, 38), fill="#6EE7B7")
        
        d.text((WIDTH//2 - 180, 185), "Accreditation Confirmed!", font=f_page_h, fill=TEXT_WHITE)
        
        # EXACT SPECIFIED MESSAGE BANNER
        d.rounded_rectangle([(WIDTH//2 - 290, 235), (WIDTH//2 + 290, 315)], radius=12, fill="#064E3B", outline="#059669", width=2)
        d.text((WIDTH//2 - 275, 252), "you have been successfully accredited for the NECO MCS election,", font=get_font(FONT_BOLD, 15), fill="#A7F3D0")
        d.text((WIDTH//2 - 275, 280), "wait for further instruction for voting.", font=get_font(FONT_BOLD, 15), fill="#FCD34D")
        
        # Credentials and Device Lock Card
        d.rounded_rectangle([(WIDTH//2 - 290, 335), (WIDTH//2 + 290, 520)], radius=12, fill=BG_CARD_INNER, outline=BORDER_COLOR, width=1)
        d.text((WIDTH//2 - 270, 355), "MCS Username: 2668", font=f_input, fill="#FFFFFF")
        d.text((WIDTH//2 - 270, 395), "Full Name: A******* O*******", font=f_input, fill="#CBD5E1")
        d.text((WIDTH//2 - 270, 435), "Accreditation Status: OFFICIALLY ACCREDITED", font=get_font(FONT_BOLD, 15), fill="#4ADE80")
        
        # Bound Device Highlight
        d.rounded_rectangle([(WIDTH//2 - 275, 465), (WIDTH//2 + 275, 505)], radius=6, fill="#1E1B4B")
        d.text((WIDTH//2 - 265, 475), "Bound Voting Device: Chrome on Android [DEVICE LOCKED]", font=get_font(FONT_BOLD, 14), fill="#38BDF8")
        
        draw_bottom_guide(d, "COMPLETE", "Device Locked for Election Day", "Your phone is now your cryptographic voting terminal. Do not clear your browser cache.")
        writer.append_data(np.array(img))
        
    # 6. Outro Card (2.5s = 50 frames)
    outro_frame = make_outro_card(
        "Accreditation Successful!",
        "Only the phone used for accreditation can access the voting booth on election day."
    )
    for _ in range(50):
        writer.append_data(outro_frame)
        
    writer.close()
    print(f"Video 2 generated: {video_path}")
    return video_path


# ==============================================================================
# VIDEO 3: ELECTION DAY VOTING & ANTI-PROXY PROTECTION (/election)
# ==============================================================================
def generate_video_3():
    print("Generating Video 3: Election Day Voting & Security Enforcement...")
    video_path = os.path.join(OUTPUT_DIR, "video_3_election_voting.mp4")
    writer = imageio.get_writer(video_path, fps=FPS, codec="libx264", quality=8)
    
    # 1. Intro Card (2.5s = 50 frames)
    title_frame = make_title_card(
        "Election Day Voting Process",
        "Hardware verification, candidate voting & cryptographic receipts",
        "TUTORIAL PART 3 / 3"
    )
    for _ in range(50):
        writer.append_data(title_frame)
        
    url = "vmi2848672.contaboserver.net/election"
    
    f_page_h = get_font(FONT_BOLD, 26)
    f_page_s = get_font(FONT_REGULAR, 15)
    f_label = get_font(FONT_BOLD, 15)
    f_input = get_font(FONT_MONO, 18)
    f_btn = get_font(FONT_BOLD, 17)
    f_note = get_font(FONT_REGULAR, 14)
    
    # 2. Scene: Election Day Login (3.5s = 70 frames)
    for i in range(70):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 280, 80), (WIDTH//2 + 280, 560)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        
        # Active Status Pill
        d.rounded_rectangle([(WIDTH//2 - 80, 110), (WIDTH//2 + 80, 145)], radius=18, fill="#065F46")
        d.text((WIDTH//2 - 60, 120), "● VOTING ACTIVE", font=get_font(FONT_BOLD, 13), fill="#6EE7B7")
        
        d.text((WIDTH//2 - 240, 175), "Cast Your Ballot", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 240, 215), "Enter your MCS number on your accredited device", font=f_page_s, fill=TEXT_SLATE)
        
        d.text((WIDTH//2 - 240, 275), "MCS Username", font=f_label, fill=TEXT_SLATE)
        d.rounded_rectangle([(WIDTH//2 - 240, 305), (WIDTH//2 + 240, 365)], radius=10, fill=BG_CARD_INNER, outline=ACCENT_INDIGO, width=2)
        d.text((WIDTH//2 - 215, 323), "2668", font=f_input, fill="#38BDF8")
        
        d.rounded_rectangle([(WIDTH//2 - 240, 405), (WIDTH//2 + 240, 465)], radius=12, fill="#4338CA")
        d.text((WIDTH//2 - 130, 423), "Validate & Send Voting OTP →", font=f_btn, fill=TEXT_WHITE)
        
        draw_bottom_guide(d, "STEP 1", "Election Day Identity & Device Verification", "The election server verifies your accredited device ID before dispatching a voting OTP.")
        draw_cursor(d, WIDTH//2, 435, clicking=(i >= 45))
        writer.append_data(np.array(img))
        
    # 3. Scene: ANTI-PROXY DEMONSTRATION (Device Mismatch Lock) (5.5s = 110 frames)
    for i in range(110):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, url)
        
        d.rounded_rectangle([(WIDTH//2 - 340, 75), (WIDTH//2 + 340, 580)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        
        if i < 55:
            # Show Device Mismatch Block when tried on unauthorized device
            d.rounded_rectangle([(WIDTH//2 - 310, 110), (WIDTH//2 + 310, 260)], radius=12, fill="#451A03", outline=ACCENT_AMBER, width=2)
            d.rounded_rectangle([(WIDTH//2 - 290, 130), (WIDTH//2 - 90, 165)], radius=6, fill="#B45309")
            d.text((WIDTH//2 - 280, 140), "DEVICE SECURITY LOCK", font=get_font(FONT_BOLD, 13), fill="#FFFFFF")
            d.text((WIDTH//2 - 290, 180), "HTTP 403 Forbidden: Device Mismatch Detected", font=get_font(FONT_BOLD, 17), fill="#FDE68A")
            d.text((WIDTH//2 - 290, 210), "Accredited Device: Chrome on Android", font=f_note, fill="#FEF3C7")
            d.text((WIDTH//2 - 290, 230), "Current Device: Windows Laptop (Edge) - ACCESS DENIED", font=f_note, fill="#FCA5A5")
            
            d.text((WIDTH//2 - 290, 300), "Why is this blocked?", font=get_font(FONT_BOLD, 18), fill="#38BDF8")
            d.text((WIDTH//2 - 290, 335), "• Prevents proxy voting: No one can vote for you using your credentials.", font=f_note, fill="#E2E8F0")
            d.text((WIDTH//2 - 290, 365), "• Stops centralized ballot harvesting on shared cyber cafe computers.", font=f_note, fill="#E2E8F0")
            d.text((WIDTH//2 - 290, 395), "• Lost/Damaged phone? The Admin can reverse your accreditation to re-bind.", font=f_note, fill="#A7F3D0")
            
            draw_bottom_guide(d, "SECURITY", "Zero-Trust Device Binding in Action", "Voting attempts from unauthorized devices are blocked instantly by the security layer.")
        else:
            # Switch to authorized device
            d.rounded_rectangle([(WIDTH//2 - 310, 110), (WIDTH//2 + 310, 230)], radius=12, fill="#064E3B", outline="#10B981", width=2)
            d.text((WIDTH//2 - 290, 135), "✓ Accredited Device Authorized: Chrome on Android", font=get_font(FONT_BOLD, 18), fill="#A7F3D0")
            d.text((WIDTH//2 - 290, 175), "Hardware match confirmed. Ephemeral voting OTP dispatched to voter.neco@gmail.com", font=f_note, fill="#FFFFFF")
            
            # OTP entry prompt
            d.text((WIDTH//2 - 290, 270), "Enter 6-Digit Voting Passcode", font=f_page_h, fill=TEXT_WHITE)
            v_digits = ["3", "8", "0", "4", "6", "2"]
            for b_idx in range(6):
                bx = WIDTH//2 - 220 + b_idx * 75
                by = 330
                d.rounded_rectangle([(bx, by), (bx + 60, by + 70)], radius=10, fill=BG_CARD_INNER, outline=ACCENT_INDIGO, width=2)
                d.text((bx + 20, by + 18), v_digits[b_idx], font=get_font(FONT_BOLD, 28), fill="#4ADE80")
                
            d.rounded_rectangle([(WIDTH//2 - 240, 440), (WIDTH//2 + 240, 500)], radius=12, fill="#059669")
            d.text((WIDTH//2 - 110, 458), "Verify & Enter Booth →", font=f_btn, fill=TEXT_WHITE)
            
            draw_bottom_guide(d, "STEP 2", "Authorized Device Passcode Verification", "Once your device matches, enter your one-time voting passcode to enter the voting booth.")
            draw_cursor(d, WIDTH//2, 470, clicking=(i >= 90))
            
        writer.append_data(np.array(img))
        
    # 4. Scene: Digital Voting Booth & Candidate Selection (7s = 140 frames)
    for i in range(140):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, "vmi2848672.contaboserver.net/voter/dashboard")
        
        d.rounded_rectangle([(WIDTH//2 - 400, 65), (WIDTH//2 + 400, 605)], radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=2)
        d.text((WIDTH//2 - 360, 90), "Executive Office: President", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 360, 125), "Please select one candidate to cast your secret ballot", font=f_page_s, fill=TEXT_SLATE)
        
        # Candidate 1 Card (Selected)
        c1_border = "#22C55E" if i >= 30 else BORDER_COLOR
        c1_fill = "#064E3B" if i >= 30 else BG_CARD_INNER
        d.rounded_rectangle([(WIDTH//2 - 360, 165), (WIDTH//2 - 20, 390)], radius=12, fill=c1_fill, outline=c1_border, width=2)
        d.ellipse([(WIDTH//2 - 230, 190), (WIDTH//2 - 150, 270)], fill="#334155")
        d.text((WIDTH//2 - 205, 215), "👤", font=get_font(FONT_BOLD, 30), fill=TEXT_WHITE)
        d.text((WIDTH//2 - 270, 290), "Candidate A (MCS-1024)", font=get_font(FONT_BOLD, 17), fill=TEXT_WHITE)
        d.text((WIDTH//2 - 240, 320), "Manifesto: Accountability", font=f_note, fill=TEXT_SLATE)
        if i >= 30:
            d.rounded_rectangle([(WIDTH//2 - 250, 350), (WIDTH//2 - 130, 380)], radius=6, fill="#059669")
            d.text((WIDTH//2 - 230, 358), "✓ SELECTED", font=get_font(FONT_BOLD, 13), fill=TEXT_WHITE)
            
        # Candidate 2 Card
        d.rounded_rectangle([(WIDTH//2 + 20, 165), (WIDTH//2 + 360, 390)], radius=12, fill=BG_CARD_INNER, outline=BORDER_COLOR, width=2)
        d.ellipse([(WIDTH//2 + 150, 190), (WIDTH//2 + 230, 270)], fill="#334155")
        d.text((WIDTH//2 + 175, 215), "👤", font=get_font(FONT_BOLD, 30), fill=TEXT_WHITE)
        d.text((WIDTH//2 + 110, 290), "Candidate B (MCS-1890)", font=get_font(FONT_BOLD, 17), fill=TEXT_WHITE)
        d.text((WIDTH//2 + 140, 320), "Manifesto: Growth & Loans", font=f_note, fill=TEXT_SLATE)
        
        # Submit Ballot Button
        btn_bg = "#4338CA" if i >= 50 else "#334155"
        d.rounded_rectangle([(WIDTH//2 - 200, 430), (WIDTH//2 + 200, 490)], radius=12, fill=btn_bg)
        d.text((WIDTH//2 - 80, 448), "Cast Secret Ballot 🗳️", font=f_btn, fill=TEXT_WHITE)
        
        # Privacy badge
        d.text((WIDTH//2 - 180, 520), "End-to-End Cryptographic Secret Ballot Protection", font=get_font(FONT_REGULAR, 14), fill="#64748B")
        
        draw_bottom_guide(d, "STEP 3", "Select Candidate & Cast Your Ballot", "Your vote is cryptographically anonymized and recorded in the immutable ballot registry.")
        draw_cursor(d, WIDTH//2 - 190, 280 if i < 50 else 460, clicking=(i >= 30 and i <= 40 or i >= 110))
        writer.append_data(np.array(img))
        
    # 5. Scene: Vote Success & Cryptographic Receipt (5s = 100 frames)
    for i in range(100):
        img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_DARK)
        d = ImageDraw.Draw(img)
        draw_browser_chrome(d, "vmi2848672.contaboserver.net/voter/dashboard")
        
        d.rounded_rectangle([(WIDTH//2 - 320, 80), (WIDTH//2 + 320, 560)], radius=16, fill=BG_CARD, outline="#059669", width=2)
        d.ellipse([(WIDTH//2 - 35, 110), (WIDTH//2 + 35, 180)], fill="#065F46", outline="#10B981", width=3)
        d.text((WIDTH//2 - 14, 125), "✓", font=get_font(FONT_BOLD, 38), fill="#6EE7B7")
        
        d.text((WIDTH//2 - 170, 205), "Vote Cast Successfully!", font=f_page_h, fill=TEXT_WHITE)
        d.text((WIDTH//2 - 220, 245), "Your ballot has been officially recorded in the election register.", font=f_page_s, fill=TEXT_SLATE)
        
        # Cryptographic Receipt Box
        d.rounded_rectangle([(WIDTH//2 - 280, 290), (WIDTH//2 + 280, 450)], radius=12, fill=BG_CARD_INNER, outline=BORDER_COLOR, width=1)
        d.text((WIDTH//2 - 250, 310), "OFFICIAL VOTING RECEIPT", font=get_font(FONT_BOLD, 15), fill="#38BDF8")
        d.text((WIDTH//2 - 250, 345), "Voter: A******* O******* (MCS-2668)", font=f_note, fill="#E2E8F0")
        d.text((WIDTH//2 - 250, 375), "Office: President", font=f_note, fill="#E2E8F0")
        d.text((WIDTH//2 - 250, 405), "SHA-256 Receipt: 9f8a4e...3b21c7", font=get_font(FONT_MONO, 14), fill="#FCD34D")
        
        d.rounded_rectangle([(WIDTH//2 - 140, 480), (WIDTH//2 + 140, 530)], radius=10, fill="#1E1B4B", outline="#4338CA", width=1)
        d.text((WIDTH//2 - 110, 495), "Download Voting Receipt", font=get_font(FONT_BOLD, 14), fill="#A5B4FC")
        
        draw_bottom_guide(d, "COMPLETE", "Ballot Receipt Generated", "Keep your receipt hash to independently verify your participation in the election.")
        writer.append_data(np.array(img))
        
    # 6. Outro Card (2.5s = 50 frames)
    outro_frame = make_outro_card(
        "Election Day Voting Complete!",
        "Every vote is cast once, bound to the accredited device, and cryptographically verified."
    )
    for _ in range(50):
        writer.append_data(outro_frame)
        
    writer.close()
    print(f"Video 3 generated: {video_path}")
    return video_path

if __name__ == "__main__":
    generate_video_1()
    generate_video_2()
    generate_video_3()
    print("All 3 sensitization videos created successfully!")
