"""add shared file metadata

Revision ID: 20260905_04
Revises: 20260904_03
Create Date: 2026-09-05

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "20260905_04"
down_revision: str | None = "20260904_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create shared user-owned file metadata."""
    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "stored_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "storage_path",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "extension",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "sha256_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "processing_status",
            sa.String(length=30),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
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
            "processing_status IN "
            "('uploaded', 'extracting', 'parsing', "
            "'awaiting_review', 'completed', 'failed')",
            name="ck_files_processing_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
        sa.UniqueConstraint(
            "user_id",
            "sha256_hash",
            name="uq_files_user_hash",
        ),
    )

    op.create_index(
        op.f("ix_files_processing_status"),
        "files",
        ["processing_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_files_user_id"),
        "files",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove shared file metadata."""
    op.drop_index(
        op.f("ix_files_user_id"),
        table_name="files",
    )
    op.drop_index(
        op.f("ix_files_processing_status"),
        table_name="files",
    )
    op.drop_table("files")
