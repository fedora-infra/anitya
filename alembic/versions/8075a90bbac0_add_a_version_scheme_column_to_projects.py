"""
Add a version scheme column to Projects

Revision ID: 8075a90bbac0
Revises: 9c29da0af3af
Create Date: 2017-03-09 21:32:35.672952
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8075a90bbac0'
down_revision = '9c29da0af3af'


def upgrade():
    op.add_column('projects_versions', sa.Column('type', sa.String(length=50),
                  nullable=False, server_default='PEP-440'))
    # Once we initialize all the rows with a default, we can drop the server
    # default. We want it to be set automatically by a pre-flush hook in Anitya
    # or explicitly by outside users.
    op.alter_column('projects_versions', 'type', server_default=None)
    op.add_column('projects', sa.Column('version_scheme', sa.String(length=50),
                  nullable=False, server_default='PEP-440'))


def downgrade():
    op.drop_column('projects_versions', 'type')
    op.drop_column('projects', 'version_scheme')
