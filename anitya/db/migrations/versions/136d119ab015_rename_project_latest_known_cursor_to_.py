"""rename Project.latest_known_cursor to latest_version_cursor

Revision ID: 136d119ab015
Revises: 92a2e9eba0a7
Create Date: 2019-12-20 20:56:25.783460
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "136d119ab015"
down_revision = "92a2e9eba0a7"


def upgrade():
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "latest_known_cursor", new_column_name="latest_version_cursor"
        )


def downgrade():
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "latest_version_cursor", new_column_name="latest_known_cursor"
        )
