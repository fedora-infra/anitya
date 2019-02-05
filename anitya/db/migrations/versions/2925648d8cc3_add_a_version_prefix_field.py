"""Add a version_prefix field

Revision ID: 2925648d8cc3
Revises: 571bd07533a9
Create Date: 2015-10-22 09:49:10.757572

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2925648d8cc3"
down_revision = "571bd07533a9"


def upgrade():
    """ Add the `version_prefix` column on the projects table. """
    op.add_column(
        "projects", sa.Column("version_prefix", sa.String(200), nullable=True)
    )


def downgrade():
    """ Drop the `version_prefix` column of the projects table. """
    op.drop_column("projects", "version_prefix")
