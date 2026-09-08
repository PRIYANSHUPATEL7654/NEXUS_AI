"""add nexus learn foundation

Revision ID: 20260907_07
Revises: 20260906_06
Create Date: 2026-09-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260907_07"
down_revision: str | None = "20260906_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="3", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'paused', 'completed')", name="ck_learning_goals_status"),
        sa.CheckConstraint("priority BETWEEN 1 AND 5", name="ck_learning_goals_priority"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_goals_user_id"), "learning_goals", ["user_id"], unique=False)
    op.create_index(op.f("ix_learning_goals_status"), "learning_goals", ["status"], unique=False)

    op.create_table(
        "learning_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("current_level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("target_level", sa.Integer(), server_default="80", nullable=False),
        sa.Column("status", sa.String(20), server_default="not_started", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("current_level BETWEEN 0 AND 100", name="ck_learning_topics_current_level"),
        sa.CheckConstraint("target_level BETWEEN 1 AND 100", name="ck_learning_topics_target_level"),
        sa.CheckConstraint("status IN ('not_started', 'in_progress', 'mastered')", name="ck_learning_topics_status"),
        sa.ForeignKeyConstraint(["goal_id"], ["learning_goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["knowledge_documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("goal_id", "title", name="uq_learning_topics_goal_title"),
    )
    op.create_index(op.f("ix_learning_topics_goal_id"), "learning_topics", ["goal_id"], unique=False)
    op.create_index(op.f("ix_learning_topics_user_id"), "learning_topics", ["user_id"], unique=False)

    op.create_table(
        "learning_progress_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("study_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_learning_progress_percent"),
        sa.CheckConstraint("study_minutes BETWEEN 0 AND 1440", name="ck_learning_progress_study_minutes"),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_progress_entries_topic_id"), "learning_progress_entries", ["topic_id"], unique=False)
    op.create_index(op.f("ix_learning_progress_entries_user_id"), "learning_progress_entries", ["user_id"], unique=False)

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_option_index", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("generation_method", sa.String(50), server_default="local_cloze_v1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("correct_option_index BETWEEN 0 AND 3", name="ck_quiz_questions_correct_index"),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quiz_questions_topic_id"), "quiz_questions", ["topic_id"], unique=False)
    op.create_index(op.f("ix_quiz_questions_user_id"), "quiz_questions", ["user_id"], unique=False)

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option_index", sa.Integer(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("selected_option_index BETWEEN 0 AND 3", name="ck_quiz_attempts_selected_index"),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quiz_attempts_question_id"), "quiz_attempts", ["question_id"], unique=False)
    op.create_index(op.f("ix_quiz_attempts_user_id"), "quiz_attempts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_quiz_attempts_user_id"), table_name="quiz_attempts")
    op.drop_index(op.f("ix_quiz_attempts_question_id"), table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index(op.f("ix_quiz_questions_user_id"), table_name="quiz_questions")
    op.drop_index(op.f("ix_quiz_questions_topic_id"), table_name="quiz_questions")
    op.drop_table("quiz_questions")
    op.drop_index(op.f("ix_learning_progress_entries_user_id"), table_name="learning_progress_entries")
    op.drop_index(op.f("ix_learning_progress_entries_topic_id"), table_name="learning_progress_entries")
    op.drop_table("learning_progress_entries")
    op.drop_index(op.f("ix_learning_topics_user_id"), table_name="learning_topics")
    op.drop_index(op.f("ix_learning_topics_goal_id"), table_name="learning_topics")
    op.drop_table("learning_topics")
    op.drop_index(op.f("ix_learning_goals_status"), table_name="learning_goals")
    op.drop_index(op.f("ix_learning_goals_user_id"), table_name="learning_goals")
    op.drop_table("learning_goals")
