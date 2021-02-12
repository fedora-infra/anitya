"""Remove cursor

Revision ID: 8be6e153962c
Revises: 5b8b587d7dbe
Create Date: 2021-02-12 12:56:51.230774
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8be6e153962c"
down_revision = "5b8b587d7dbe"


def upgrade():
    """
    Remove latest_version_cursor from project.
    """
    op.drop_column("projects", "latest_version_cursor")


def downgrade():
    """
    Add latest_version_cursor back to project.
    """
    op.add_column(
        "projects",
        sa.Column(
            "latest_version_cursor",
            sa.VARCHAR(length=200),
            autoincrement=False,
            nullable=True,
        ),
    )
