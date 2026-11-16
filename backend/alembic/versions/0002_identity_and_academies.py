"""Add academy and user identity tables.

Revision ID: 0002_identity
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_identity"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "academies",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False, unique=True),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED')", name="ck_academies_status"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("academy_id", sa.Uuid(), sa.ForeignKey("academies.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('SUPER_ADMIN', 'ACADEMY_ADMIN', 'TEACHER', 'STUDENT')", name="ck_users_role"),
        sa.CheckConstraint("(role = 'SUPER_ADMIN' AND academy_id IS NULL) OR (role != 'SUPER_ADMIN' AND academy_id IS NOT NULL)", name="ck_user_academy_scope"),
    )
    op.create_index("ix_users_academy_id", "users", ["academy_id"])
    op.create_index("ix_users_role", "users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_academy_id", table_name="users")
    op.drop_table("users")
    op.drop_table("academies")
