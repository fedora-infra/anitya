"""
Add a version scheme column to Projects

Revision ID: 8040ef9a9dda
Revises: b9201d816075
Create Date: 2017-04-19 14:50:54.736648
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8040ef9a9dda"
down_revision = "b9201d816075"


def upgrade():
    """Add the version_scheme column to the projects table."""
    op.add_column(
        "projects", sa.Column("version_scheme", sa.String(length=50), nullable=True)
    )


def downgrade():
    """Remove the version_scheme column from the projects table."""
    op.drop_column("projects", "version_scheme")
