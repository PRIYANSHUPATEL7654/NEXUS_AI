"""add nexus intelligence run audit

Revision ID: 20260911_11
Revises: 20260910_10
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260911_11"
down_revision: str | None = "20260910_10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "intelligence_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("tool_name", sa.String(80), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("result_summary", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('completed', 'failed')", name="ck_intelligence_runs_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_intelligence_runs_user_id"), "intelligence_runs", ["user_id"], unique=False)
    op.create_index(op.f("ix_intelligence_runs_operation"), "intelligence_runs", ["operation"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_intelligence_runs_operation"), table_name="intelligence_runs")
    op.drop_index(op.f("ix_intelligence_runs_user_id"), table_name="intelligence_runs")
    op.drop_table("intelligence_runs")
