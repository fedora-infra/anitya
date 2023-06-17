# -*- coding: utf-8 -*-
"""Remove the backends and ecosystems tables

Revision ID: b9201d816075
Revises: 9c29da0af3af
Create Date: 2017-03-22 18:46:06.281100

"""

import sqlalchemy as sa
from alembic import op

from anitya.lib import plugins

# revision identifiers, used by Alembic.
revision = "b9201d816075"
down_revision = "9c29da0af3af"


def upgrade():
    """Drop the Backends and Ecosystems tables and remove foreign keys."""
    op.drop_constraint("projects_backend_fkey", "projects", type_="foreignkey")
    op.drop_constraint("FK_ECOSYSTEM_FOR_PROJECT", "projects", type_="foreignkey")
    op.create_index(
        op.f("ix_projects_ecosystem_name"), "projects", ["ecosystem_name"], unique=False
    )
    op.drop_table("ecosystems")
    op.drop_table("backends")


def downgrade():
    """Restore the Backends and Ecosystems tables."""
    op.drop_index(op.f("ix_projects_ecosystem_name"), table_name="projects")
    op.create_table(
        "backends",
        sa.Column("name", sa.VARCHAR(length=200), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("name", name="backends_pkey"),
        postgresql_ignore_search_path=False,
    )
    # We have to populate the backends table before we can add the ecosystems
    # table with its foreign key constraint.
    for backend in plugins.BACKEND_PLUGINS.get_plugins():
        op.execute(f"INSERT INTO backends (name) VALUES ('{backend.name}');")

    op.create_table(
        "ecosystems",
        sa.Column("name", sa.VARCHAR(length=200), autoincrement=False, nullable=False),
        sa.Column(
            "default_backend_name",
            sa.VARCHAR(length=200),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["default_backend_name"],
            ["backends.name"],
            name="ecosystems_default_backend_name_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("name", name="ecosystems_pkey"),
        sa.UniqueConstraint(
            "default_backend_name", name="ecosystems_default_backend_name_key"
        ),
    )
    for ecosystem in plugins.ECOSYSTEM_PLUGINS.get_plugins():
        op.execute(
            f"""
            INSERT INTO ecosystems (name, default_backend_name)
            VALUES ('{ecosystem.name}', '{ecosystem.default_backend}');"""
        )

    op.create_foreign_key(
        "FK_ECOSYSTEM_FOR_PROJECT",
        "projects",
        "ecosystems",
        ["ecosystem_name"],
        ["name"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "projects_backend_fkey",
        "projects",
        "backends",
        ["backend"],
        ["name"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
