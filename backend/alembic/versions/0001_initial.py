"""Enable PostgreSQL trigram search support.

Revision ID: 0001_initial
Revises:
"""
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    # Extensions can be shared by other databases objects; keep it installed.
    pass
