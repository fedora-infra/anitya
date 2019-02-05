"""Add check times

Revision ID: 1bf8aead6179
Revises: b13662e5d288
Create Date: 2018-12-07 08:58:45.152649
"""

from alembic import op
import sqlalchemy as sa
import arrow


# revision identifiers, used by Alembic.
revision = "1bf8aead6179"
down_revision = "b13662e5d288"


def upgrade():
    """ Add next_check and last_check columns to the projects table. """
    op.add_column(
        "projects",
        sa.Column(
            "last_check",
            sa.TIMESTAMP(timezone=True),
            default=arrow.utcnow().datetime,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.add_column(
        "projects",
        sa.Column(
            "next_check",
            sa.TIMESTAMP(timezone=True),
            default=arrow.utcnow().datetime,
            server_default=sa.func.current_timestamp(),
        ),
    )
    op.create_index(
        op.f("ix_projects_last_check"), "projects", ["last_check"], unique=False
    )
    op.create_index(
        op.f("ix_projects_next_check"), "projects", ["next_check"], unique=False
    )


def downgrade():
    """ Drop next_check and last_check columns to the projects table. """
    op.drop_column("projects", "last_check")
    op.drop_column("projects", "next_check")
    op.drop_index(op.f("ix_projects_next_check"), table_name="projects")
    op.drop_index(op.f("ix_projects_last_check"), table_name="projects")
