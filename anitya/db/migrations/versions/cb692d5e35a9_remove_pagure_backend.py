"""remove pagure backend

Revision ID: cb692d5e35a9
Revises: ebc827e80373
Create Date: 2026-09-21 01:35:34.326403
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "cb692d5e35a9"
down_revision = "ebc827e80373"


def upgrade():
    op.execute(
        "UPDATE projects SET backend = 'custom', "
        "version_url = 'https://pagure.io/' || name || '/releases' "
        "WHERE backend = 'pagure'"
    )


def downgrade():
    pass
