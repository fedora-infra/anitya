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
anitya tests of the models.
'''

from uuid import uuid4, UUID
import datetime
import unittest

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.types import CHAR
from sqlalchemy.exc import IntegrityError
from social_flask_sqlalchemy import models as social_models
import six

from anitya.db import models
from anitya.lib import versions
from anitya.tests.base import (
    DatabaseTestCase, create_distro,
    create_project, create_package,
    create_flagged_project)


class ProjectTests(DatabaseTestCase):
    """Tests for the Project models."""

    def test_init_project(self):
        """ Test the __init__ function of Project. """
        create_project(self.session)
        self.assertEqual(3, models.Project.all(self.session, count=True))

        projects = models.Project.all(self.session)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[2].name, 'subsurface')

    def test_validate_backend(self):
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(models.Project).count())
        self.assertEqual('custom', self.session.query(models.Project).one().backend)

    def test_validate_backend_bad(self):
        self.assertRaises(
            ValueError,
            models.Project,
            name='test',
            homepage='https://example.com',
            backend='Nope',
        )

    def test_default_ecosystem_is_homepage(self):
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name=None,
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(models.Project).count())
        self.assertEqual(
            'https://example.com',
            self.session.query(models.Project).one().ecosystem_name)

    def test_validate_ecosystem_good(self):
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name='pypi',
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(models.Project).count())
        self.assertEqual('pypi', self.session.query(models.Project).one().ecosystem_name)

    def test_ecosystem_in_json(self):
        """Assert the ecosystem is included in the dict returned from ``__json__``"""
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name='pypi',
        )
        self.assertEqual('pypi', project.__json__()['ecosystem'])

    def get_sorted_version_objects(self):
        """ Assert that sorted versions are included in the list returned from
        :data:`Project.get_sorted_version_objects`.
        """
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name='pypi',
            version_scheme='Date'
        )
        version_first = models.ProjectVersion(
            project_id=project.id,
            version='1.0',
        )
        version_second = models.ProjectVersion(
            project_id=project.id,
            version='0.8',
        )
        self.session.add(project)
        self.session.add(version_first)
        self.session.add(version_second)
        self.session.commit()

        versions = project.get_sorted_version_objects()

        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version, version_second.version)
        self.assertEqual(versions[1].version, version_first.version)

    def test_get_version_class(self):
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name='pypi',
            version_scheme='RPM',
        )
        version_class = project.get_version_class()
        self.assertEqual(version_class, versions.RpmVersion)

    def test_get_version_class_missing(self):
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name='pypi',
            version_scheme='Invalid',
        )
        version_class = project.get_version_class()
        self.assertEqual(version_class, None)

    def test_project_all(self):
        """ Test the Project.all function. """
        create_project(self.session)

        projects = models.Project.all(self.session, count=True)
        self.assertEqual(projects, 3)

        projects = models.Project.all(self.session, page=2)
        self.assertEqual(len(projects), 0)

        projects = models.Project.all(self.session, page='asd')
        self.assertEqual(len(projects), 3)

    def test_project_search(self):
        """ Test the Project.search function. """
        create_project(self.session)

        projects = models.Project.search(self.session, '*', count=True)
        self.assertEqual(projects, 3)

        projects = models.Project.search(self.session, '*', page=2)
        self.assertEqual(len(projects), 0)

        projects = models.Project.search(self.session, '*', page='asd')
        self.assertEqual(len(projects), 3)

    def test_project_get_or_create(self):
        """ Test the Project.get_or_create function. """
        project = models.Project.get_or_create(
            self.session,
            name='test',
            homepage='https://test.org',
            backend='custom')
        self.assertEqual(project.name, 'test')
        self.assertEqual(project.homepage, 'https://test.org')
        self.assertEqual(project.backend, 'custom')

        self.assertRaises(
            ValueError,
            models.Project.get_or_create,
            self.session,
            name='test_project',
            homepage='https://project.test.org',
            backend='foobar'
        )

    def test_project_delete_cascade(self):
        """ Assert deletion of mapped packages when project is deleted """
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name='pypi',
            version_scheme='Invalid',
        )
        self.session.add(project)

        package = models.Packages(
            project_id=1,
            distro_name='Fedora',
            package_name='test',
        )
        self.session.add(package)
        self.session.commit()

        projects = self.session.query(models.Project).all()
        self.assertEqual(len(projects), 1)
        self.assertEqual(len(projects[0].package), 1)

        self.session.delete(projects[0])
        self.session.commit()

        projects = self.session.query(models.Project).all()
        packages = self.session.query(models.Packages).all()
        self.assertEqual(len(projects), 0)
        self.assertEqual(len(packages), 0)

        create_flagged_project(self.session)
        projects = self.session.query(models.Project).all()
        self.assertEqual(len(projects), 1)
        self.assertEqual(len(projects[0].flags), 1)

        self.session.delete(projects[0])
        self.session.commit()

        projects = self.session.query(models.Project).all()
        packages = self.session.query(models.ProjectFlag).all()
        self.assertEqual(len(projects), 0)
        self.assertEqual(len(packages), 0)


class DatabaseTestCase(DatabaseTestCase):
    """ Model tests. """

    def test_init_distro(self):
        """ Test the __init__ function of Distro. """
        create_distro(self.session)
        self.assertEqual(2, models.Distro.all(self.session, count=True))

        distros = models.Distro.all(self.session)
        self.assertEqual(distros[0].name, 'Debian')
        self.assertEqual(distros[1].name, 'Fedora')

    def test_distro_delete_cascade(self):
        """ Assert deletion of mapped packages when project is deleted """
        project = models.Project(
            name='test',
            homepage='https://example.com',
            backend='custom',
            ecosystem_name='pypi',
            version_scheme='Invalid',
        )
        self.session.add(project)

        distro = models.Distro(
            name='Fedora',
        )
        self.session.add(distro)

        package = models.Packages(
            project_id=1,
            distro_name='Fedora',
            package_name='test',
        )
        self.session.add(package)
        self.session.commit()

        distros = self.session.query(models.Distro).all()

        self.assertEqual(len(distros), 1)
        self.assertEqual(len(distros[0].package), 1)

        self.session.delete(distros[0])
        self.session.commit()

        distros = self.session.query(models.Distro).all()
        packages = self.session.query(models.Packages).all()

        self.assertEqual(len(distros), 0)
        self.assertEqual(len(packages), 0)

    def test_log_search(self):
        """ Test the Log.search function. """
        create_project(self.session)

        logs = models.Log.search(self.session)
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

        logs = models.Log.search(self.session, count=True)
        self.assertEqual(logs, 3)

        from_date = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
        logs = models.Log.search(
            self.session, from_date=from_date, offset=1, limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

        logs = models.Log.search(self.session, project_name='subsurface')
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

    def test_distro_search(self):
        """ Test the Distro.search function. """
        create_distro(self.session)

        logs = models.Distro.search(self.session, '*', count=True)
        self.assertEqual(logs, 2)

        logs = models.Distro.search(self.session, 'Fed*')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = models.Distro.search(self.session, 'Fed*', page=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = models.Distro.search(self.session, 'Fed*', page='as')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

    def test_packages_by_id(self):
        """ Test the Packages.by_id function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = models.Packages.by_id(self.session, 1)
        self.assertEqual(pkg.package_name, 'geany')
        self.assertEqual(pkg.distro_name, 'Fedora')

    def test_packages__repr__(self):
        """ Test the Packages.__repr__ function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = models.Packages.by_id(self.session, 1)
        self.assertEqual(str(pkg), '<Packages(1, Fedora: geany)>')


class GuidTests(unittest.TestCase):
    """Tests for the :class:`anitya.db.models.GUID` class."""

    def test_load_dialect_impl_postgres(self):
        """Assert with PostgreSQL, a UUID type is used."""
        guid = models.GUID()
        dialect = postgresql.dialect()

        result = guid.load_dialect_impl(dialect)

        self.assertTrue(isinstance(result, postgresql.UUID))

    def test_load_dialect_impl_other(self):
        """Assert with dialects other than PostgreSQL, a CHAR type is used."""
        guid = models.GUID()
        dialect = sqlite.dialect()

        result = guid.load_dialect_impl(dialect)

        self.assertTrue(isinstance(result, CHAR))

    def test_process_bind_param_uuid_postgres(self):
        """Assert UUIDs with PostgreSQL are normal string representations of UUIDs."""
        guid = models.GUID()
        uuid = uuid4()
        dialect = postgresql.dialect()

        result = guid.process_bind_param(uuid, dialect)

        self.assertEqual(str(uuid), result)

    def test_process_bind_param_uuid_other(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = models.GUID()
        uuid = uuid4()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(uuid, dialect)

        self.assertEqual(32, len(result))
        self.assertEqual(str(uuid).replace('-', ''), result)

    def test_process_bind_param_str_other(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = models.GUID()
        uuid = uuid4()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(str(uuid), dialect)

        self.assertEqual(32, len(result))
        self.assertEqual(str(uuid).replace('-', ''), result)

    def test_process_bind_param_none(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = models.GUID()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(None, dialect)

        self.assertTrue(result is None)

    def test_process_result_value_none(self):
        """Assert when the result value is None, None is returned."""
        guid = models.GUID()

        self.assertTrue(guid.process_result_value(None, sqlite.dialect()) is None)

    def test_process_result_string(self):
        """Assert when the result value is a string, a native UUID is returned."""
        guid = models.GUID()
        uuid = uuid4()

        result = guid.process_result_value(str(uuid), sqlite.dialect())

        self.assertTrue(isinstance(result, UUID))
        self.assertEqual(uuid, result)

    def test_process_result_short_string(self):
        """Assert when the result value is a short string, a native UUID is returned."""
        guid = models.GUID()
        uuid = uuid4()

        result = guid.process_result_value(str(uuid).replace('-', ''), sqlite.dialect())

        self.assertTrue(isinstance(result, UUID))
        self.assertEqual(uuid, result)


class UserTests(DatabaseTestCase):

    def test_user_id(self):
        """Assert Users have a UUID id assigned to them."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertTrue(isinstance(user.id, UUID))

    def test_user_get_id(self):
        """Assert Users implements the Flask-Login API for getting user IDs."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertEqual(six.text_type(user.id), user.get_id())

    def test_user_email_unique(self):
        """Assert User emails have a uniqueness constraint on them."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        user = models.User(email='user@fedoraproject.org', username='user2')
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )
        self.session.add(user)
        self.session.add(user_social_auth)
        self.assertRaises(IntegrityError, self.session.commit)

    def test_username_unique(self):
        """Assert User usernames have a uniqueness constraint on them."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        user = models.User(email='user2@fedoraproject.org', username='user')
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )
        self.session.add(user)
        self.session.add(user_social_auth)
        self.assertRaises(IntegrityError, self.session.commit)

    def test_default_active(self):
        """Assert User usernames have a uniqueness constraint on them."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertTrue(user.active)
        self.assertTrue(user.is_active)

    def test_not_anonymous(self):
        """Assert User implements the Flask-Login API for authenticated users."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertFalse(user.is_anonymous)
        self.assertTrue(user.is_authenticated)


class ApiTokenTests(DatabaseTestCase):

    def test_token_default(self):
        """Assert creating an ApiToken generates a random token."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)

        token = models.ApiToken(user=user)
        self.session.add(token)
        self.session.commit()

        self.assertEqual(40, len(token.token))

    def test_user_relationship(self):
        """Assert users have a reference to their tokens."""
        user = models.User(
            email='user@fedoraproject.org',
            username='user',
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id,
            user=user
        )

        self.session.add(user)
        self.session.add(user_social_auth)

        token = models.ApiToken(user=user)
        self.session.add(token)
        self.session.commit()

        self.assertEqual(user.api_tokens, [token])


if __name__ == '__main__':
    unittest.main(verbosity=2)
