"""Add archive flag

Revision ID: 1f839c54e428
Revises: d6170cfc2814
Create Date: 2020-07-13 12:00:39.800783
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1f839c54e428"
down_revision = "d6170cfc2814"


def upgrade():
    """ Add archived column to the projects table. """
    op.add_column(
        "projects",
        sa.Column(
            "archived",
            sa.Boolean(),
            default=False,
            server_default="FALSE",
            nullable=False,
        ),
    )


def downgrade():
    """ Drop archived column to the projects table. """
    op.drop_column("projects", "archived")
