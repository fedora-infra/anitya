# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
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
#

'''
anitya tests of the model.
'''

from uuid import uuid4, UUID
import datetime
import unittest

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.types import CHAR
from sqlalchemy.exc import IntegrityError
import mock
import six

import anitya.lib.model as model
from anitya.lib import versions
from anitya.tests.base import DatabaseTestCase, create_distro, create_project, create_package


class InitalizeTests(unittest.TestCase):

    @mock.patch('anitya.lib.model.sa.create_engine')
    @mock.patch('anitya.lib.model.Session')
    def test_initialize(self, mock_session, mock_create_engine):
        config = {'DB_URL': 'postgresql://postgres:pass@localhost/mydb'}
        engine = model.initialize(config)
        mock_create_engine.assert_called_once_with(config['DB_URL'], echo=False)
        self.assertEqual(engine, mock_create_engine.return_value)
        mock_session.configure.assert_called_once_with(bind=engine)

    @mock.patch('anitya.lib.model.sa.create_engine')
    @mock.patch('anitya.lib.model.sa.event.listen')
    @mock.patch('anitya.lib.model.Session')
    def test_initalize_sqlite(self, mock_session, mock_listen, mock_create_engine):
        config = {'DB_URL': 'sqlite://', 'SQL_DEBUG': True}
        engine = model.initialize(config)
        mock_create_engine.assert_called_once_with(config['DB_URL'], echo=True)
        mock_session.configure.assert_called_once_with(bind=engine)
        self.assertEqual(1, mock_listen.call_count)
        self.assertEqual(engine, mock_listen.call_args_list[0][0][0])
        self.assertEqual('connect', mock_listen.call_args_list[0][0][1])


