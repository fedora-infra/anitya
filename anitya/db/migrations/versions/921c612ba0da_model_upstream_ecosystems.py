"""Model upstream ecosystems

Revision ID: 921c612ba0da
Revises: 2925648d8cc3
Create Date: 2016-08-09 18:44:53.119461

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "921c612ba0da"
down_revision = "2925648d8cc3"


def upgrade():
    op.add_column(
        "projects", sa.Column("ecosystem_name", sa.String(length=200), nullable=True)
    )
    op.create_unique_constraint(
        "UNIQ_PROJECT_NAME_PER_ECOSYSTEM", "projects", ["name", "ecosystem_name"]
    )
    op.create_foreign_key(
        "FK_ECOSYSTEM_FOR_PROJECT",
        "projects",
        "ecosystems",
        ["ecosystem_name"],
        ["name"],
        onupdate="cascade",
        ondelete="set null",
    )


def downgrade():
    op.drop_constraint("FK_ECOSYSTEM_FOR_PROJECT", "projects", type_="foreignkey")
    op.drop_constraint("UNIQ_PROJECT_NAME_PER_ECOSYSTEM", "projects", type_="unique")
    op.drop_column("projects", "ecosystem_name")
