"""Add statistics to run

Revision ID: e34988f3e2f4
Revises: 1ab95561edae
Create Date: 2019-03-14 15:41:11.614870
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e34988f3e2f4"
down_revision = "1ab95561edae"


def upgrade():
    """
    Add statistics column to runs table.
    Remove status column to runs table.
    """
    op.add_column("runs", sa.Column("total_count", sa.Integer(), default=0))
    op.add_column("runs", sa.Column("error_count", sa.Integer(), default=0))
    op.add_column("runs", sa.Column("ratelimit_count", sa.Integer(), default=0))
    op.add_column("runs", sa.Column("success_count", sa.Integer(), default=0))
    op.drop_column("runs", "status")


def downgrade():
    """
    Remove statistics column to runs table.
    Add status column to runs table.
    """
    op.drop_column("runs", "total_count")
    op.drop_column("runs", "error_count")
    op.drop_column("runs", "ratelimit_count")
    op.drop_column("runs", "success_count")
    op.add_column(
        "runs",
        sa.Column("status", sa.String(20), primary_key=True, server_default="ended"),
    )
