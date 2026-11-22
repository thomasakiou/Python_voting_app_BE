import asyncio
import os
import edge_tts

VOICE = "en-NG-AbeoNeural"
OUTPUT_DIR = r"G:\Projects\voting-app\voting-explainer\public\audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCRIPTS = {
    "scene0_intro": (
        "Welcome to the official NECO MCS Electronic Voting Guide. "
        "Participating in the election is fast, secure, and straightforward. "
        "Every voter must complete three essential steps: "
        "Number one: Contact Update. "
        "Number two: Voter Accreditation. "
        "And number three: Voting on Election Day."
    ),
    "scene1_contact_lookup": (
        "Step one: Contact Update and Verification. "
        "Visit the Contact Update Portal and enter your four-digit MCS number. "
        "The system immediately retrieves your voter profile and confirms your full name."
    ),
    "scene1_contact_otp": (
        "If your email or phone number is missing, type them in and click submit. "
        "A six-digit One-Time-Password will be dispatched to your email. "
        "Enter the OTP code into the six boxes to verify and lock your contact details securely into the database."
    ),
    "scene1_dispute": (
        "Now, what if your email is already registered, but it is incorrect or inaccessible? "
        "Do not worry! You can easily raise a dispute. "
        "Simply click 'Raise Dispute', select your dispute reason, provide your correct details and explanation, "
        "and the election administrator will review and resolve it promptly."
    ),
    "scene2_accreditation": (
        "Step two: Voter Accreditation. "
        "Before election day, visit the Accreditation Portal and enter your MCS number. "
        "Confirm your identity and registered contact details, then click 'Submit and Request OTP'."
    ),
    "scene2_device_binding": (
        "Enter the six-digit accreditation OTP received on your phone or email. "
        "Very important: Accreditation securely binds your voter account to this exact device and browser. "
        "On election day, you must vote from this same device. "
        "Once verified, you will receive your official confirmation: You have been successfully accredited for the NECO MCS election!"
    ),
    "scene3_election_login": (
        "Step three: Election Day Voting. "
        "When the polls open, head over to the Election Portal. "
        "Enter your MCS number and click validate to receive your one-time voting passcode via email. "
        "Enter your six-digit OTP to unlock your secure ballot."
    ),
    "scene3_ballot_inspect": (
        "On your voter dashboard, click 'Proceed to Ballot'. "
        "Here you will see all contested offices, such as President and General Secretary. "
        "Select an office to view the candidates. "
        "You can click on any candidate's photo to enlarge and inspect their full profile before making your choice."
    ),
    "scene3_cast_receipt": (
        "Select your preferred candidate and click 'Cast Vote'. "
        "Your vote is instantly encrypted, permanently counted, and locked. "
        "You immediately receive an official SHA-256 cryptographic receipt confirming your ballot has been counted. "
        "Repeat this for all offices until your ballot is complete!"
    ),
    "scene4_outro": (
        "And that is it! Three simple steps: Update your contact, accredit your device, and cast your ballot. "
        "NECO MCS Voting System: Authenticated, Transparent, and Cryptographically Secure. "
        "Make your vote count!"
    )
}

async def generate():
    for name, text in SCRIPTS.items():
        out_path = os.path.join(OUTPUT_DIR, f"{name}.mp3")
        print(f"Generating {name}...")
        communicate = edge_tts.Communicate(text, VOICE, rate="+3%", pitch="+0Hz")
        await communicate.save(out_path)
        print(f"Saved {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    asyncio.run(generate())
