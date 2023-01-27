# -*- coding: utf-8 -*-
#
# Copyright © 2014-2017  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
"""
Base class for Anitya tests.
"""
from __future__ import print_function

import os
import unittest
from contextlib import contextmanager

import flask_login
import vcr
from flask import request_started
from social_flask_sqlalchemy.models import PSABase
from sqlalchemy import create_engine, event

from anitya import app, config
from anitya.db import Base, Session, models

engine = None


@contextmanager
def login_user(app, user):
    """
    A context manager to log a user in for testing purposes.

    For example:

        >>> with login_user(self.flask_app, user):
        ...     self.flask_app.test_client().get('/protected/view')

    The above example will cause the request to ``/protected/view`` to occur with the
    provided user being authenticated.

    Args:
        app (flask.Flask): An instance of the Flask application.
        user (models.User): The user to log in. Note that this user must be committed to the
            database as it needs a ``user.id`` value.
    """

    def handler(sender, **kwargs):
        flask_login.login_user(user)

    with request_started.connected_to(handler, app):
        yield


def _configure_db(db_uri="sqlite://"):
    """Creates and configures a database engine for the tests to use.

    Args:
        db_uri (str): The URI to use when creating the engine. This defaults
            to an in-memory SQLite database.
    """
    global engine  # pylint: disable=W0603
    engine = create_engine(db_uri)

    if db_uri.startswith("sqlite://"):
        # Necessary to get nested transactions working with SQLite. See:
        # https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html\
        # #serializable-isolation-savepoints-transactional-ddl
        @event.listens_for(engine, "connect")
        def connect_event(dbapi_connection, connection_record):
            """Stop pysqlite from emitting 'BEGIN'"""
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None

        @event.listens_for(engine, "begin")
        def begin_event(conn):
            """Emit our own 'BEGIN' instead of letting pysqlite do it."""
            conn.exec_driver_sql("BEGIN")

    @event.listens_for(Session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        """Allow tests to call rollback on the session."""
        if (
            transaction.nested
            and not transaction._parent.nested  # pylint: disable=W0212
        ):
            session.expire_all()
            session.begin_nested()


class AnityaTestCase(unittest.TestCase):
    """This is the base test case class for Anitya tests."""

    def setUp(self):
        """Set a basic test environment.

        This simply starts recording a VCR on start-up and stops on tearDown.
        """
        self.config = config.config.copy()
        self.config["TESTING"] = True
        self.flask_app = app.create(self.config)

        cwd = os.path.dirname(os.path.realpath(__file__))
        my_vcr = vcr.VCR(
            cassette_library_dir=os.path.join(cwd, "request-data/"),
            record_mode="once",
            decode_compressed_response=True,
        )
        self.vcr = my_vcr.use_cassette(
            self.id(), filter_headers=[("Authorization", "bearer foobar")]
        )
        self.vcr.__enter__()
        self.addCleanup(self.vcr.__exit__, None, None, None)


class DatabaseTestCase(AnityaTestCase):
    """The base class for tests that use the database.

    This pattern requires that the database support nested transactions.
    """

    def setUp(self):
        super().setUp()

        # We don't want our SQLAlchemy session thrown away post-request because that rolls
        # back the transaction and no database assertions can be made.
        self.flask_app.teardown_request_funcs = {None: []}

        if engine is None:
            # In the future we could provide a postgres URI to test against various
            # databases!
            _configure_db()

        self.connection = engine.connect()
        Base.metadata.create_all(bind=self.connection)
        PSABase.metadata.create_all(bind=self.connection)
        self.transaction = self.connection.begin_nested()

        Session.remove()
        Session.configure(bind=self.connection, autoflush=False)
        self.session = Session()

        # Start a transaction after creating the schema, but before anything is
        # placed into the database. We'll roll back to the start of this
        # transaction at the end of every test, and code under test will start
        # nested transactions
        self.session.begin_nested()

    def tearDown(self):
        """Roll back all the changes from the test and clean up the session."""
        self.session.close()
        self.transaction.rollback()
        self.connection.close()
        Session.remove()
        super().tearDown()


def create_distro(session):
    """Create some basic distro for testing."""
    distro = models.Distro(name="Fedora")
    session.add(distro)

    distro = models.Distro(name="Debian")
    session.add(distro)

    session.commit()


def create_project(session):
    """Create some basic projects to work with."""
    project = models.Project(
        name="geany",
        homepage="https://www.geany.org/",
        version_scheme="RPM",
        backend="custom",
        version_url="https://www.geany.org/Download/Releases",
        regex="DEFAULT",
    )
    session.add(project)

    project = models.Project(
        name="subsurface",
        homepage="https://subsurface-divelog.org/",
        backend="custom",
        version_url="https://subsurface-divelog.org/downloads/",
        regex="DEFAULT",
    )
    session.add(project)

    project = models.Project(
        name="R2spec", homepage="https://fedorahosted.org/r2spec/", backend="custom"
    )
    session.add(project)
    session.commit()


def create_ecosystem_projects(session):
    """Create some fake projects from particular upstream ecosystems

    Each project name is used in two different ecosystems
    """
    project = models.Project(
        name="pypi_and_npm",
        homepage="https://example.com/not-a-real-pypi-project",
        backend="PyPI",
    )
    session.add(project)

    project = models.Project(
        name="pypi_and_npm",
        homepage="https://example.com/not-a-real-npmjs-project",
        backend="npmjs",
    )
    session.add(project)

    project = models.Project(
        name="rubygems_and_maven",
        homepage="https://example.com/not-a-real-rubygems-project",
        backend="Rubygems",
    )
    session.add(project)

    project = models.Project(
        name="rubygems_and_maven",
        homepage="https://example.com/not-a-real-maven-project",
        backend="Maven Central",
    )
    session.add(project)
    session.commit()


def create_package(session):
    """Create some basic packages to work with."""
    package = models.Packages(project_id=1, distro_name="Fedora", package_name="geany")
    session.add(package)

    package = models.Packages(
        project_id=2, distro_name="Fedora", package_name="subsurface"
    )
    session.add(package)

    session.commit()


def create_flagged_project(session):
    """Create and flag a project. Returns the ProjectFlag."""
    project = models.Project(
        name="geany",
        homepage="https://www.geany.org/",
        version_url="https://www.geany.org/Download/Releases",
        regex="DEFAULT",
    )
    session.add(project)

    flag = models.ProjectFlag(
        project=project, reason="this is a duplicate.", user="dgay@redhat.com"
    )
    session.add(flag)

    session.commit()
    return flag


if __name__ == "__main__":
    unittest.main(verbosity=2)
