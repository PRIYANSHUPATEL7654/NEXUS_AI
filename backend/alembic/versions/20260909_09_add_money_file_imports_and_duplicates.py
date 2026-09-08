"""add money file imports, duplicate review and fingerprints

Revision ID: 20260909_09
Revises: 20260908_08
Create Date: 2026-09-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260909_09"
down_revision: str | None = "20260908_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("money_import_batches", sa.Column("file_id", sa.Integer(), nullable=True))
    op.add_column("money_import_batches", sa.Column("import_job_id", sa.Integer(), nullable=True))
    op.add_column("money_import_batches", sa.Column("extraction_method", sa.String(50), nullable=True))
    op.create_foreign_key(
        "fk_money_import_batches_file_id",
        "money_import_batches",
        "files",
        ["file_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_money_import_batches_import_job_id",
        "money_import_batches",
        "import_jobs",
        ["import_job_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_money_import_batches_file_id"), "money_import_batches", ["file_id"], unique=False)
    op.create_unique_constraint("uq_money_import_batches_import_job_id", "money_import_batches", ["import_job_id"])

    op.add_column("money_transaction_drafts", sa.Column("source_location", sa.String(120), nullable=True))
    op.add_column(
        "money_transaction_drafts",
        sa.Column("possible_duplicate", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("money_transaction_drafts", sa.Column("duplicate_transaction_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_money_transaction_drafts_duplicate_transaction_id",
        "money_transaction_drafts",
        "money_transactions",
        ["duplicate_transaction_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("money_transactions", sa.Column("fingerprint", sa.String(64), nullable=True))
    op.create_index(op.f("ix_money_transactions_fingerprint"), "money_transactions", ["fingerprint"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_money_transactions_fingerprint"), table_name="money_transactions")
    op.drop_column("money_transactions", "fingerprint")
    op.drop_constraint(
        "fk_money_transaction_drafts_duplicate_transaction_id",
        "money_transaction_drafts",
        type_="foreignkey",
    )
    op.drop_column("money_transaction_drafts", "duplicate_transaction_id")
    op.drop_column("money_transaction_drafts", "possible_duplicate")
    op.drop_column("money_transaction_drafts", "source_location")
    op.drop_constraint("uq_money_import_batches_import_job_id", "money_import_batches", type_="unique")
    op.drop_index(op.f("ix_money_import_batches_file_id"), table_name="money_import_batches")
    op.drop_constraint("fk_money_import_batches_import_job_id", "money_import_batches", type_="foreignkey")
    op.drop_constraint("fk_money_import_batches_file_id", "money_import_batches", type_="foreignkey")
    op.drop_column("money_import_batches", "extraction_method")
    op.drop_column("money_import_batches", "import_job_id")
    op.drop_column("money_import_batches", "file_id")
