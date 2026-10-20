# -*- coding: utf-8 -*-
#
# Copyright © 2026 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""Pytest fixtures for Anitya tests."""

import os
import tempfile
import pytest
from sqlalchemy import event

from anitya import app, config
from anitya.db import db

user_id = os.getuid() if hasattr(os, "getuid") else "default"
worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")

_env_db_url = os.environ.get("ANITYA_TEST_DB_URL") or os.environ.get("DB_URL")
if _env_db_url:
    TEST_DB_URI = _env_db_url
    TEST_DB_PATH = None
else:
    temp_dir = tempfile.gettempdir()
    TEST_DB_PATH = os.path.join(temp_dir, f"anitya-test-{user_id}-{worker_id}.sqlite")
    TEST_DB_URI = f"sqlite:///{TEST_DB_PATH}"


def get_test_config(overrides=None):
    """Return application configuration dictionary configured for testing."""
    cfg = config.config.copy()
    cfg["TESTING"] = True
    cfg["DB_URL"] = TEST_DB_URI
    cfg["SQLALCHEMY_DATABASE_URI"] = TEST_DB_URI
    if overrides:
        cfg.update(overrides)
    return cfg


def cleanup_test_db():
    """Remove temporary SQLite test database file if it exists."""
    if TEST_DB_PATH and os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass


def configure_sqlite_engine(engine):
    """Configure SQLite engine with optimal PRAGMAs and transactional isolation."""
    if engine.name != "sqlite":
        return
    if getattr(engine, "_sqlite_configured", False):
        return
    engine._sqlite_configured = True

    @event.listens_for(engine, "connect")
    def connect_event(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA synchronous = OFF")
        cursor.execute("PRAGMA journal_mode = MEMORY")
        cursor.close()
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def begin_event(conn):
        conn.exec_driver_sql("BEGIN")


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    """Initialize database schema once per test session."""
    cleanup_test_db()

    flask_app = app.create(get_test_config())
    with flask_app.app_context():
        configure_sqlite_engine(db.manager.engine)
        db.manager.sync()

    yield

    try:
        with flask_app.app_context():
            db.manager.engine.dispose()
    except Exception:
        pass

    cleanup_test_db()
