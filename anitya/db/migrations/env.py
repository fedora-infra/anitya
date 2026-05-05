"""env"""

from __future__ import with_statement

import sys
from os.path import dirname

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy_helpers import Base
from sqlalchemy_helpers.flask_ext import get_url_from_app

from anitya.app import create

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# Don't check this with mypy, it doesn't work well with
# proxy class
config = context.config  # type: ignore

# Get URL for the app
url = get_url_from_app(create)
config.set_main_option("sqlalchemy.url", url)

# add your model's MetaData object here
# for 'autogenerate' support
sys.path.append(dirname(dirname(__file__)))
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(url=url, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    connection = engine.connect()
    context.configure(connection=connection, target_metadata=target_metadata)

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
