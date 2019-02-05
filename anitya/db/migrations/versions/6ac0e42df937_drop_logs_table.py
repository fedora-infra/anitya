"""Drop logs table

Revision ID: 6ac0e42df937
Revises: 7a8c4aa92678
Create Date: 2018-10-11 11:42:44.947483
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6ac0e42df937"
down_revision = "1bf8aead6179"


def upgrade():
    """
    Drop logs table.
    Add and fill check_successful column to projects table.
    """
    op.drop_table("logs")

    op.add_column("projects", sa.Column("check_successful", sa.Boolean, default=None))

    op.execute(
        """
        UPDATE projects
        SET check_successful=TRUE
        WHERE (logs='Version retrieved correctly'
        OR logs='No new version found')
        AND check_successful IS NULL
    """
    )

    op.execute(
        """
        UPDATE projects
        SET check_successful=FALSE
        WHERE logs IS NOT NULL
        AND check_successful IS NULL
    """
    )


def downgrade():
    """
    Create the logs table.
    Drop updated column from projects table.
    """
    op.create_table(
        "logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user", sa.String(length=200), nullable=False),
        sa.Column("project", sa.String(length=200), nullable=True),
        sa.Column("distro", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_logs_distro"), "logs", ["distro"], unique=False)
    op.create_index(op.f("ix_logs_project"), "logs", ["project"], unique=False)
    op.create_index(op.f("ix_logs_user"), "logs", ["user"], unique=False)
    op.drop_column("projects", "check_successful")
