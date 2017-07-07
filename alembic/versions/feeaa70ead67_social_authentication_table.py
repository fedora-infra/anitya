"""Social authentication table

Revision ID: feeaa70ead67
Revises: a52d2fe99d4f
Create Date: 2017-07-07 14:23:30.605238
"""

from alembic import op
from social_sqlalchemy import storage
import sqlalchemy as sa

from anitya.lib.model import GUID


# revision identifiers, used by Alembic.
revision = 'feeaa70ead67'
down_revision = 'a52d2fe99d4f'


def upgrade():
    op.create_table(
        'social_auth_association',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_url', sa.String(length=255), nullable=True),
        sa.Column('handle', sa.String(length=255), nullable=True),
        sa.Column('secret', sa.String(length=255), nullable=True),
        sa.Column('issued', sa.Integer(), nullable=True),
        sa.Column('lifetime', sa.Integer(), nullable=True),
        sa.Column('assoc_type', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_url', 'handle')
    )
    op.create_table(
        'social_auth_code',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('code', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'email')
    )
    op.create_index(op.f('ix_social_auth_code_code'), 'social_auth_code', ['code'], unique=False)
    op.create_table(
        'social_auth_nonce',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_url', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.Integer(), nullable=True),
        sa.Column('salt', sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_url', 'timestamp', 'salt')
    )
    op.create_table(
        'social_auth_partial',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=32), nullable=True),
        sa.Column('data', storage.JSONType(), nullable=True),
        sa.Column('next_step', sa.Integer(), nullable=True),
        sa.Column('backend', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_social_auth_partial_token'), 'social_auth_partial', ['token'], unique=False)
    op.create_table(
        'social_auth_usersocialauth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=True),
        sa.Column('extra_data', storage.JSONType(), nullable=True),
        sa.Column('uid', sa.String(length=255), nullable=True),
        sa.Column('user_id', GUID, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], [u'users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_social_auth_usersocialauth_user_id'),
        'social_auth_usersocialauth',
        ['user_id'],
        unique=False
    )


def downgrade():
    op.drop_index(
        op.f('ix_social_auth_usersocialauth_user_id'), table_name='social_auth_usersocialauth')
    op.drop_table('social_auth_usersocialauth')
    op.drop_index(op.f('ix_social_auth_partial_token'), table_name='social_auth_partial')
    op.drop_table('social_auth_partial')
    op.drop_table('social_auth_nonce')
    op.drop_index(op.f('ix_social_auth_code_code'), table_name='social_auth_code')
    op.drop_table('social_auth_code')
    op.drop_table('social_auth_association')
