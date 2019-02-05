"""Creation date on version

Revision ID: 24b6734e8565
Revises: 34b9bb5fa388
Create Date: 2018-10-01 11:17:19.457383
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "24b6734e8565"
down_revision = "34b9bb5fa388"


def upgrade():
    """ Add `created_on` date column to projects_versions table. """
    op.add_column(
        "projects_versions",
        sa.Column("created_on", sa.DateTime, default=sa.func.current_timestamp()),
    )


def downgrade():
    """ Drop the `created_on` column from the projects_version table. """
    op.drop_column("projects_versions", "created_on")
