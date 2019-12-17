"""Add error counter to project

Revision ID: 314651690dc7
Revises: 136d119ab015
Create Date: 2019-12-17 11:55:12.472854
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "314651690dc7"
down_revision = "136d119ab015"


def upgrade():
    """ Add error_counter column to project. """
    op.add_column(
        "projects",
        sa.Column(
            "error_counter", sa.Integer(), default=0, server_default=sa.text("0")
        ),
    )
    op.create_index(
        op.f("ix_projects_error_counter"), "projects", ["error_counter"], unique=False
    )


def downgrade():
    """ Remove error_counter column from project. """
    op.drop_column("projects", "error_counter")
    op.drop_index(op.f("ix_projects_error_counter"), table_name="projects")
