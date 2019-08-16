# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2017 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""Social authentication table

Revision ID: feeaa70ead67
Revises: a52d2fe99d4f
Create Date: 2017-07-07 14:23:30.605238
"""
import uuid

from alembic import op
from social_sqlalchemy import storage
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "feeaa70ead67"
down_revision = "a52d2fe99d4f"


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    If PostgreSQL is being used, use its native UUID type, otherwise use a CHAR(32) type.
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        """
        PostgreSQL has a native UUID type, so use it if we're using PostgreSQL.

        Args:
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            sqlalchemy.types.TypeEngine: Either a PostgreSQL UUID or a CHAR(32) on other
                dialects.
        """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        """
        Process the value being bound.

        If PostgreSQL is in use, just use the string representation of the UUID.
        Otherwise, use the integer as a hex-encoded string.

        Args:
            value (object): The value that's being bound to the object.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            str: The value of the UUID as a string.
        """
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        """
        Casts the UUID value to the native Python type.

        Args:
            value (object): The database value.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            uuid.UUID: The value as a Python :class:`uuid.UUID`.
        """
        if value is None:
            return value
        else:
            return uuid.UUID(value)


def upgrade():
    """Create the tables necessary for the python-social-auth library."""
    op.create_table(
        "social_auth_association",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_url", sa.String(length=255), nullable=True),
        sa.Column("handle", sa.String(length=255), nullable=True),
        sa.Column("secret", sa.String(length=255), nullable=True),
        sa.Column("issued", sa.Integer(), nullable=True),
        sa.Column("lifetime", sa.Integer(), nullable=True),
        sa.Column("assoc_type", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("server_url", "handle"),
    )
    op.create_table(
        "social_auth_code",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("code", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "email"),
    )
    op.create_index(
        op.f("ix_social_auth_code_code"), "social_auth_code", ["code"], unique=False
    )
    op.create_table(
        "social_auth_nonce",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_url", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.Integer(), nullable=True),
        sa.Column("salt", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("server_url", "timestamp", "salt"),
    )
    op.create_table(
        "social_auth_partial",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=32), nullable=True),
        sa.Column("data", storage.JSONType(), nullable=True),
        sa.Column("next_step", sa.Integer(), nullable=True),
        sa.Column("backend", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_social_auth_partial_token"),
        "social_auth_partial",
        ["token"],
        unique=False,
    )
    op.create_table(
        "social_auth_usersocialauth",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("extra_data", storage.JSONType(), nullable=True),
        sa.Column("uid", sa.String(length=255), nullable=True),
        sa.Column("user_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_social_auth_usersocialauth_user_id"),
        "social_auth_usersocialauth",
        ["user_id"],
        unique=False,
    )


def downgrade():
    """Drop the tables necessary for the python-social-auth library."""
    op.drop_index(
        op.f("ix_social_auth_usersocialauth_user_id"),
        table_name="social_auth_usersocialauth",
    )
    op.drop_table("social_auth_usersocialauth")
    op.drop_index(
        op.f("ix_social_auth_partial_token"), table_name="social_auth_partial"
    )
    op.drop_table("social_auth_partial")
    op.drop_table("social_auth_nonce")
    op.drop_index(op.f("ix_social_auth_code_code"), table_name="social_auth_code")
    op.drop_table("social_auth_code")
    op.drop_table("social_auth_association")
