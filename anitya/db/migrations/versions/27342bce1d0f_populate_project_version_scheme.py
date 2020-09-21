"""Populate project version scheme

Revision ID: 27342bce1d0f
Revises: 24b6734e8565
Create Date: 2018-10-03 07:07:47.573097
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "27342bce1d0f"
down_revision = "24b6734e8565"


def upgrade():
    """Populate projects version_scheme column by RPM value.
    This was the only available version value before this update.
    In newer version of Anitya you can change the value when editing project.
    """
    op.execute(
        """
        UPDATE projects
        SET version_scheme='RPM'
        WHERE version_scheme is null
    """
    )


def downgrade():
    """ No need to downgrade, there was only one versioning scheme previously """
    raise NotImplementedError