class BaseQueryPaginateTests(DatabaseTestCase):
    """Tests for the BaseQuery queries."""

    def setUp(self):
        super(BaseQueryPaginateTests, self).setUp()
        self.query = model.BaseQuery(model.Project, session=self.session)

    def test_defaults(self):
        """Assert paginate defaults to the first page and 25 items."""
        create_project(self.session)
        page = self.query.paginate()
        self.assertEqual(1, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(25, page.items_per_page)
        # Default ordering is just by id
        self.assertEqual(page.items[0].name, 'geany')
        self.assertEqual(page.items[1].name, 'subsurface')
        self.assertEqual(page.items[2].name, 'R2spec')

    def test_multiple_pages(self):
        """Assert multiple pages work with pagination."""
        create_project(self.session)
        page = self.query.paginate(items_per_page=2)
        page2 = self.query.paginate(page=2, items_per_page=2)
        self.assertEqual(1, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(2, page.items_per_page)
        self.assertEqual(page.items[0].name, 'geany')
        self.assertEqual(page.items[1].name, 'subsurface')

        self.assertEqual(2, page2.page)
        self.assertEqual(3, page2.total_items)
        self.assertEqual(2, page2.items_per_page)
        self.assertEqual(page2.items[0].name, 'R2spec')

    def test_no_results(self):
        """Assert an empty page is returned when page * items_per_page > total_items."""
        create_project(self.session)
        page = self.query.paginate(page=1000)
        self.assertEqual(1000, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(25, page.items_per_page)
        self.assertEqual(0, len(page.items))

    def test_nonsense_page(self):
        """Assert a page number less than 1 raises a ValueError."""
        self.assertRaises(ValueError, self.query.paginate, 0)
        self.assertRaises(ValueError, self.query.paginate, -1)

    def test_nonsense_items_per_page(self):
        """Assert an items_per_page number less than 1 raises a ValueError."""
        self.assertRaises(ValueError, self.query.paginate, 1, 0)
        self.assertRaises(ValueError, self.query.paginate, 1, -1)

    def test_order_by(self):
        """Assert you can alter the order of page results."""
        create_project(self.session)
        page = self.query.paginate(order_by=model.Project.name)
        self.assertEqual(1, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(25, page.items_per_page)
        self.assertEqual(page.items[0].name, 'R2spec')
        self.assertEqual(page.items[1].name, 'geany')
        self.assertEqual(page.items[2].name, 'subsurface')

    def test_as_dict(self):
        expected_dict = {
            u'items_per_page': 1,
            u'page': 1,
            u'total_items': 3,
            u'items': [{
                'id': 3,
                'backend': u'custom',
                'name': u'R2spec',
                'homepage': u'https://fedorahosted.org/r2spec/',
                'regex': None,
                'version': None,
                'version_url': None,
                'versions': [],
            }],
        }
        create_project(self.session)
        page = self.query.paginate(order_by=model.Project.name, items_per_page=1)
        actual_dict = page.as_dict()
        actual_dict['items'][0].pop('updated_on')
        actual_dict['items'][0].pop('created_on')
        self.assertEqual(expected_dict, actual_dict)


class ProjectTests(DatabaseTestCase):
    """Tests for the Project model."""

    def test_init_project(self):
        """ Test the __init__ function of Project. """
        create_project(self.session)
        self.assertEqual(3, model.Project.all(self.session, count=True))

        projects = model.Project.all(self.session)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[2].name, 'subsurface')

    def test_validate_backend(self):
        project = model.Project(
            name='test',
            homepage='http://example.com',
            backend='custom',
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(model.Project).count())
        self.assertEqual('custom', self.session.query(model.Project).one().backend)

    def test_validate_backend_bad(self):
        self.assertRaises(
            ValueError,
            model.Project,
            name='test',
            homepage='http://example.com',
            backend='Nope',
        )

    def test_validate_ecosystem_none(self):
        project = model.Project(
            name='test',
            homepage='http://example.com',
            backend='custom',
            ecosystem_name=None,
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(model.Project).count())
        self.assertEqual(None, self.session.query(model.Project).one().ecosystem_name)

    def test_validate_ecosystem_good(self):
        project = model.Project(
            name='test',
            homepage='http://example.com',
            backend='custom',
            ecosystem_name='pypi',
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(model.Project).count())
        self.assertEqual('pypi', self.session.query(model.Project).one().ecosystem_name)

    def test_validate_ecosystem_bad(self):
        self.assertRaises(
            ValueError,
            model.Project,
            name='test',
            homepage='http://example.com',
            backend='custom',
            ecosystem_name='Nope',
        )

    def test_get_version_class(self):
        project = model.Project(
            name='test',
            homepage='http://example.com',
            backend='custom',
            ecosystem_name='pypi',
            version_scheme='RPM',
        )
        version_class = project.get_version_class()
        self.assertEqual(version_class, versions.RpmVersion)

    def test_get_version_class_missing(self):
        project = model.Project(
            name='test',
            homepage='http://example.com',
            backend='custom',
            ecosystem_name='pypi',
            version_scheme='Invalid',
        )
        version_class = project.get_version_class()
        self.assertEqual(version_class, None)

    def test_project_all(self):
        """ Test the Project.all function. """
        create_project(self.session)

        projects = model.Project.all(self.session, count=True)
        self.assertEqual(projects, 3)

        projects = model.Project.all(self.session, page=2)
        self.assertEqual(len(projects), 0)

        projects = model.Project.all(self.session, page='asd')
        self.assertEqual(len(projects), 3)

    def test_project_search(self):
        """ Test the Project.search function. """
        create_project(self.session)

        projects = model.Project.search(self.session, '*', count=True)
        self.assertEqual(projects, 3)

        projects = model.Project.search(self.session, '*', page=2)
        self.assertEqual(len(projects), 0)

        projects = model.Project.search(self.session, '*', page='asd')
        self.assertEqual(len(projects), 3)

    def test_project_get_or_create(self):
        """ Test the Project.get_or_create function. """
        project = model.Project.get_or_create(
            self.session,
            name='test',
            homepage='http://test.org',
            backend='custom')
        self.assertEqual(project.name, 'test')
        self.assertEqual(project.homepage, 'http://test.org')
        self.assertEqual(project.backend, 'custom')

        self.assertRaises(
            ValueError,
            model.Project.get_or_create,
            self.session,
            name='test_project',
            homepage='http://project.test.org',
            backend='foobar'
        )


class DatabaseTestCase(DatabaseTestCase):
    """ Model tests. """

    def test_init_distro(self):
        """ Test the __init__ function of Distro. """
        create_distro(self.session)
        self.assertEqual(2, model.Distro.all(self.session, count=True))

        distros = model.Distro.all(self.session)
        self.assertEqual(distros[0].name, 'Debian')
        self.assertEqual(distros[1].name, 'Fedora')

    def test_log_search(self):
        """ Test the Log.search function. """
        create_project(self.session)

        logs = model.Log.search(self.session)
        self.assertEqual(len(logs), 3)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: R2spec')
        self.assertEqual(
            logs[1].description,
            'noreply@fedoraproject.org added project: subsurface')
        self.assertEqual(
            logs[2].description,
            'noreply@fedoraproject.org added project: geany')

        logs = model.Log.search(self.session, count=True)
        self.assertEqual(logs, 3)

        from_date = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
        logs = model.Log.search(
            self.session, from_date=from_date, offset=1, limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

        logs = model.Log.search(self.session, project_name='subsurface')
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

    def test_distro_search(self):
        """ Test the Distro.search function. """
        create_distro(self.session)

        logs = model.Distro.search(self.session, '*', count=True)
        self.assertEqual(logs, 2)

        logs = model.Distro.search(self.session, 'Fed*')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = model.Distro.search(self.session, 'Fed*', page=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = model.Distro.search(self.session, 'Fed*', page='as')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

    def test_packages_by_id(self):
        """ Test the Packages.by_id function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = model.Packages.by_id(self.session, 1)
        self.assertEqual(pkg.package_name, 'geany')
        self.assertEqual(pkg.distro, 'Fedora')

    def test_packages__repr__(self):
        """ Test the Packages.__repr__ function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = model.Packages.by_id(self.session, 1)
        self.assertEqual(str(pkg), '<Packages(1, Fedora: geany)>')


class GuidTests(unittest.TestCase):
    """Tests for the :class:`anitya.lib.model.GUID` class."""

    def test_load_dialect_impl_postgres(self):
        """Assert with PostgreSQL, a UUID type is used."""
        guid = model.GUID()
        dialect = postgresql.dialect()

        result = guid.load_dialect_impl(dialect)

        self.assertTrue(isinstance(result, postgresql.UUID))

    def test_load_dialect_impl_other(self):
        """Assert with dialects other than PostgreSQL, a CHAR type is used."""
        guid = model.GUID()
        dialect = sqlite.dialect()

        result = guid.load_dialect_impl(dialect)

        self.assertTrue(isinstance(result, CHAR))

    def test_process_bind_param_uuid_postgres(self):
        """Assert UUIDs with PostgreSQL are normal string representations of UUIDs."""
        guid = model.GUID()
        uuid = uuid4()
        dialect = postgresql.dialect()

        result = guid.process_bind_param(uuid, dialect)

        self.assertEqual(str(uuid), result)

    def test_process_bind_param_uuid_other(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = model.GUID()
        uuid = uuid4()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(uuid, dialect)

        self.assertEqual(32, len(result))
        self.assertEqual(str(uuid).replace('-', ''), result)

    def test_process_bind_param_str_other(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = model.GUID()
        uuid = uuid4()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(str(uuid), dialect)

        self.assertEqual(32, len(result))
        self.assertEqual(str(uuid).replace('-', ''), result)

    def test_process_bind_param_none(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = model.GUID()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(None, dialect)

        self.assertTrue(result is None)

    def test_process_result_value_none(self):
        """Assert when the result value is None, None is returned."""
        guid = model.GUID()

        self.assertTrue(guid.process_result_value(None, sqlite.dialect()) is None)

    def test_process_result_string(self):
        """Assert when the result value is a string, a native UUID is returned."""
        guid = model.GUID()
        uuid = uuid4()

        result = guid.process_result_value(str(uuid), sqlite.dialect())

        self.assertTrue(isinstance(result, UUID))
        self.assertEqual(uuid, result)

    def test_process_result_short_string(self):
        """Assert when the result value is a short string, a native UUID is returned."""
        guid = model.GUID()
        uuid = uuid4()

        result = guid.process_result_value(str(uuid).replace('-', ''), sqlite.dialect())

        self.assertTrue(isinstance(result, UUID))
        self.assertEqual(uuid, result)


class UserTests(DatabaseTestCase):

    def test_user_id(self):
        """Assert Users have a UUID id assigned to them."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        session.add(user)
        session.commit()

        self.assertTrue(isinstance(user.id, UUID))

    def test_user_get_id(self):
        """Assert Users implements the Flask-Login API for getting user IDs."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        session.add(user)
        session.commit()

        self.assertEqual(six.text_type(user.id), user.get_id())

    def test_user_email_unique(self):
        """Assert User emails have a uniqueness constraint on them."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        session.add(user)
        session.commit()

        user2 = model.User(email='user@example.com', username='user2')
        session.add(user2)
        self.assertRaises(IntegrityError, session.commit)

    def test_username_unique(self):
        """Assert User usernames have a uniqueness constraint on them."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        session.add(user)
        session.commit()

        user2 = model.User(email='user2@example.com', username='user')
        session.add(user2)
        self.assertRaises(IntegrityError, session.commit)

    def test_default_active(self):
        """Assert User usernames have a uniqueness constraint on them."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        session.add(user)
        session.commit()

        self.assertTrue(user.active)
        self.assertTrue(user.is_active)

    def test_not_anonymous(self):
        """Assert User implements the Flask-Login API for authenticated users."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        session.add(user)
        session.commit()

        self.assertFalse(user.is_anonymous)
        self.assertTrue(user.is_authenticated)


class ApiTokenTests(DatabaseTestCase):

    def test_token_default(self):
        """Assert creating an ApiToken generates a random token."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        token = model.ApiToken(user=user)
        session.add(token)
        session.commit()

        self.assertEqual(40, len(token.token))

    def test_user_relationship(self):
        """Assert users have a reference to their tokens."""
        session = model.Session()
        user = model.User(email='user@example.com', username='user')
        token = model.ApiToken(user=user)
        session.add(token)
        session.commit()

        self.assertEqual(user.api_tokens, [token])


if __name__ == '__main__':
    unittest.main(verbosity=2)
