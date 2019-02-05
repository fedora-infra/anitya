"""Convert Date to RPM

Revision ID: 1ab95561edae
Revises: 6ac0e42df937
Create Date: 2019-01-17 09:45:34.158432
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "1ab95561edae"
down_revision = "6ac0e42df937"


def upgrade():
    """ Any project using Date version scheme should now use RPM version scheme. """
    op.execute(
        """
        UPDATE projects
        SET version_scheme='RPM'
        WHERE version_scheme='Date'
    """
    )


def downgrade():
    """No-op, as project works fine with the old version scheme."""
    raise NotImplementedError
