import psycopg2
from fastapi.testclient import TestClient
from app.main import app
from app.core import database
from app.domain.user import User
from app.domain.otp import OTP
from app.domain.voting_time import VotingTime
from app.domain.office import Office
from app.domain.candidate import Candidate
from app.domain.vote import Vote
from app.core import utils

client = TestClient(app)

db = database.SessionLocal()

# Setup test offices and candidates
off1 = db.query(Office).filter(Office.office_code == "PRES").first()
if not off1:
    off1 = Office(office_code="PRES", description="President")
    db.add(off1)
    db.commit()

cand1 = db.query(Candidate).filter(Candidate.candidate_code == "C001").first()
if not cand1:
    cand1 = Candidate(candidate_code="C001", name="Candidate Alpha", office_code="PRES")
    db.add(cand1)
    db.commit()

# Ensure a test voter with 4-digit MCS number exists with phone=None, email=None
test_voter = db.query(User).filter(User.username == "2668").first()
if not test_voter:
    test_voter = User(
        username="2668",
        full_name="Muhammad Sani",
        password=utils.hash_password("Vote@123"),
        phone=None,
        email=None,
        role="voter",
        is_active=True,
        is_accredited=False
    )
    db.add(test_voter)
    db.commit()
    db.refresh(test_voter)
else:
    test_voter.is_active = True
    test_voter.is_accredited = False
    test_voter.phone = None
    test_voter.email = None
    db.commit()

print("--- 1. Testing Accreditation Step 1: Validate Voter MCS 2668 ---")
res = client.post("/accreditation/validate", json={"username": "2668"})
print("Status:", res.status_code, "Body:", res.json())
assert res.status_code == 200
assert res.json()["full_name"] == "Muhammad Sani"
assert res.json()["is_accredited"] is False

print("\n--- 2. Testing Accreditation Step 2: Send OTP with phone and email ---")
res = client.post("/accreditation/send-otp", json={
    "username": "2668",
    "phone": "08012345678",
    "email": "voter2668@example.com"
})
print("Status:", res.status_code, "Body:", res.json())
assert res.status_code == 200

# Get the generated OTP from DB
otp_entry = db.query(OTP).filter(OTP.user_id == test_voter.id, OTP.purpose == "accreditation", OTP.is_used == False).order_by(OTP.created_at.desc()).first()
print("Found OTP code:", otp_entry.otp_code)

print("\n--- 3. Testing Accreditation Step 3: Verify OTP ---")
res = client.post("/accreditation/verify-otp", json={
    "username": "2668",
    "otp_code": otp_entry.otp_code,
    "phone": "08012345678",
    "email": "voter2668@example.com"
})
print("Status:", res.status_code, "Body:", res.json())
assert res.status_code == 200
assert res.json()["accredited"] is True

db.refresh(test_voter)
print("Updated voter state:", test_voter.email, test_voter.phone, "is_accredited:", test_voter.is_accredited)
assert test_voter.email == "voter2668@example.com"
assert test_voter.phone == "08012345678"
assert test_voter.is_accredited is True

print("\n--- 4. Testing Admin Start Voting ---")
# Admin login to get admin token
admin_res = client.post("/admin/login", json={"username": "admin", "password": "123456"})
assert admin_res.status_code == 200
admin_token = admin_res.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

res = client.post("/voting-time/start", headers=admin_headers)
print("Start voting status:", res.status_code, res.json())
assert res.status_code == 200
assert res.json()["is_active"] is True
assert res.json()["status"] == "ACTIVE"

print("\n--- 5. Testing Election Day Login for Accredited Voter ---")
res = client.post("/election/login", json={"username": "2668"})
print("Election login status:", res.status_code, res.json())
assert res.status_code == 200
assert res.json()["otp_sent"] is True

# Get voting OTP
voting_otp = db.query(OTP).filter(OTP.user_id == test_voter.id, OTP.purpose == "voting", OTP.is_used == False).order_by(OTP.created_at.desc()).first()
print("Found voting OTP code:", voting_otp.otp_code)

