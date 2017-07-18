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

import unittest
import os

from sqlalchemy import create_engine, event
import vcr
import mock

from anitya import app
from anitya.lib import model, utilities


engine = None


def _configure_db(db_uri='sqlite://'):
    """Creates and configures a database engine for the tests to use.

    Args:
        db_uri (str): The URI to use when creating the engine. This defaults
            to an in-memory SQLite database.
    """
    global engine
    engine = create_engine(db_uri)

    if db_uri.startswith('sqlite://'):
        # Necessary to get nested transactions working with SQLite. See:
        # http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html\
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
            conn.execute('BEGIN')

    @event.listens_for(model.Session, 'after_transaction_end')
    def restart_savepoint(session, transaction):
        """Allow tests to call rollback on the session."""
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            session.begin_nested()


class AnityaTestCase(unittest.TestCase):
    """This is the base test case class for Anitya tests."""

    def setUp(self):
        """Set a basic test environment.

        This simply starts recording a VCR on start-up and stops on tearDown.
        """
        cwd = os.path.dirname(os.path.realpath(__file__))
        my_vcr = vcr.VCR(
            cassette_library_dir=os.path.join(cwd, 'request-data/'), record_mode='once')
        self.vcr = my_vcr.use_cassette(self.id())
        self.vcr.__enter__()
        self.addCleanup(self.vcr.__exit__, None, None, None)


class DatabaseTestCase(AnityaTestCase):
    """The base class for tests that use the database.

    This pattern requires that the database support nested transactions.
    """

    def setUp(self):
        super(DatabaseTestCase, self).setUp()

        # We don't want our SQLAlchemy session thrown away post-request because that rolls
        # back the transaction and no database assertions can be made. This mocks out the
        # function that disposes of the session at the end of a request.
        mock_teardowns = mock.patch.object(app.APP, 'teardown_request_funcs', {})
        mock_teardowns.start()
        self.addCleanup(mock_teardowns.stop)

        if engine is None:
            # In the future we could provide a postgres URI to test against various
            # databases!
            _configure_db()

        self.connection = engine.connect()
        model.BASE.metadata.create_all(bind=self.connection)
        self.transaction = self.connection.begin()

        model.Session.remove()
        model.Session.configure(bind=self.connection, autoflush=False)
        self.session = model.Session()

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
        model.Session.remove()
        super(DatabaseTestCase, self).tearDown()


def create_distro(session):
    """ Create some basic distro for testing. """
    distro = model.Distro(
        name='Fedora',
    )
    session.add(distro)

    distro = model.Distro(
        name='Debian',
    )
    session.add(distro)

    session.commit()


def create_project(session):
    """ Create some basic projects to work with. """
    utilities.create_project(
        session,
        name='geany',
        homepage='http://www.geany.org/',
        version_url='http://www.geany.org/Download/Releases',
        regex='DEFAULT',
        user_id='noreply@fedoraproject.org',
    )

    utilities.create_project(
        session,
        name='subsurface',
        homepage='http://subsurface.hohndel.org/',
        version_url='http://subsurface.hohndel.org/downloads/',
        regex='DEFAULT',
        user_id='noreply@fedoraproject.org',
    )

    utilities.create_project(
        session,
        name='R2spec',
        homepage='https://fedorahosted.org/r2spec/',
        user_id='noreply@fedoraproject.org',
    )


def create_ecosystem_projects(session):
    """ Create some fake projects from particular upstream ecosystems

    Each project name is used in two different ecosystems
    """
    utilities.create_project(
        session,
        name='pypi_and_npm',
        homepage='https://example.com/not-a-real-pypi-project',
        backend='PyPI',
        user_id='noreply@fedoraproject.org'
    )

    utilities.create_project(
        session,
        name='pypi_and_npm',
        homepage='https://example.com/not-a-real-npmjs-project',
        backend='npmjs',
        user_id='noreply@fedoraproject.org'
    )

    utilities.create_project(
        session,
        name='rubygems_and_maven',
        homepage='https://example.com/not-a-real-rubygems-project',
        backend='Rubygems',
        user_id='noreply@fedoraproject.org'
    )

    utilities.create_project(
        session,
        name='rubygems_and_maven',
        homepage='https://example.com/not-a-real-maven-project',
        backend='Maven Central',
        user_id='noreply@fedoraproject.org'
    )


def create_package(session):
    """ Create some basic packages to work with. """
    package = model.Packages(
        project_id=1,
        distro='Fedora',
        package_name='geany',
    )
    session.add(package)

    package = model.Packages(
        project_id=2,
        distro='Fedora',
        package_name='subsurface',
    )
    session.add(package)

    session.commit()


def create_flagged_project(session):
    """ Create and flag a project. Returns the ProjectFlag. """
    project = utilities.create_project(
        session,
        name='geany',
        homepage='http://www.geany.org/',
        version_url='http://www.geany.org/Download/Releases',
        regex='DEFAULT',
        user_id='noreply@fedoraproject.org',
    )

    session.add(project)

    flag = utilities.flag_project(
        session,
        project,
        "This is a duplicate.",
        "dgay@redhat.com",
        "user_openid_id",
    )

    session.add(flag)

    session.commit()
    return flag


if __name__ == '__main__':
    unittest.main(verbosity=2)
