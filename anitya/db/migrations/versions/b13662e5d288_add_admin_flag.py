"""Add admin flag

Revision ID: b13662e5d288
Revises: ac10bf3f974c
Create Date: 2018-11-14 10:02:06.593605
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b13662e5d288"
down_revision = "ac10bf3f974c"


def upgrade():
    """ Add 'admin' flag to users table. """
    op.add_column("users", sa.Column("admin", sa.Boolean, default=False))


def downgrade():
    """ Drop 'admin' flag from users table. """
    op.drop_column("users", "admin")
