"""add accreditation and election fields

Revision ID: d4e5f6a7b8c9
Revises: c3d1f2a4b5e6
Create Date: 2026-11-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d1f2a4b5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Users table additions
    conn = op.get_bind()
    # Safe PostgreSQL column additions
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR;"))
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_accredited BOOLEAN DEFAULT FALSE;"))
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS accredited_at TIMESTAMP WITH TIME ZONE;"))

    # ── 2. Candidates & Offices
    conn.execute(sa.text("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS is_disqualified BOOLEAN DEFAULT FALSE;"))
    conn.execute(sa.text("ALTER TABLE offices ADD COLUMN IF NOT EXISTS is_disqualified BOOLEAN DEFAULT FALSE;"))

    # ── 3. Votes
    conn.execute(sa.text("ALTER TABLE votes ADD COLUMN IF NOT EXISTS receipt_hash VARCHAR(64);"))

    # ── 4. Voting Times
    conn.execute(sa.text("ALTER TABLE voting_times ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE;"))
    conn.execute(sa.text("ALTER TABLE voting_times ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'NOT_STARTED';"))

    # ── 5. OTPs
    conn.execute(sa.text("ALTER TABLE otps ADD COLUMN IF NOT EXISTS purpose VARCHAR(32) DEFAULT 'login';"))
    conn.execute(sa.text("ALTER TABLE otps ADD COLUMN IF NOT EXISTS temp_email VARCHAR(255);"))
    conn.execute(sa.text("ALTER TABLE otps ADD COLUMN IF NOT EXISTS temp_phone VARCHAR(32);"))

    # ── 6. Audit Logs Table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            admin_username VARCHAR(100) NOT NULL,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            target_id VARCHAR(100),
            details TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS is_accredited;"))
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS accredited_at;"))
    conn.execute(sa.text("ALTER TABLE candidates DROP COLUMN IF EXISTS is_disqualified;"))
    conn.execute(sa.text("ALTER TABLE offices DROP COLUMN IF EXISTS is_disqualified;"))
    conn.execute(sa.text("ALTER TABLE votes DROP COLUMN IF EXISTS receipt_hash;"))
    conn.execute(sa.text("ALTER TABLE voting_times DROP COLUMN IF EXISTS is_active;"))
    conn.execute(sa.text("ALTER TABLE voting_times DROP COLUMN IF EXISTS status;"))
    conn.execute(sa.text("ALTER TABLE otps DROP COLUMN IF EXISTS purpose;"))
    conn.execute(sa.text("ALTER TABLE otps DROP COLUMN IF EXISTS temp_email;"))
    conn.execute(sa.text("ALTER TABLE otps DROP COLUMN IF EXISTS temp_phone;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS audit_logs;"))
