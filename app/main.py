from fastapi import FastAPI
from .api import (
    user_routes as users,
    candidate_routes as candidates,
    office_routes as offices,
    vote_routes as votes,
    result_routes as results,
    config_route as config,
    voting_time_routes as voting_time,
    accreditation_routes as accreditation,
    audit_log_routes as audit_logs,
    voter_contact_routes as voter_contact,
    portal_lock_routes as portal_locks,
)
from .api.auth import otp_login, admin_login, logout
from .domain import user as models
from .domain import otp as otp_models
from .domain import voting_time as vt_models
from .domain import audit_log as audit_models
from .domain import dispute as dispute_models
from .core.database import engine
from .core import database
from .core.init_super_admin import init_super_admin
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware


def auto_upgrade_schema():
    """
    Ensures newly added columns and tables exist on PostgreSQL without requiring manual migrations.
    Uses AUTOCOMMIT so each ALTER TABLE is immediately committed and errors in one don't abort others.
    """
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_accredited BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accredited_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accredited_device_id VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS device_info VARCHAR(255);",
        "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS is_disqualified BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE offices ADD COLUMN IF NOT EXISTS is_disqualified BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE votes ADD COLUMN IF NOT EXISTS receipt_hash VARCHAR(64);",
        "ALTER TABLE voting_times ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE voting_times ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'NOT_STARTED';",
        "ALTER TABLE voting_times ALTER COLUMN start_time DROP NOT NULL;",
        "ALTER TABLE voting_times ALTER COLUMN end_time DROP NOT NULL;",
        "ALTER TABLE otps ADD COLUMN IF NOT EXISTS purpose VARCHAR(32) DEFAULT 'login';",
        "ALTER TABLE otps ADD COLUMN IF NOT EXISTS temp_email VARCHAR(255);",
        "ALTER TABLE otps ADD COLUMN IF NOT EXISTS temp_phone VARCHAR(32);",
        """CREATE TABLE IF NOT EXISTS voter_disputes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            username VARCHAR(50) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            current_email VARCHAR(255),
            current_phone VARCHAR(50),
            requested_email VARCHAR(255),
            requested_phone VARCHAR(50),
            dispute_type VARCHAR(50) DEFAULT 'CONTACT_UPDATE' NOT NULL,
            reason TEXT NOT NULL,
            status VARCHAR(32) DEFAULT 'PENDING' NOT NULL,
            admin_notes TEXT,
            resolved_by VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            resolved_at TIMESTAMP WITH TIME ZONE
        );""",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
        "CREATE INDEX IF NOT EXISTS idx_users_is_accredited ON users(is_accredited);",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_votes_user_id ON votes(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_votes_office_code ON votes(office_code);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_session_id VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMP WITH TIME ZONE;",
        "UPDATE users SET email = NULL WHERE role IN ('admin', 'super-admin') AND email IS NOT NULL;",
        """CREATE TABLE IF NOT EXISTS portal_locks (
            id INTEGER PRIMARY KEY DEFAULT 1,
            is_contact_update_locked BOOLEAN NOT NULL DEFAULT FALSE,
            is_accreditation_locked BOOLEAN NOT NULL DEFAULT FALSE,
            is_election_locked BOOLEAN NOT NULL DEFAULT FALSE,
            contact_update_message VARCHAR(500) DEFAULT 'The Voter Contact Update portal is currently closed by the election administrator.',
            accreditation_message VARCHAR(500) DEFAULT 'Voter Accreditation is currently closed by the election administrator.',
            election_message VARCHAR(500) DEFAULT 'The Election portal is currently closed by the election administrator.',
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );""",
        "INSERT INTO portal_locks (id, is_contact_update_locked, is_accreditation_locked, is_election_locked) VALUES (1, FALSE, FALSE, FALSE) ON CONFLICT (id) DO NOTHING;",
    ]
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception as inner_e:
                    print(f"[Schema Upgrade Notice]: {stmt} -> {inner_e}")
    except Exception as e:
        print(f"[Schema Upgrade Notice] {e}")


models.Base.metadata.create_all(bind=engine)
auto_upgrade_schema()

app = FastAPI(
    title="NECO MCS Voting API",
    description="High-Performance Electronic Accreditation & Voting System API for NECO MCS Election",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/api",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://votingappfe.netlify.app",
    "https://onlinevoter.netlify.app",
    "https://vmi2848672.contaboserver.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Welcome to NECO MCS Voting API",
        "version": "2.0.0",
        "docs_url": "/api/docs",
        "openapi_url": "/api/openapi.json",
        "status": "running",
    }


@app.get("/app")
def app_status():
    return {"message": "API is running"}


@app.on_event("startup")
def create_super_admin():
    db = database.SessionLocal()
    init_super_admin(db)
    db.close()


# Core Routers
app.include_router(accreditation.router) # POST /accreditation/validate, /send-otp, /verify-otp
app.include_router(otp_login.router)     # POST /login, POST /election/login, POST /verify-otp
app.include_router(admin_login.router)   # POST /admin/login
app.include_router(logout.router)
app.include_router(users.router)
app.include_router(candidates.router)
app.include_router(offices.router)
app.include_router(votes.router)
app.include_router(results.router)
app.include_router(config.router)
app.include_router(voting_time.router)
app.include_router(audit_logs.router)
app.include_router(voter_contact.router)
app.include_router(portal_locks.router)
