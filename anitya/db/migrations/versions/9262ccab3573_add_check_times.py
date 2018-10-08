"""Add check times

Revision ID: 9262ccab3573
Revises: 7a8c4aa92678
Create Date: 2018-10-10 10:11:19.281233
"""

from alembic import op
import sqlalchemy as sa
import arrow


# revision identifiers, used by Alembic.
revision = '9262ccab3573'
down_revision = 'b13662e5d288'


def upgrade():
    """ Add next_check and last_check columns to the projects table. """
    op.add_column(
        'projects',
        sa.Column(
            'last_check',
            sa.TIMESTAMP(timezone=True),
            default=arrow.utcnow().datetime
        )
    )

    op.add_column(
        'projects',
        sa.Column(
            'next_check',
            sa.TIMESTAMP(timezone=True),
            default=arrow.utcnow().datetime
        )
    )


def downgrade():
    """ Drop next_check and last_check columns to the projects table. """
    op.drop_column('projects', 'last_check')
    op.drop_column('projects', 'next_check')
