"""Add cascade delete

Revision ID: c8735fa14a0a
Revises: 34b9bb5fa388
Create Date: 2018-09-04 13:54:40.031238
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c8735fa14a0a"
down_revision = "34b9bb5fa388"


def upgrade():
    """ Rename column `distro` in packages table. """
    op.alter_column("packages", "distro", new_column_name="distro_name")


def downgrade():
    pass
