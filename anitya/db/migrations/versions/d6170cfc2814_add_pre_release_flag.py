"""Add pre-release flag

Revision ID: d6170cfc2814
Revises: 16aa7da2764c
Create Date: 2020-07-08 12:09:51.416356
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d6170cfc2814"
down_revision = "16aa7da2764c"


def upgrade():
    """
    Add new pre-release column to project.
    """
    op.add_column(
        "projects",
        sa.Column("pre_release_filter", sa.String(length=200), nullable=True),
    )


def downgrade():
    """
    Drop pre-release columns from project.
    """
    op.drop_column("projects", "pre_release_filter")
