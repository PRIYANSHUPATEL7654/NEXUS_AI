"""add user profiles

Revision ID: 20260904_03
Revises: 20260902_02
Create Date: 2026-09-04

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers, used by Alembic.
revision: str = "20260904_03"
down_revision: str | None = "20260902_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create one shared profile for every user."""
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "timezone",
            sa.String(length=50),
            server_default="UTC",
            nullable=False,
        ),
        sa.Column(
            "preferred_currency",
            sa.String(length=3),
            server_default="INR",
            nullable=False,
        ),
        sa.Column("learning_goals", sa.Text(), nullable=True),
        sa.Column("work_preferences", sa.Text(), nullable=True),
        sa.Column(
            "ai_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "privacy_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "notification_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO user_profiles (user_id)
            SELECT id
            FROM users
            """
        )
    )


def downgrade() -> None:
    """Remove the shared user-profile table."""
    op.drop_table("user_profiles")