res = client.post("/verify-otp", json={"username": "2668", "otp_code": voting_otp.otp_code})
print("Verify voting OTP:", res.status_code, res.json())
assert res.status_code == 200
voter_token = res.json()["access_token"]
voter_headers = {"Authorization": f"Bearer {voter_token}"}

print("\n--- 6. Testing Casting Vote ---")
# Clean any previous vote for this test voter in PRES
db.query(Vote).filter(Vote.user_id == test_voter.id, Vote.office_code == "PRES").delete()
db.commit()

res = client.post("/votes/", json={"candidate_code": "C001", "office_code": "PRES"}, headers=voter_headers)
print("Vote cast response:", res.status_code, res.json())
assert res.status_code == 200
assert "receipt_hash" in res.json()
print("Receipt:", res.json()["receipt_hash"])

print("\n--- 7. Testing Duplicate Vote Prevention ---")
res = client.post("/votes/", json={"candidate_code": "C001", "office_code": "PRES"}, headers=voter_headers)
print("Duplicate vote status:", res.status_code, res.json())
assert res.status_code == 400

print("\n--- 8. Testing Voter's Own Votes & Stats ---")
res = client.get("/votes/my-votes", headers=voter_headers)
print("My votes:", res.status_code, res.json())
assert res.status_code == 200
assert len(res.json()) >= 1

res = client.get("/votes/my-stats", headers=voter_headers)
print("My stats:", res.status_code, res.json())
assert res.status_code == 200

print("\n--- 9. Testing Disabling Voter (is_active = False) ---")
res = client.patch(f"/users/{test_voter.id}/status?is_active=false", headers=admin_headers)
print("Disabled voter:", res.status_code, res.json()["is_active"])
assert res.json()["is_active"] is False

# Test that disabled voter cannot log in or accredit
res = client.post("/election/login", json={"username": "2668"})
print("Election login when disabled:", res.status_code, res.json())
assert res.status_code == 403

# Re-enable voter
client.patch(f"/users/{test_voter.id}/status?is_active=true", headers=admin_headers)

print("\n--- 10. Testing Admin Stop Voting ---")
res = client.post("/voting-time/stop", headers=admin_headers)
print("Stop voting status:", res.status_code, res.json())
assert res.status_code == 200
assert res.json()["is_active"] is False

# Test that voter cannot vote when voting stopped
res = client.post("/votes/", json={"candidate_code": "C001", "office_code": "PRES"}, headers=voter_headers)
print("Vote when stopped status:", res.status_code, res.json())
assert res.status_code == 400

print("\n--- 11. Testing Voters Analysis Endpoint ---")
res = client.get("/users/stats/analysis", headers=admin_headers)
print("Analysis:", res.status_code, res.json())
assert res.status_code == 200
assert "total_voters" in res.json()
assert "accredited_voters" in res.json()
assert "eligible_voters" in res.json()
assert "non_eligible_voters" in res.json()

print("\n--- 12. Testing CSV and PDF Exports ---")
res = client.get("/users/export/csv", headers=admin_headers)
assert res.status_code == 200
assert "text/csv" in res.headers["content-type"]
print("CSV Export length:", len(res.content))

res = client.get("/users/export/pdf", headers=admin_headers)
assert res.status_code == 200
assert "application/pdf" in res.headers["content-type"]
print("PDF Export length:", len(res.content))

res = client.get("/results/export/PRES", headers=admin_headers)
assert res.status_code == 200
assert "text/csv" in res.headers["content-type"]
print("Office results CSV length:", len(res.content))

print("\n--- 13. Testing Audit Logs ---")
res = client.get("/audit-logs/", headers=admin_headers)
assert res.status_code == 200
print("Audit logs count:", len(res.json()))

res = client.get("/audit-logs/export/csv", headers=admin_headers)
assert res.status_code == 200
print("Audit logs CSV length:", len(res.content))

print("\n>>> ALL BACKEND TESTS PASSED SUCCESSFULLY! <<<")
db.close()
