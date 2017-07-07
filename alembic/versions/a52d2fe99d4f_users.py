"""
Add a table for Users.

Revision ID: a52d2fe99d4f
Revises: 8040ef9a9dda
Create Date: 2017-07-06 18:08:56.027650
"""

from alembic import op
import sqlalchemy as sa

from anitya.lib.model import GUID


# revision identifiers, used by Alembic.
revision = 'a52d2fe99d4f'
down_revision = '8040ef9a9dda'


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', GUID, nullable=False),
        sa.Column('email', sa.String(length=256), nullable=False),
        sa.Column('username', sa.String(length=256), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
