"""
Remove all the socialauth tables

Revision ID: 8ba7d4c42044
Revises: 2d1aa7ff82a5
Create Date: 2024-11-29 09:36:00.486832
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8ba7d4c42044"
down_revision = "2d1aa7ff82a5"


def upgrade():
    """
    Removes all the socialauth tables.
    """
    op.drop_table("social_auth_nonce")
    op.drop_index("ix_social_auth_code_code", table_name="social_auth_code")
    op.drop_table("social_auth_code")
    op.drop_table("social_auth_association")
    op.drop_index("ix_social_auth_partial_token", table_name="social_auth_partial")
    op.drop_table("social_auth_partial")
    op.drop_index(
        "ix_social_auth_usersocialauth_user_id", table_name="social_auth_usersocialauth"
    )
    op.drop_table("social_auth_usersocialauth")
    # ### end Alembic commands ###


def downgrade():
    """
    Restores the tables without data.
    """
    op.create_table(
        "social_auth_usersocialauth",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "provider", sa.VARCHAR(length=32), autoincrement=False, nullable=True
        ),
        sa.Column("extra_data", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("uid", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="social_auth_usersocialauth_user_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="social_auth_usersocialauth_pkey"),
    )
    op.create_index(
        "ix_social_auth_usersocialauth_user_id",
        "social_auth_usersocialauth",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "social_auth_partial",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("token", sa.VARCHAR(length=32), autoincrement=False, nullable=True),
        sa.Column("data", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("next_step", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("backend", sa.VARCHAR(length=32), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="social_auth_partial_pkey"),
    )
    op.create_index(
        "ix_social_auth_partial_token", "social_auth_partial", ["token"], unique=False
    )
    op.create_table(
        "social_auth_association",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "server_url", sa.VARCHAR(length=255), autoincrement=False, nullable=True
        ),
        sa.Column("handle", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("secret", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("issued", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("lifetime", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "assoc_type", sa.VARCHAR(length=64), autoincrement=False, nullable=True
        ),
        sa.PrimaryKeyConstraint("id", name="social_auth_association_pkey"),
        sa.UniqueConstraint(
            "server_url", "handle", name="social_auth_association_server_url_handle_key"
        ),
    )
    op.create_table(
        "social_auth_code",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("email", sa.VARCHAR(length=200), autoincrement=False, nullable=True),
        sa.Column("code", sa.VARCHAR(length=32), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="social_auth_code_pkey"),
        sa.UniqueConstraint("code", "email", name="social_auth_code_code_email_key"),
    )
    op.create_index(
        "ix_social_auth_code_code", "social_auth_code", ["code"], unique=False
    )
    op.create_table(
        "social_auth_nonce",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "server_url", sa.VARCHAR(length=255), autoincrement=False, nullable=True
        ),
        sa.Column("timestamp", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("salt", sa.VARCHAR(length=40), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="social_auth_nonce_pkey"),
        sa.UniqueConstraint(
            "server_url",
            "timestamp",
            "salt",
            name="social_auth_nonce_server_url_timestamp_salt_key",
        ),
    )
