"""add nexus money manual and pasted text imports

Revision ID: 20260908_08
Revises: 20260907_07
Create Date: 2026-09-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260908_08"
down_revision: str | None = "20260907_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "money_import_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(20), server_default="pasted_text", nullable=False),
        sa.Column("status", sa.String(20), server_default="awaiting_review", nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("default_currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("source_type IN ('pasted_text', 'file')", name="ck_money_import_batches_source"),
        sa.CheckConstraint("status IN ('awaiting_review', 'approved', 'cancelled')", name="ck_money_import_batches_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_money_import_batches_user_id"), "money_import_batches", ["user_id"], unique=False)
    op.create_index(op.f("ix_money_import_batches_status"), "money_import_batches", ["status"], unique=False)

    op.create_table(
        "money_transaction_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("transaction_type", sa.String(10), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_money_drafts_positive_amount"),
        sa.CheckConstraint("transaction_type IN ('expense', 'income')", name="ck_money_drafts_type"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_money_drafts_confidence"),
        sa.ForeignKeyConstraint(["batch_id"], ["money_import_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_money_transaction_drafts_batch_id"), "money_transaction_drafts", ["batch_id"], unique=False)
    op.create_index(op.f("ix_money_transaction_drafts_user_id"), "money_transaction_drafts", ["user_id"], unique=False)

    op.create_table(
        "money_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("transaction_type", sa.String(10), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR", nullable=False),
        sa.Column("source", sa.String(20), server_default="manual", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_money_transactions_positive_amount"),
        sa.CheckConstraint("transaction_type IN ('expense', 'income')", name="ck_money_transactions_type"),
        sa.CheckConstraint("source IN ('manual', 'pasted_text', 'file')", name="ck_money_transactions_source"),
        sa.ForeignKeyConstraint(["batch_id"], ["money_import_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_money_transactions_user_id"), "money_transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_money_transactions_transaction_date"), "money_transactions", ["transaction_date"], unique=False)
    op.create_index(op.f("ix_money_transactions_category"), "money_transactions", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_money_transactions_category"), table_name="money_transactions")
    op.drop_index(op.f("ix_money_transactions_transaction_date"), table_name="money_transactions")
    op.drop_index(op.f("ix_money_transactions_user_id"), table_name="money_transactions")
    op.drop_table("money_transactions")
    op.drop_index(op.f("ix_money_transaction_drafts_user_id"), table_name="money_transaction_drafts")
    op.drop_index(op.f("ix_money_transaction_drafts_batch_id"), table_name="money_transaction_drafts")
    op.drop_table("money_transaction_drafts")
    op.drop_index(op.f("ix_money_import_batches_status"), table_name="money_import_batches")
    op.drop_index(op.f("ix_money_import_batches_user_id"), table_name="money_import_batches")
    op.drop_table("money_import_batches")
