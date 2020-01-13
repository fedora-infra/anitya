"""add ProjectVersion.commit_url

Revision ID: 16aa7da2764c
Revises: 314651690dc7
Create Date: 2019-12-19 14:54:56.036040
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "16aa7da2764c"
down_revision = "314651690dc7"


def upgrade():
    op.add_column(
        "projects_versions",
        sa.Column("commit_url", sa.String(length=200), nullable=True),
    )


def downgrade():
    with op.batch_alter_table("projects_versions") as batch_op:
        batch_op.drop_column("commit_url")
