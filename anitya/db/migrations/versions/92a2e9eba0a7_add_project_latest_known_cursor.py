"""add Project.latest_known_cursor

Revision ID: 92a2e9eba0a7
Revises: 5e209766aead
Create Date: 2019-12-12 10:11:38.652950
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "92a2e9eba0a7"
down_revision = "5e209766aead"


def upgrade():
    op.add_column(
        "projects",
        sa.Column("latest_known_cursor", sa.String(length=200), nullable=True),
    )


def downgrade():
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("latest_known_cursor")
