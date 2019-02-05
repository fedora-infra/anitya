"""Populate missing ecosystem data

Revision ID: 9c29da0af3af
Revises: 921c612ba0da
Create Date: 2017-01-11 22:23:58.497998

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9c29da0af3af"
down_revision = "921c612ba0da"


def upgrade():
    # We use a subquery instead of an UPDATE FROM with a table join
    # due to the fact that SQLite doesn't allow joins in update statements
    op.execute(
        """
        UPDATE projects
        SET ecosystem_name=(
            SELECT ecosystems.name
            FROM projects AS subquery_projects
                INNER JOIN ecosystems ON
                    subquery_projects.backend = ecosystems.default_backend_name
            WHERE projects.id = subquery_projects.id
        )
        WHERE ecosystem_name is null
    """
    )


def downgrade():
    # Do nothing on downgrade - column removal will be handled by previous
    # revision
    pass
