"""add knowledge documents and summaries

Revision ID: 20260906_06
Revises: 20260906_05
Create Date: 2026-09-06

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260906_06"
down_revision: str | None = "20260906_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Knowledge documents and their generated summaries."""
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("import_job_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("extraction_method", sa.String(length=50), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["files.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_jobs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_id"),
        sa.UniqueConstraint("import_job_id"),
    )
    op.create_index(
        op.f("ix_knowledge_documents_title"),
        "knowledge_documents",
        ["title"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_user_id"),
        "knowledge_documents",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "knowledge_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("summary_type", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "generation_method",
            sa.String(length=50),
            server_default="local_extractive_v1",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "summary_type IN "
            "('short', 'detailed', 'revision_notes', 'key_insights')",
            name="ck_knowledge_summaries_type",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_summaries_document_id"),
        "knowledge_summaries",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_summaries_user_id"),
        "knowledge_summaries",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove Knowledge summaries and documents."""
    op.drop_index(
        op.f("ix_knowledge_summaries_user_id"),
        table_name="knowledge_summaries",
    )
    op.drop_index(
        op.f("ix_knowledge_summaries_document_id"),
        table_name="knowledge_summaries",
    )
    op.drop_table("knowledge_summaries")
    op.drop_index(
        op.f("ix_knowledge_documents_user_id"),
        table_name="knowledge_documents",
    )
    op.drop_index(
        op.f("ix_knowledge_documents_title"),
        table_name="knowledge_documents",
    )
    op.drop_table("knowledge_documents")
