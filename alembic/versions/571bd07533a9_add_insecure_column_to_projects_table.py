"""Add insecure column to projects table

Revision ID: 571bd07533a9
Revises: None
Create Date: 2015-03-23 17:18:11.421783

"""

# revision identifiers, used by Alembic.
revision = '571bd07533a9'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'projects',
        sa.Column(
            'insecure', sa.Boolean(), nullable=False, server_default=False)
    )


def downgrade():
    op.drop_column('projects', 'insecure')
