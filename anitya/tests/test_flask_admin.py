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
"""Tests for the :mod:`anitya.admin` module."""

import mock
import six

from anitya import admin
from anitya.db import models, Session
from anitya.tests.base import DatabaseTestCase, login_user


class IsAdminTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.is_admin` function."""

    def setUp(self):
        super(IsAdminTests, self).setUp()

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')
        session.add_all([self.user, self.admin])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

    def test_admin_user(self):
        """Assert admin users passed via parameter returns True."""
        self.assertTrue(admin.is_admin(self.admin))

    def test_non_admin_user(self):
        """Assert regular users passed via parameter returns False."""
        self.assertFalse(admin.is_admin(self.user))


class AddDistroTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.add_distro` view function."""

    def setUp(self):
        super(AddDistroTests, self).setUp()

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')
        session.add_all([self.user, self.admin])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot add a distribution."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/distro/add')
            self.assertEqual(401, output.status_code)

    def test_no_csrf_token(self):
        """Assert submitting without a CSRF token, no change is made."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/distro/add', data={'name': 'Fedora'})
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.count())

    def test_invalid_csrf_token(self):
        """Assert submitting with an invalid CSRF token, no change is made."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/distro/add', data={'csrf_token': 'abc', 'name': 'Fedora'})
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.count())

    def test_admin_get(self):
        """Assert admin users can view the add a distribution page."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/add')
            self.assertEqual(200, output.status_code)

    def test_add_distro(self):
        """Assert admins can add distributions."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/add')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'name': 'Fedora', 'csrf_token': csrf_token}

            output = self.client.post('/distro/add', data=data, follow_redirects=True)

            # self.assertEqual(201, output.status_code)
            self.assertTrue(b'Distribution added' in output.data)

    def test_duplicate_distro(self):
        """Assert trying to create a duplicate distribution results in HTTP 409."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/add')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'name': 'Fedora', 'csrf_token': csrf_token}

            create_output = self.client.post('/distro/add', data=data, follow_redirects=True)
            dup_output = self.client.post('/distro/add', data=data, follow_redirects=True)

            self.assertTrue(b'Distribution added' in create_output.data)
            self.assertTrue(b'Could not add this distro' in dup_output.data)


class EditDistroTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.edit_distro` view function."""

    def setUp(self):
        super(EditDistroTests, self).setUp()

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        # Add distributions to edit
        self.fedora = models.Distro(name='Fedora')
        self.centos = models.Distro(name='CentOS')

        session.add_all([self.user, self.admin, self.fedora, self.centos])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the edit distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/distro/Fedora/edit')
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the edit distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/distro/Fedora/edit')
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can get the edit distribution view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/Fedora/edit')
            self.assertEqual(200, output.status_code)

    def test_admin_post(self):
        """Assert admin users can edit a distribution."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/Fedora/edit')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'name': 'Top', 'csrf_token': csrf_token}

            output = self.client.post('/distro/Fedora/edit', data=data, follow_redirects=True)
            self.assertEqual(200, output.status_code)
            self.assertEqual(200, self.client.get('/distro/Top/edit').status_code)

    def test_missing_distro(self):
        """Assert requesting a non-existing distro returns HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/LFS/edit')
            self.assertEqual(404, output.status_code)

    def test_no_csrf_token(self):
        """Assert submitting without a CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/distro/Fedora/edit', data={'name': 'Top'})
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.filter_by(name='Top').count())

    def test_invalid_csrf_token(self):
        """Assert submitting with an invalid CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post(
                '/distro/Fedora/edit', data={'csrf_token': 'a', 'name': 'Top'})
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.filter_by(name='Top').count())


class DeleteDistroTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_distro` view function."""

    def setUp(self):
        super(DeleteDistroTests, self).setUp()

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        # Add distributions to delete
        self.fedora = models.Distro(name='Fedora')
        self.centos = models.Distro(name='CentOS')

        session.add_all([self.user, self.admin, self.fedora, self.centos])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/distro/Fedora/delete')
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/distro/Fedora/delete')
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can get the delete distribution view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/Fedora/delete')
            self.assertEqual(200, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete a distribution."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/Fedora/delete')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'csrf_token': csrf_token}

            output = self.client.post('/distro/Fedora/delete', data=data, follow_redirects=True)
            self.assertEqual(200, output.status_code)
            self.assertEqual(404, self.client.get('/distro/Fedora/delete').status_code)

    def test_missing_distro(self):
        """Assert requesting a non-existing distro returns HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/distro/LFS/delete')
            self.assertEqual(404, output.status_code)

    def test_no_csrf_token(self):
        """Assert submitting without a CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/distro/Fedora/delete', data={})
            self.assertEqual(200, output.status_code)
            self.assertEqual(1, models.Distro.query.filter_by(name='Fedora').count())

    def test_invalid_csrf_token(self):
        """Assert submitting with an invalid CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/distro/Fedora/delete', data={'csrf_token': 'a'})
            self.assertEqual(200, output.status_code)
            self.assertEqual(1, models.Distro.query.filter_by(name='Fedora').count())


class DeleteProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_projects` view function."""

    def setUp(self):
        super(DeleteProjectTests, self).setUp()
        self.project = models.Project(
            name='test_project',
            homepage='https://example.com/test_project',
            backend='PyPI',
        )

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        session.add_all([self.user, self.admin, self.project])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete project view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/project/{0}/delete'.format(self.project.id))
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete project view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/project/{0}/delete'.format(self.project.id))
            self.assertEqual(401, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/project/42/delete')
            self.assertEqual(404, output.status_code)

    def test_admin_get(self):
        """Assert admin users can get the delete project view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/{0}/delete'.format(self.project.id))
            self.assertEqual(200, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete projects."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/{0}/delete'.format(self.project.id))
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'confirm': True, 'csrf_token': csrf_token}

            output = self.client.post(
                '/project/{0}/delete'.format(self.project.id), data=data, follow_redirects=True)

            self.assertEqual(200, output.status_code)
            self.assertEqual(0, len(models.Project.query.all()))

    def test_admin_post_unconfirmed(self):
        """Assert admin users must confirm deleting projects."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/{0}/delete'.format(self.project.id))
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'csrf_token': csrf_token}

            output = self.client.post('/project/{0}/delete'.format(self.project.id), data=data)

            self.assertEqual(302, output.status_code)
            self.assertEqual(1, len(models.Project.query.all()))


class DeleteProjectMappingTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_project_mapping` view."""

    def setUp(self):
        super(DeleteProjectMappingTests, self).setUp()
        self.project = models.Project(
            name='test_project',
            homepage='https://example.com/test_project',
            backend='PyPI',
        )
        self.distro = models.Distro(name='Fedora')
        self.package = models.Packages(
            distro=self.distro.name, project=self.project, package_name='test-project')

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        session.add_all([self.user, self.admin, self.distro, self.project, self.package])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete project mapping view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/project/1/delete/Fedora/test-project')
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete project mapping view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/project/1/delete/Fedora/test-project')
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can GET the delete project mapping view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/Fedora/test-project')
            self.assertEqual(200, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/42/delete/Fedora/test-project')
            self.assertEqual(404, output.status_code)

    def test_missing_distro(self):
        """Assert HTTP 404 is returned if the distro doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/LFS/test-project')
            self.assertEqual(404, output.status_code)

    def test_missing_package(self):
        """Assert HTTP 404 is returned if the package doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/Fedora/some-package')
            self.assertEqual(404, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete project mappings."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/Fedora/test-project')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'confirm': True, 'csrf_token': csrf_token}

            output = self.client.post(
                '/project/1/delete/Fedora/test-project', data=data, follow_redirects=True)

            self.assertEqual(200, output.status_code)
            self.assertEqual(0, len(models.Packages.query.all()))

    def test_admin_post_unconfirmed(self):
        """Assert failing to confirm the action results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/Fedora/test-project')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'csrf_token': csrf_token}

            output = self.client.post(
                '/project/1/delete/Fedora/test-project', data=data, follow_redirects=True)

            self.assertEqual(200, output.status_code)
            self.assertEqual(1, len(models.Packages.query.all()))


class DeleteProjectVersionTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_project_version` view."""

    def setUp(self):
        super(DeleteProjectVersionTests, self).setUp()
        session = Session()

        # Add a project with a version to delete.
        self.project = models.Project(
            name='test_project',
            homepage='https://example.com/test_project',
            backend='PyPI',
        )
        self.project_version = models.ProjectVersion(project=self.project, version='1.0.0')

        # Add a regular user and an admin user
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        session.add_all([self.user, self.admin, self.project, self.project_version])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete project version view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/project/1/delete/1.0.0')
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete project mapping view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/project/1/delete/1.0.0')
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can GET the delete project mapping view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/1.0.0')
            self.assertEqual(200, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/42/delete/1.0.0')
            self.assertEqual(404, output.status_code)

    def test_missing_version(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/42/delete/9.9.9')
            self.assertEqual(404, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete project mappings."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/1.0.0')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'confirm': True, 'csrf_token': csrf_token}

            output = self.client.post('/project/1/delete/1.0.0', data=data, follow_redirects=True)
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, len(models.ProjectVersion.query.all()))

    def test_admin_post_unconfirmed(self):
        """Assert failing to confirm the action results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/project/1/delete/1.0.0')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {'csrf_token': csrf_token}

            output = self.client.post('/project/1/delete/1.0.0', data=data)
            self.assertEqual(302, output.status_code)
            self.assertEqual(1, len(models.ProjectVersion.query.all()))


class BrowseLogsTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.browse_logs` view function."""

    def setUp(self):
        super(BrowseLogsTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        self.user_log = models.Log(
            user='user@example.com',
            project='relational_db',
            distro='Fedora',
            description='This is a log',
        )
        self.admin_log = models.Log(
            user='admin',
            project='best_project',
            distro='CentOS',
            description='This is also a log',
        )

        session.add_all([self.user, self.admin, self.user_log, self.admin_log])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users get only their own logs."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/logs')

            self.assertEqual(200, output.status_code)
            self.assertTrue(b'This is a log' in output.data)
            self.assertFalse(b'This is also a log' in output.data)

    def test_admin_get(self):
        """Assert admin users can get everyone's logs."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/logs')

            self.assertEqual(200, output.status_code)
            self.assertTrue(b'This is a log' in output.data)
            self.assertTrue(b'This is also a log' in output.data)

    def test_from_date(self):
        """Assert logs can be filtered via a from_date."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/logs?from_date=2017-07-19')

            self.assertEqual(200, output.status_code)
            self.assertTrue(b'This is a log' in output.data)
            self.assertTrue(b'This is also a log' in output.data)

    def test_from_date_future(self):
        """Assert when the from_date doesn't include logs, none are returned."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/logs?from_date=2500-07-01')

            self.assertEqual(200, output.status_code)
            self.assertFalse(b'This is a log' in output.data)
            self.assertFalse(b'This is also a log' in output.data)


class BrowseFlagsTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.browse_flags` view function."""

    def setUp(self):
        super(BrowseFlagsTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        self.project1 = models.Project(
            name='test_project', homepage='https://example.com/test_project', backend='PyPI')
        self.project2 = models.Project(
            name='project2', homepage='https://example.com/project2', backend='PyPI')
        self.flag1 = models.ProjectFlag(
            reason='I wanted to flag it', user='user', project=self.project1)
        self.flag2 = models.ProjectFlag(
            reason='This project is wrong', user='user', project=self.project2)

        session.add_all(
            [self.user, self.admin, self.project1, self.project2, self.flag1, self.flag2])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users can't see flags."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/flags')
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/flags')

            self.assertEqual(200, output.status_code)
            self.assertTrue(b'I wanted to flag it' in output.data)
            self.assertTrue(b'This project is wrong' in output.data)

    def test_pages(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            page_one = self.client.get('/flags?limit=1&page=1')

            self.assertEqual(200, page_one.status_code)
            self.assertTrue(
                b'I wanted to flag it' in page_one.data or
                b'This project is wrong' in page_one.data
            )
            self.assertFalse(
                b'I wanted to flag it' in page_one.data and
                b'This project is wrong' in page_one.data
            )

    def test_from_date(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/flags?from_date=2017-07-01')

            self.assertEqual(200, output.status_code)
            self.assertTrue(b'I wanted to flag it' in output.data)
            self.assertTrue(b'This project is wrong' in output.data)

    def test_from_date_future(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/flags?from_date=2200-07-01')

            self.assertEqual(200, output.status_code)
            self.assertFalse(b'I wanted to flag it' in output.data)
            self.assertFalse(b'This project is wrong' in output.data)


class SetFlagStateTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.set_flag_state` view function."""

    def setUp(self):
        super(SetFlagStateTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email='user@example.com', username='user')
        self.admin = models.User(email='admin@example.com', username='admin')

        self.project1 = models.Project(
            name='test_project', homepage='https://example.com/test_project', backend='PyPI')
        self.project2 = models.Project(
            name='project2', homepage='https://example.com/project2', backend='PyPI')
        self.flag1 = models.ProjectFlag(
            reason='I wanted to flag it', user='user', project=self.project1)
        self.flag2 = models.ProjectFlag(
            reason='This project is wrong', user='user', project=self.project2)

        session.add_all(
            [self.user, self.admin, self.project1, self.project2, self.flag1, self.flag2])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {'ANITYA_WEB_ADMINS': [six.text_type(self.admin.id)]})
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_post(self):
        """Assert non-admin users can't set flags."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/flags/1/set/closed')
            self.assertEqual(401, output.status_code)

    def test_bad_state(self):
        """Assert an invalid stat results in HTTP 422."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/flags/1/set/deferred')
            self.assertEqual(422, output.status_code)

    def test_missing(self):
        """Assert trying to set the state of a non-existent flag results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post('/flags/42/set/closed')
            self.assertEqual(404, output.status_code)

    def test_set_flag(self):
        """Assert trying to set the state of a non-existent flag results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get('/flags')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]

            output = self.client.post(
                '/flags/1/set/closed', data={'csrf_token': csrf_token}, follow_redirects=True)

            self.assertEqual(200, output.status_code)
            self.assertTrue(b'Flag 1 set to closed' in output.data)
