"""Remove code google backend

Revision ID: 2d1aa7ff82a5
Revises: 8be6e153962c
Create Date: 2021-03-17 16:08:13.478078
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "2d1aa7ff82a5"
down_revision = "8be6e153962c"


def upgrade():
    """
    Change backend of projects with code google backend to custom.
    """
    op.execute(
        """
        UPDATE projects
        SET backend='custom'
        WHERE backend='Google code'
    """
    )


def downgrade():
    """
    This change can't be reverted.
    """
    pass
