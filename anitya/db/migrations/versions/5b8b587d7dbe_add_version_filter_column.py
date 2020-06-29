"""Add version_filter column

Revision ID: 5b8b587d7dbe
Revises: 1f839c54e428
Create Date: 2020-06-29 13:11:50.961730
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5b8b587d7dbe"
down_revision = "1f839c54e428"


def upgrade():
    """ Add the `version_filter` column on the projects table. """
    op.add_column(
        "projects", sa.Column("version_filter", sa.String(200), nullable=True)
    )


def downgrade():
    """ Drop the `version_filter` column of the projects table. """
    op.drop_column("projects", "version_filter")
