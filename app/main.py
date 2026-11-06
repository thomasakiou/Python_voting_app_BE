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
)
from .api.auth import otp_login, admin_login, logout
from .domain import user as models
from .domain import otp as otp_models
from .domain import voting_time as vt_models
from .domain import audit_log as audit_models
from .core.database import engine
from .core import database
from .core.init_super_admin import init_super_admin
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware


def auto_upgrade_schema():
    """
    Ensures newly added columns and tables exist on PostgreSQL without requiring manual migrations.
    Uses IF NOT EXISTS so it is completely safe and idempotent.
    """
    try:
        with engine.begin() as conn:
            statements = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_accredited BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS accredited_at TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS is_disqualified BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE offices ADD COLUMN IF NOT EXISTS is_disqualified BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE votes ADD COLUMN IF NOT EXISTS receipt_hash VARCHAR(64);",
                "ALTER TABLE voting_times ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE voting_times ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'NOT_STARTED';",
                "ALTER TABLE otps ADD COLUMN IF NOT EXISTS purpose VARCHAR(32) DEFAULT 'login';",
                "ALTER TABLE otps ADD COLUMN IF NOT EXISTS temp_email VARCHAR(255);",
                "ALTER TABLE otps ADD COLUMN IF NOT EXISTS temp_phone VARCHAR(32);",
            ]
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass
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
