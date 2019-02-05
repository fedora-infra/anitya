"""Add missing GitHub owner/project pairs

Revision ID: 7a8c4aa92678
Revises: 540bdcf7edbc
Create Date: 2018-10-08 12:25:07.006729
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "7a8c4aa92678"
down_revision = "540bdcf7edbc"


def upgrade():
    """Populate missing GitHub owner/project pairs from homepage."""
    op.execute(
        """
        UPDATE projects
        SET version_url=trim(substr(trim(homepage), 19), '/')
        WHERE backend = 'GitHub'
            AND trim(homepage) LIKE 'http://github.com/%'
            AND (version_url IS NULL OR version_url = '')
    """
    )
    op.execute(
        """
        UPDATE projects
        SET version_url=trim(substr(trim(homepage), 20), '/')
        WHERE backend = 'GitHub'
            AND trim(homepage) LIKE 'https://github.com/%'
            AND (version_url IS NULL OR version_url = '')
    """
    )


def downgrade():
    """No-op, as empty version_url wouldn't have worked before anyway."""
    raise NotImplementedError
