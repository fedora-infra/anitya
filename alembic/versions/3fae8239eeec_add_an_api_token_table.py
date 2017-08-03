"""Add an API token table.

Revision ID: 3fae8239eeec
Revises: feeaa70ead67
Create Date: 2017-07-31 20:13:54.179584
"""

from alembic import op
import sqlalchemy as sa

from anitya.lib.model import GUID


# revision identifiers, used by Alembic.
revision = '3fae8239eeec'
down_revision = 'feeaa70ead67'


def upgrade():
    """Create the ``tokens`` table."""
    op.create_table(
        'tokens',
        sa.Column('token', sa.String(length=40), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('token')
    )


def downgrade():
    """Drop the ``tokens`` table."""
    op.drop_table('tokens')
