# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright © 2018 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""
Make ecosystem non-nullable.

Revision ID: 34b9bb5fa388
Revises: 3fae8239eeec
Create Date: 2018-01-15 22:10:34.624110
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "34b9bb5fa388"
down_revision = "3fae8239eeec"


def upgrade():
    """Make the ecosystem_name non-nullable after setting null instances to the homepage."""
    op.execute(
        """
        UPDATE projects
        SET ecosystem_name=homepage
        WHERE ecosystem_name IS NULL
    """
    )
    op.alter_column(
        "projects",
        "ecosystem_name",
        existing_type=sa.VARCHAR(length=200),
        nullable=False,
    )


def downgrade():
    """Make the ecosystem_name nullable."""
    op.alter_column(
        "projects",
        "ecosystem_name",
        existing_type=sa.VARCHAR(length=200),
        nullable=True,
    )
    op.execute(
        """
        UPDATE projects
        SET ecosystem_name=NULL
        WHERE ecosystem_name=homepage
    """
    )
