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
"""Add an API token table.

Revision ID: 3fae8239eeec
Revises: feeaa70ead67
Create Date: 2017-07-31 20:13:54.179584
"""
import uuid

from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3fae8239eeec"
down_revision = "feeaa70ead67"


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
    """Create the ``tokens`` table."""
    op.create_table(
        "tokens",
        sa.Column("token", sa.String(length=40), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("token"),
    )


def downgrade():
    """Drop the ``tokens`` table."""
    op.drop_table("tokens")
