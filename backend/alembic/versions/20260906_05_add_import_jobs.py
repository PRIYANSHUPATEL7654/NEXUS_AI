"""add shared import jobs

Revision ID: 20260906_05
Revises: 20260905_04
Create Date: 2026-09-06

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260906_05"
down_revision: str | None = "20260905_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the reusable import-processing queue table."""
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("target_module", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column("extraction_method", sa.String(length=50), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column(
            "extracted_item_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "warnings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "target_module IN ('knowledge', 'money', 'work')",
            name="ck_import_jobs_target_module",
        ),
        sa.CheckConstraint(
            "status IN ('uploaded', 'extracting', 'parsing', "
            "'awaiting_review', 'completed', 'failed')",
            name="ck_import_jobs_status",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["files.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "file_id",
            "target_module",
            name="uq_import_jobs_file_module",
        ),
    )
    op.create_index(
        op.f("ix_import_jobs_file_id"),
        "import_jobs",
        ["file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_import_jobs_status"),
        "import_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_import_jobs_user_id"),
        "import_jobs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the reusable import-processing queue table."""
    op.drop_index(op.f("ix_import_jobs_user_id"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_status"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_file_id"), table_name="import_jobs")
    op.drop_table("import_jobs")
