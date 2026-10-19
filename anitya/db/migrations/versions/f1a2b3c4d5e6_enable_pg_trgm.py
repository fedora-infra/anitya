"""Enable PostgreSQL trigram extension for fuzzy project search."""

from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "ebc827e80373"
branch_labels = None
depends_on = None


def upgrade():
    """Enable pg_trgm and create the project name trigram index."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_projects_name_trgm "
            "ON projects USING gist (name gist_trgm_ops)"
        )


def downgrade():
    """Drop the project name index and disable pg_trgm."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_projects_name_trgm")
        op.execute("DROP EXTENSION IF EXISTS pg_trgm")
