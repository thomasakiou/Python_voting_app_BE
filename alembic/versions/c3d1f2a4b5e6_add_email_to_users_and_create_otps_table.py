"""add email to users and create otps table

Revision ID: c3d1f2a4b5e6
Revises: 7e0010723302
Create Date: 2026-11-05 13:14:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d1f2a4b5e6"
down_revision: Union[str, Sequence[str], None] = "7e0010723302"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Add nullable email column to users
    op.add_column(
        "users",
        sa.Column("email", sa.String(), nullable=True),
    )
    op.create_unique_constraint("users_email_key", "users", ["email"])

    # ── 2. Create the otps table
    op.create_table(
        "otps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("otp_code", sa.String(length=6), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "expires_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="otps_user_id_fkey", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="otps_pkey"),
    )


def downgrade() -> None:
    # Drop otps table
    op.drop_table("otps")

    # Remove email column from users
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.drop_column("users", "email")
