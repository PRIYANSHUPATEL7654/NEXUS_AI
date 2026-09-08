"""add nexus work projects, tasks and reviewed document plans

Revision ID: 20260910_10
Revises: 20260909_09
Create Date: 2026-09-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260910_10"
down_revision: str | None = "20260909_09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "work_projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("client_name", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), server_default="planned", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('planned', 'in_progress', 'blocked', 'completed', 'cancelled')",
            name="ck_work_projects_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_work_projects_user_id"), "work_projects", ["user_id"], unique=False)
    op.create_index(op.f("ix_work_projects_status"), "work_projects", ["status"], unique=False)

    op.create_table(
        "work_plan_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("import_job_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), server_default="awaiting_review", nullable=False),
        sa.Column("proposed_project_title", sa.String(200), nullable=False),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.Column("estimated_minutes_low", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes_high", sa.Integer(), nullable=False),
        sa.Column("estimate_confidence", sa.String(10), nullable=False),
        sa.Column("assumptions", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('awaiting_review', 'approved', 'cancelled')", name="ck_work_plan_imports_status"),
        sa.CheckConstraint("estimate_confidence IN ('low', 'medium', 'high')", name="ck_work_plan_imports_confidence"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["work_projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("import_job_id", name="uq_work_plan_imports_import_job_id"),
    )
    op.create_index(op.f("ix_work_plan_imports_user_id"), "work_plan_imports", ["user_id"], unique=False)
    op.create_index(op.f("ix_work_plan_imports_project_id"), "work_plan_imports", ["project_id"], unique=False)
    op.create_index(op.f("ix_work_plan_imports_file_id"), "work_plan_imports", ["file_id"], unique=False)
    op.create_index(op.f("ix_work_plan_imports_status"), "work_plan_imports", ["status"], unique=False)

    op.create_table(
        "work_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("parent_task_id", sa.Integer(), nullable=True),
        sa.Column("source_plan_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="planned", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="3", nullable=False),
        sa.Column("complexity", sa.Integer(), server_default="3", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("estimated_minutes_low", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes_high", sa.Integer(), nullable=False),
        sa.Column("actual_minutes", sa.Integer(), nullable=True),
        sa.Column("dependencies", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('backlog', 'planned', 'in_progress', 'blocked', 'completed', 'cancelled')", name="ck_work_tasks_status"),
        sa.CheckConstraint("priority BETWEEN 1 AND 5", name="ck_work_tasks_priority"),
        sa.CheckConstraint("complexity BETWEEN 1 AND 5", name="ck_work_tasks_complexity"),
        sa.CheckConstraint("estimated_minutes_low > 0", name="ck_work_tasks_estimate_low"),
        sa.CheckConstraint("estimated_minutes_high >= estimated_minutes_low", name="ck_work_tasks_estimate_range"),
        sa.CheckConstraint("actual_minutes IS NULL OR actual_minutes >= 0", name="ck_work_tasks_actual_minutes"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["work_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_task_id"], ["work_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_plan_id"], ["work_plan_imports.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_work_tasks_user_id"), "work_tasks", ["user_id"], unique=False)
    op.create_index(op.f("ix_work_tasks_project_id"), "work_tasks", ["project_id"], unique=False)
    op.create_index(op.f("ix_work_tasks_status"), "work_tasks", ["status"], unique=False)

    op.create_table(
        "work_task_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_import_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="3", nullable=False),
        sa.Column("complexity", sa.Integer(), server_default="3", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("estimated_minutes_low", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes_high", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("source_location", sa.String(120), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("priority BETWEEN 1 AND 5", name="ck_work_task_drafts_priority"),
        sa.CheckConstraint("complexity BETWEEN 1 AND 5", name="ck_work_task_drafts_complexity"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_work_task_drafts_confidence"),
        sa.CheckConstraint("estimated_minutes_low > 0", name="ck_work_task_drafts_estimate_low"),
        sa.CheckConstraint("estimated_minutes_high >= estimated_minutes_low", name="ck_work_task_drafts_estimate_range"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_import_id"], ["work_plan_imports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_work_task_drafts_user_id"), "work_task_drafts", ["user_id"], unique=False)
    op.create_index(op.f("ix_work_task_drafts_plan_import_id"), "work_task_drafts", ["plan_import_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_work_task_drafts_plan_import_id"), table_name="work_task_drafts")
    op.drop_index(op.f("ix_work_task_drafts_user_id"), table_name="work_task_drafts")
    op.drop_table("work_task_drafts")
    op.drop_index(op.f("ix_work_tasks_status"), table_name="work_tasks")
    op.drop_index(op.f("ix_work_tasks_project_id"), table_name="work_tasks")
    op.drop_index(op.f("ix_work_tasks_user_id"), table_name="work_tasks")
    op.drop_table("work_tasks")
    op.drop_index(op.f("ix_work_plan_imports_status"), table_name="work_plan_imports")
    op.drop_index(op.f("ix_work_plan_imports_file_id"), table_name="work_plan_imports")
    op.drop_index(op.f("ix_work_plan_imports_project_id"), table_name="work_plan_imports")
    op.drop_index(op.f("ix_work_plan_imports_user_id"), table_name="work_plan_imports")
    op.drop_table("work_plan_imports")
    op.drop_index(op.f("ix_work_projects_status"), table_name="work_projects")
    op.drop_index(op.f("ix_work_projects_user_id"), table_name="work_projects")
    op.drop_table("work_projects")
