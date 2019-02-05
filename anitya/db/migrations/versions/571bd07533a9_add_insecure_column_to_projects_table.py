"""Add insecure column to projects table

Revision ID: 571bd07533a9
Revises: None
Create Date: 2015-03-23 17:18:11.421783

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "571bd07533a9"
down_revision = None


def upgrade():
    """ Add the `insecure` column on the projects table. """
    op.add_column(
        "projects",
        sa.Column(
            "insecure",
            sa.Boolean,
            default=False,
            server_default="FALSE",
            nullable=False,
        ),
    )


def downgrade():
    """ Drop the `insecure` column of the projects table. """
    op.drop_column("projects", "insecure")
