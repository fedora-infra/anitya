"""Convert GitHub URL to owner/project

Revision ID: 540bdcf7edbc
Revises: 27342bce1d0f
Create Date: 2018-10-08 11:23:33.361838
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "540bdcf7edbc"
down_revision = "27342bce1d0f"


def upgrade():
    """Convert GitHub URL to owner/project to work with the new GitHub backend."""
    op.execute(
        """
        UPDATE projects
        SET version_url=trim(substr(version_url, 19), '/')
        WHERE backend = 'GitHub' AND version_url LIKE 'http://github.com/%'
    """
    )
    op.execute(
        """
        UPDATE projects
        SET version_url=trim(substr(version_url, 20), '/')
        WHERE backend = 'GitHub' AND version_url LIKE 'https://github.com/%'
    """
    )


def downgrade():
    """No-op, as owner/project works fine with the old GitHub backend."""
    raise NotImplementedError
