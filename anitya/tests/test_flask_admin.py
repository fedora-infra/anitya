# -*- coding: utf-8 -*-
#
# Copyright © 2014-2020  Red Hat, Inc.
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

from fedora_messaging import testing as fml_testing
from social_flask_sqlalchemy import models as social_models
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.query import Query
import anitya_schema

from anitya import admin
from anitya.db import models, Session
from anitya.tests.base import DatabaseTestCase, login_user


class IsAdminTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.is_admin` function."""

    def setUp(self):
        super(IsAdminTests, self).setUp()

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )
        session.add_all([admin_social_auth, self.admin])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

    def test_admin_user(self):
        """Assert admin users passed via parameter returns True."""
        self.assertTrue(admin.is_admin(self.admin))

    def test_non_admin_user(self):
        """Assert regular users passed via parameter returns False."""
        self.assertFalse(admin.is_admin(self.user))


class EditDistroTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.edit_distro` view function."""

    def setUp(self):
        super(EditDistroTests, self).setUp()

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        # Add distributions to edit
        self.fedora = models.Distro(name="Fedora")
        self.centos = models.Distro(name="CentOS")

        session.add_all([admin_social_auth, self.admin, self.fedora, self.centos])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the edit distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/distro/Fedora/edit")
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the edit distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/distro/Fedora/edit")
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can get the edit distribution view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/distro/Fedora/edit")
            self.assertEqual(200, output.status_code)

    def test_admin_post(self):
        """Assert admin users can edit a distribution."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/distro/Fedora/edit")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"name": "Top", "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.DistroEdited):
                output = self.client.post(
                    "/distro/Fedora/edit", data=data, follow_redirects=True
                )
            self.assertEqual(200, output.status_code)
            self.assertEqual(200, self.client.get("/distro/Top/edit").status_code)

    def test_missing_distro(self):
        """Assert requesting a non-existing distro returns HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/distro/LFS/edit")
            self.assertEqual(404, output.status_code)

    def test_no_csrf_token(self):
        """Assert submitting without a CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/distro/Fedora/edit", data={"name": "Top"})
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.filter_by(name="Top").count())

    def test_invalid_csrf_token(self):
        """Assert submitting with an invalid CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post(
                "/distro/Fedora/edit", data={"csrf_token": "a", "name": "Top"}
            )
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.filter_by(name="Top").count())


class DeleteDistroTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_distro` view function."""

    def setUp(self):
        super(DeleteDistroTests, self).setUp()

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        # Add distributions to delete
        self.fedora = models.Distro(name="Fedora")
        self.centos = models.Distro(name="CentOS")

        session.add_all([admin_social_auth, self.admin, self.fedora, self.centos])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/distro/Fedora/delete")
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete distribution view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/distro/Fedora/delete")
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can get the delete distribution view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/distro/Fedora/delete")
            self.assertEqual(200, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete a distribution."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/distro/Fedora/delete")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.DistroDeleted):
                output = self.client.post(
                    "/distro/Fedora/delete", data=data, follow_redirects=True
                )
            self.assertEqual(200, output.status_code)
            self.assertEqual(404, self.client.get("/distro/Fedora/delete").status_code)

    def test_missing_distro(self):
        """Assert requesting a non-existing distro returns HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/distro/LFS/delete")
            self.assertEqual(404, output.status_code)

    def test_no_csrf_token(self):
        """Assert submitting without a CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/distro/Fedora/delete", data={})
            self.assertEqual(200, output.status_code)
            self.assertEqual(1, models.Distro.query.filter_by(name="Fedora").count())

    def test_invalid_csrf_token(self):
        """Assert submitting with an invalid CSRF token results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/distro/Fedora/delete", data={"csrf_token": "a"})
            self.assertEqual(200, output.status_code)
            self.assertEqual(1, models.Distro.query.filter_by(name="Fedora").count())


class DeleteProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_projects` view function."""

    def setUp(self):
        super(DeleteProjectTests, self).setUp()
        self.project = models.Project(
            name="test_project",
            homepage="https://example.com/test_project",
            backend="PyPI",
        )

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        session.add_all([admin_social_auth, self.admin, self.project])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete project view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/project/{0}/delete".format(self.project.id))
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete project view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/project/{0}/delete".format(self.project.id))
            self.assertEqual(401, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/project/42/delete")
            self.assertEqual(404, output.status_code)

    def test_admin_get(self):
        """Assert admin users can get the delete project view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/{0}/delete".format(self.project.id))
            self.assertEqual(200, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete projects."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/{0}/delete".format(self.project.id))
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectDeleted):
                output = self.client.post(
                    "/project/{0}/delete".format(self.project.id),
                    data=data,
                    follow_redirects=True,
                )

            self.assertEqual(200, output.status_code)
            self.assertEqual(0, len(models.Project.query.all()))

    def test_admin_post_unconfirmed(self):
        """Assert admin users must confirm deleting projects."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/{0}/delete".format(self.project.id))
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"csrf_token": csrf_token}

            output = self.client.post(
                "/project/{0}/delete".format(self.project.id), data=data
            )

            self.assertEqual(302, output.status_code)
            self.assertEqual(1, len(models.Project.query.all()))


class SetProjectArchiveState(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.set_project_archive_state` view function."""

    def setUp(self):
        super(SetProjectArchiveState, self).setUp()
        self.project = models.Project(
            name="test_project",
            homepage="https://example.com/test_project",
            backend="PyPI",
        )

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        session.add_all([admin_social_auth, self.admin, self.project])
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the archive project view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get(
                "/project/{0}/archive/set/true".format(self.project.id)
            )
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the archive project view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post(
                "/project/{0}/archive/set/true".format(self.project.id)
            )
            self.assertEqual(401, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/project/42/archive/set/true")
            self.assertEqual(404, output.status_code)

    def test_wrong_state(self):
        """Assert HTTP 404 is returned if the state doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post(
                "/project/{0}/archive/set/nonsense".format(self.project.id)
            )
            self.assertEqual(422, output.status_code)

    def test_admin_post(self):
        """Assert admin users can archive projects."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get(
                "/project/{0}/archive/set/true".format(self.project.id)
            )
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectEdited):
                output = self.client.post(
                    "/project/{0}/archive/set/true".format(self.project.id),
                    data=data,
                    follow_redirects=True,
                )

            project = models.Project.query.one()

            self.assertEqual(200, output.status_code)
            self.assertEqual(project.archived, True)

    def test_admin_post_unarchive(self):
        """Assert admin users can unarchive projects."""
        self.project.archived = True
        self.session.add(self.project)
        self.session.commit()
        with login_user(self.flask_app, self.admin):
            output = self.client.get(
                "/project/{0}/archive/set/false".format(self.project.id)
            )
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectEdited):
                output = self.client.post(
                    "/project/{0}/archive/set/false".format(self.project.id),
                    data=data,
                    follow_redirects=True,
                )

            project = models.Project.query.one()

            self.assertEqual(200, output.status_code)
            self.assertEqual(project.archived, False)

    def test_admin_post_unconfirmed(self):
        """Assert admin users must confirm archiving projects."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get(
                "/project/{0}/archive/set/true".format(self.project.id)
            )
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"csrf_token": csrf_token}

            output = self.client.post(
                "/project/{0}/archive/set/true".format(self.project.id), data=data
            )

            project = models.Project.query.one()

            self.assertEqual(302, output.status_code)
            self.assertEqual(project.archived, False)


class DeleteProjectMappingTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_project_mapping` view."""

    def setUp(self):
        super(DeleteProjectMappingTests, self).setUp()
        self.project = models.Project(
            name="test_project",
            homepage="https://example.com/test_project",
            backend="PyPI",
        )
        self.distro = models.Distro(name="Fedora")
        self.package = models.Packages(
            distro_name=self.distro.name,
            project=self.project,
            package_name="test-project",
        )

        # Add a regular user and an admin user
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        session.add_all(
            [admin_social_auth, self.admin, self.distro, self.project, self.package]
        )
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete project mapping view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/project/1/delete/Fedora/test-project")
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete project mapping view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/project/1/delete/Fedora/test-project")
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can GET the delete project mapping view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/Fedora/test-project")
            self.assertEqual(200, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/42/delete/Fedora/test-project")
            self.assertEqual(404, output.status_code)

    def test_missing_distro(self):
        """Assert HTTP 404 is returned if the distro doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/LFS/test-project")
            self.assertEqual(404, output.status_code)

    def test_missing_package(self):
        """Assert HTTP 404 is returned if the package doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/Fedora/some-package")
            self.assertEqual(404, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete project mappings."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/Fedora/test-project")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectMapDeleted):
                output = self.client.post(
                    "/project/1/delete/Fedora/test-project",
                    data=data,
                    follow_redirects=True,
                )

            self.assertEqual(200, output.status_code)
            self.assertEqual(0, len(models.Packages.query.all()))

    def test_admin_post_unconfirmed(self):
        """Assert failing to confirm the action results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/Fedora/test-project")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"csrf_token": csrf_token}

            output = self.client.post(
                "/project/1/delete/Fedora/test-project",
                data=data,
                follow_redirects=True,
            )

            self.assertEqual(200, output.status_code)
            self.assertEqual(1, len(models.Packages.query.all()))


class DeleteProjectVersionTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_project_version` view."""

    def setUp(self):
        super(DeleteProjectVersionTests, self).setUp()
        self.session = Session()

        # Add a project with a version to delete.
        self.project = models.Project(
            name="test_project",
            homepage="https://example.com/test_project",
            backend="PyPI",
        )
        self.project_version = models.ProjectVersion(
            project=self.project, version="1.0.0"
        )

        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        self.session.add_all(
            [admin_social_auth, self.admin, self.project, self.project_version]
        )
        self.session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the delete project version view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/project/1/delete/1.0.0")
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the delete project mapping view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/project/1/delete/1.0.0")
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can GET the delete project mapping view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/1.0.0")
            self.assertEqual(200, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/42/delete/1.0.0")
            self.assertEqual(404, output.status_code)

    def test_missing_version(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/42/delete/9.9.9")
            self.assertEqual(404, output.status_code)

    def test_admin_post(self):
        """Assert admin users can delete project mappings."""
        self.project.latest_version = "1.0.0"
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/1.0.0")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectVersionDeleted):
                output = self.client.post(
                    "/project/1/delete/1.0.0", data=data, follow_redirects=True
                )
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, len(models.ProjectVersion.query.all()))
            self.assertEqual(self.project.latest_version, None)

    def test_admin_post_latest_version(self):
        """Assert latest version is changed when version is removed."""
        project_version = models.ProjectVersion(project=self.project, version="1.0.1")
        self.session.add(project_version)
        self.session.commit()
        self.project.latest_version = "1.0.1"

        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/1.0.1")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectVersionDeleted):
                output = self.client.post(
                    "/project/1/delete/1.0.1", data=data, follow_redirects=True
                )
            self.assertEqual(200, output.status_code)
            self.assertEqual(1, len(models.ProjectVersion.query.all()))
            self.assertEqual(self.project.latest_version, "1.0.0")

    def test_admin_post_latest_version_parsed(self):
        """
        Assert latest version is changed when version is parsed version of deleted version.
        For example v1.0.1 is latest version 1.0.1.
        """
        project_version = models.ProjectVersion(project=self.project, version="v1.0.1")
        self.session.add(project_version)
        self.session.commit()
        self.project.latest_version = "1.0.1"

        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/v1.0.1")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectVersionDeleted):
                output = self.client.post(
                    "/project/1/delete/v1.0.1", data=data, follow_redirects=True
                )
            self.assertEqual(200, output.status_code)
            self.assertEqual(1, len(models.ProjectVersion.query.all()))
            self.assertEqual(self.project.latest_version, "1.0.0")

    def test_admin_post_latest_version_delete_previous(self):
        """Assert latest version is not changed when other than latest version is removed."""
        project_version = models.ProjectVersion(project=self.project, version="1.0.1")
        self.session.add(project_version)
        self.session.commit()
        self.project.latest_version = "1.0.1"

        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/1.0.0")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectVersionDeleted):
                output = self.client.post(
                    "/project/1/delete/1.0.0", data=data, follow_redirects=True
                )
            self.assertEqual(200, output.status_code)
            self.assertEqual(1, len(models.ProjectVersion.query.all()))
            self.assertEqual(self.project.latest_version, "1.0.1")

    def test_admin_post_unconfirmed(self):
        """Assert failing to confirm the action results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/1.0.0")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"csrf_token": csrf_token}

            output = self.client.post("/project/1/delete/1.0.0", data=data)
            self.assertEqual(302, output.status_code)
            self.assertEqual(1, len(models.ProjectVersion.query.all()))


class DeleteProjectVersionsTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.delete_project_versions` view."""

    def setUp(self):
        super(DeleteProjectVersionsTests, self).setUp()
        self.session = Session()

        # Add a project with a version to delete.
        self.project = models.Project(
            name="test_project",
            homepage="https://example.com/test_project",
            backend="PyPI",
        )
        self.project_version = models.ProjectVersion(
            project=self.project, version="1.0.0"
        )

        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        self.session.add_all(
            [admin_social_auth, self.admin, self.project, self.project_version]
        )
        self.session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users cannot GET the filter project versions view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/project/1/delete/versions")
            self.assertEqual(401, output.status_code)

    def test_non_admin_post(self):
        """Assert non-admin users cannot POST to the filter project versions view."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/project/1/delete/versions")
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can GET the filter project versions view."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/versions")
            self.assertEqual(200, output.status_code)

    def test_missing_project(self):
        """Assert HTTP 404 is returned if the project doesn't exist."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/42/delete/versions")
            self.assertEqual(404, output.status_code)

    def test_admin_post(self):
        """Assert admin users can filter project versions."""
        self.project.latest_version = "1.0.0"
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/versions")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"confirm": True, "csrf_token": csrf_token}

            with fml_testing.mock_sends(anitya_schema.ProjectVersionDeleted):
                output = self.client.post(
                    "/project/1/delete/versions", data=data, follow_redirects=True
                )
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, len(models.ProjectVersion.query.all()))
            self.assertEqual(self.project.latest_version, None)

    def test_admin_post_unconfirmed(self):
        """Assert failing to confirm the action results in no change."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/project/1/delete/versions")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"csrf_token": csrf_token}

            output = self.client.post("/project/1/delete/versions", data=data)
            self.assertEqual(302, output.status_code)
            self.assertEqual(1, len(models.ProjectVersion.query.all()))


class BrowseFlagsTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.browse_flags` view function."""

    def setUp(self):
        super(BrowseFlagsTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        self.project1 = models.Project(
            name="test_project",
            homepage="https://example.com/test_project",
            backend="PyPI",
        )
        self.project2 = models.Project(
            name="project2", homepage="https://example.com/project2", backend="PyPI"
        )
        self.flag1 = models.ProjectFlag(
            reason="I wanted to flag it", user="user", project=self.project1
        )
        self.flag2 = models.ProjectFlag(
            reason="This project is wrong", user="user", project=self.project2
        )

        session.add_all(
            [
                admin_social_auth,
                self.admin,
                self.project1,
                self.project2,
                self.flag1,
                self.flag2,
            ]
        )
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users can't see flags."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/flags")
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/flags")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"I wanted to flag it" in output.data)
            self.assertTrue(b"This project is wrong" in output.data)

    def test_pages(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            page_one = self.client.get("/flags?limit=1&page=1")

            self.assertEqual(200, page_one.status_code)
            self.assertTrue(
                b"I wanted to flag it" in page_one.data
                or b"This project is wrong" in page_one.data
            )
            self.assertFalse(
                b"I wanted to flag it" in page_one.data
                and b"This project is wrong" in page_one.data
            )

    def test_from_date(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/flags?from_date=2017-07-01")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"I wanted to flag it" in output.data)
            self.assertTrue(b"This project is wrong" in output.data)

    def test_from_date_future(self):
        """Assert admin users can see the flags."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/flags?from_date=2200-07-01")

            self.assertEqual(200, output.status_code)
            self.assertFalse(b"I wanted to flag it" in output.data)
            self.assertFalse(b"This project is wrong" in output.data)


class SetFlagStateTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.set_flag_state` view function."""

    def setUp(self):
        super(SetFlagStateTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        self.project1 = models.Project(
            name="test_project",
            homepage="https://example.com/test_project",
            backend="PyPI",
        )
        self.project2 = models.Project(
            name="project2", homepage="https://example.com/project2", backend="PyPI"
        )
        self.flag1 = models.ProjectFlag(
            reason="I wanted to flag it", user="user", project=self.project1
        )
        self.flag2 = models.ProjectFlag(
            reason="This project is wrong", user="user", project=self.project2
        )

        session.add_all(
            [
                admin_social_auth,
                self.admin,
                self.project1,
                self.project2,
                self.flag1,
                self.flag2,
            ]
        )
        session.commit()

        mock_config = mock.patch.dict(
            models.anitya_config, {"ANITYA_WEB_ADMINS": [six.text_type(self.admin.id)]}
        )
        mock_config.start()
        self.addCleanup(mock_config.stop)

        self.client = self.flask_app.test_client()

    def test_non_admin_post(self):
        """Assert non-admin users can't set flags."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/flags/1/set/closed")
            self.assertEqual(401, output.status_code)

    def test_bad_state(self):
        """Assert an invalid stat results in HTTP 422."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/flags/1/set/deferred")
            self.assertEqual(422, output.status_code)

    def test_missing(self):
        """Assert trying to set the state of a non-existent flag results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/flags/42/set/closed")
            self.assertEqual(404, output.status_code)

    def test_set_flag(self):
        """Assert trying to set the state of a non-existent flag results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/flags")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            with fml_testing.mock_sends(anitya_schema.ProjectFlagSet):
                output = self.client.post(
                    "/flags/1/set/closed",
                    data={"csrf_token": csrf_token},
                    follow_redirects=True,
                )

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"Flag 1 set to closed" in output.data)


class BrowseUsersTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.browse_users` view function."""

    def setUp(self):
        super(BrowseUsersTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(
            email="admin@example.com", username="admin", admin=True
        )
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        session.add_all([admin_social_auth, self.admin])
        session.commit()

        self.client = self.flask_app.test_client()

    def test_non_admin_get(self):
        """Assert non-admin users can't see users."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/users")
            self.assertEqual(401, output.status_code)

    def test_admin_get(self):
        """Assert admin users can see the users."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertTrue(b"user@fedoraproject.org" in output.data)

    def test_pages(self):
        """Assert admin users can see the users."""
        with login_user(self.flask_app, self.admin):
            page_one = self.client.get("/users?limit=1&page=1")

            self.assertEqual(200, page_one.status_code)
            self.assertTrue(b"user@fedoraproject.org" in page_one.data)
            self.assertFalse(b"admin@example.com" in page_one.data)

    def test_pagination_offset(self):
        """Assert offset is calculated when page is > 1."""
        with login_user(self.flask_app, self.admin):
            page = self.client.get("/users?limit=1&page=2")

            self.assertEqual(200, page.status_code)
            self.assertFalse(b"user@fedoraproject.org" in page.data)
            self.assertTrue(b"admin@example.com" in page.data)

    def test_pagination_limit_zero(self):
        """Assert limit is not used when set to 0."""
        with login_user(self.flask_app, self.admin):
            page = self.client.get("/users?limit=0&page=1")

            self.assertEqual(200, page.status_code)
            self.assertTrue(b"user@fedoraproject.org" in page.data)
            self.assertTrue(b"admin@example.com" in page.data)

    def test_pagination_limit_negative(self):
        """Assert limit is not used when set to negative value."""
        with login_user(self.flask_app, self.admin):
            page = self.client.get("/users?limit=-1")

            self.assertEqual(200, page.status_code)
            self.assertTrue(b"user@fedoraproject.org" in page.data)
            self.assertTrue(b"admin@example.com" in page.data)

    def test_pagination_invalid_page(self):
        """Assert pagination returns first page on invalid value."""
        with login_user(self.flask_app, self.admin):
            page_one = self.client.get("/users?limit=1&page=dummy")

            self.assertEqual(200, page_one.status_code)
            self.assertTrue(b"user@fedoraproject.org" in page_one.data)
            self.assertFalse(b"admin@example.com" in page_one.data)

    def test_pagination_invalid_limit(self):
        """Assert pagination sets limit to default value on invalid input value."""
        with login_user(self.flask_app, self.admin):
            page_one = self.client.get("/users?limit=dummy&page=1")

            self.assertEqual(200, page_one.status_code)
            self.assertTrue(b"user@fedoraproject.org" in page_one.data)
            self.assertTrue(b"admin@example.com" in page_one.data)

    def test_filter_user_id(self):
        """Assert filter by user_id works."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get(
                "/users?user_id={}".format(six.text_type(self.admin.id))
            )

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)

    def test_filter_user_id_wrong(self):
        """Assert filter by wrong user_id returns nothing."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?user_id=dummy")

            self.assertEqual(200, output.status_code)
            self.assertFalse(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)

    def test_filter_username(self):
        """Assert filter by username works."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?username={}".format(self.admin.username))

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)

    def test_filter_username_wrong(self):
        """Assert filter by wrong username returns nothing."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?username=dummy")

            self.assertEqual(200, output.status_code)
            self.assertFalse(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)

    def test_filter_email(self):
        """Assert filter by email works."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?email={}".format(self.admin.email))

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)

    def test_filter_email_wrong(self):
        """Assert filter by wrong email returns nothing."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?email=dummy")

            self.assertEqual(200, output.status_code)
            self.assertFalse(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)

    def test_filter_admin_true(self):
        """Assert filter by admin flag works."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?admin=True")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)

    def test_filter_admin_false(self):
        """Assert filter by admin flag works."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?admin=False")

            self.assertEqual(200, output.status_code)
            self.assertFalse(b"admin@example.com" in output.data)
            self.assertTrue(b"user@fedoraproject.org" in output.data)

    def test_filter_admin_wrong(self):
        """Assert filter by wrong admin flag returns everything."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?admin=dummy")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertTrue(b"user@fedoraproject.org" in output.data)

    def test_filter_active_true(self):
        """Assert filter by active flag works."""
        # Add a inactive user
        user = models.User(
            email="inactive@fedoraproject.org", username="inactive", active=False
        )
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?active=True")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertTrue(b"user@fedoraproject.org" in output.data)
            self.assertFalse(b"inactive@fedoraproject.org" in output.data)

    def test_filter_active_false(self):
        """Assert filter by active flag works."""
        # Add a inactive user
        user = models.User(
            email="inactive@fedoraproject.org", username="inactive", active=False
        )
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?active=False")

            self.assertEqual(200, output.status_code)
            self.assertFalse(b"admin@example.com" in output.data)
            self.assertFalse(b"user@fedoraproject.org" in output.data)
            self.assertTrue(b"inactive@fedoraproject.org" in output.data)

    def test_filter_active_wrong(self):
        """Assert filter by wrong active flag returns everything."""
        # Add a inactive user
        user = models.User(
            email="inactive@fedoraproject.org", username="inactive", active=False
        )
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users?active=dummy")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"admin@example.com" in output.data)
            self.assertTrue(b"user@fedoraproject.org" in output.data)
            self.assertTrue(b"inactive@fedoraproject.org" in output.data)

    def test_sql_exception(self):
        """ Assert that SQL exception is handled correctly."""
        with mock.patch.object(
            Query,
            "filter_by",
            mock.Mock(side_effect=[SQLAlchemyError("SQLError"), None]),
        ):
            with login_user(self.flask_app, self.admin):
                output = self.client.get("/users?user_id=dummy")

                self.assertEqual(200, output.status_code)
                self.assertTrue(b"SQLError" in output.data)
                self.assertFalse(b"admin@example.com" in output.data)
                self.assertFalse(b"user@fedoraproject.org" in output.data)


class SetUserAdminStateTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.set_user_admin_state` view function."""

    def setUp(self):
        super(SetUserAdminStateTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.admin = models.User(
            email="admin@example.com", username="admin", admin=True
        )
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )
        session.add_all([admin_social_auth, self.admin])
        session.commit()

        self.client = self.flask_app.test_client()

    def test_non_admin_post(self):
        """Assert non-admin users can't set flags."""
        with login_user(self.flask_app, self.user):
            output = self.client.post(
                "/users/{}/admin/True".format(six.text_type(self.user.id))
            )
            self.assertEqual(401, output.status_code)

    def test_bad_state(self):
        """Assert an invalid state results in HTTP 422."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post(
                "/users/{}/admin/wrong".format(six.text_type(self.user.id))
            )
            self.assertEqual(422, output.status_code)

    def test_missing_state(self):
        """Assert an missing state results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post(
                "/users/{}/admin/".format(six.text_type(self.user.id))
            )
            self.assertEqual(404, output.status_code)

    def test_missing_user(self):
        """Assert trying to set the state of a non-existent user results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/users/42/admin/true")
            self.assertEqual(404, output.status_code)

    def test_set_admin(self):
        """Assert that admin flag is set correctly."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            output = self.client.post(
                "/users/{}/admin/True".format(six.text_type(self.user.id)),
                data={"csrf_token": csrf_token},
                follow_redirects=True,
            )

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"User user is now admin" in output.data)
            self.assertTrue(self.user.admin)

    def test_sql_exception(self):
        """ Assert that SQL exception is handled correctly."""
        with mock.patch.object(
            self.session,
            "add",
            mock.Mock(side_effect=[SQLAlchemyError("SQLError"), None]),
        ):
            with login_user(self.flask_app, self.admin):
                output = self.client.get("/users")
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]

                output = self.client.post(
                    "/users/{}/admin/True".format(six.text_type(self.user.id)),
                    data={"csrf_token": csrf_token},
                    follow_redirects=True,
                )

                self.assertEqual(200, output.status_code)
                self.assertTrue(b"SQLError" in output.data)
                self.assertFalse(self.user.admin)

    def test_form_not_valid(self):
        """ Assert that invalid form will do nothing."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            with mock.patch("anitya.forms.ConfirmationForm") as mock_form:
                mock_form.return_value.validate_on_submit.return_value = False
                output = self.client.post(
                    "/users/{}/admin/True".format(six.text_type(self.user.id)),
                    data={"csrf_token": csrf_token},
                    follow_redirects=True,
                )

                self.assertEqual(200, output.status_code)
                self.assertTrue(b"admin@example.com" in output.data)
                self.assertTrue(b"user@fedoraproject.org" in output.data)
                self.assertFalse(self.user.admin)

    def test_remove_admin(self):
        """Assert that admin flag is removed correctly."""
        self.user.admin = True
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            self.assertTrue(self.user.admin)
            output = self.client.post(
                "/users/{}/admin/False".format(six.text_type(self.user.id)),
                data={"csrf_token": csrf_token},
                follow_redirects=True,
            )

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"User user is not admin anymore" in output.data)
            self.assertFalse(self.user.admin)

    def test_remove_admin_current_user(self):
        """Assert that admin flag is removed correctly."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            output = self.client.post(
                "/users/{}/admin/False".format(six.text_type(self.admin.id)),
                data={"csrf_token": csrf_token},
                follow_redirects=True,
            )

            self.assertEqual(401, output.status_code)
            self.assertFalse(self.admin.admin)


class SetUserActiveStateTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.set_user_admin_state` view function."""

    def setUp(self):
        super(SetUserActiveStateTests, self).setUp()
        session = Session()

        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)

        # Add inactive user
        self.inactive_user = models.User(
            email="inactive@fedoraproject.org", username="inactive_user", active=False
        )
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.inactive_user.id, user=self.inactive_user
        )

        session.add(self.inactive_user)
        session.add(user_social_auth)
        self.admin = models.User(
            email="admin@example.com", username="admin", admin=True
        )
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )
        session.add_all([admin_social_auth, self.admin])
        session.commit()

        self.client = self.flask_app.test_client()

    def test_non_admin_post(self):
        """Assert non-admin users can't set flags."""
        with login_user(self.flask_app, self.user):
            output = self.client.post(
                "/users/{}/active/True".format(six.text_type(self.user.id))
            )
            self.assertEqual(401, output.status_code)

    def test_bad_state(self):
        """Assert an invalid state results in HTTP 422."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post(
                "/users/{}/active/wrong".format(six.text_type(self.user.id))
            )
            self.assertEqual(422, output.status_code)

    def test_missing_state(self):
        """Assert an missing state results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post(
                "/users/{}/active/".format(six.text_type(self.user.id))
            )
            self.assertEqual(404, output.status_code)

    def test_missing_user(self):
        """Assert trying to set the state of a non-existent user results in HTTP 404."""
        with login_user(self.flask_app, self.admin):
            output = self.client.post("/users/42/active/true")
            self.assertEqual(404, output.status_code)

    def test_sql_exception(self):
        """ Assert that SQL exception is handled correctly."""
        with mock.patch.object(
            self.session,
            "add",
            mock.Mock(side_effect=[SQLAlchemyError("SQLError"), None]),
        ):
            with login_user(self.flask_app, self.admin):
                output = self.client.get("/users")
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]

                output = self.client.post(
                    "/users/{}/active/False".format(six.text_type(self.user.id)),
                    data={"csrf_token": csrf_token},
                    follow_redirects=True,
                )

                self.assertEqual(200, output.status_code)
                self.assertTrue(b"SQLError" in output.data)
                self.assertTrue(self.user.active)

    def test_form_not_valid(self):
        """ Assert that invalid form will do nothing."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            with mock.patch("anitya.forms.ConfirmationForm") as mock_form:
                mock_form.return_value.validate_on_submit.return_value = False
                output = self.client.post(
                    "/users/{}/active/False".format(six.text_type(self.user.id)),
                    data={"csrf_token": csrf_token},
                    follow_redirects=True,
                )

                self.assertEqual(200, output.status_code)
                self.assertTrue(b"admin@example.com" in output.data)
                self.assertTrue(b"user@fedoraproject.org" in output.data)
                self.assertTrue(self.user.active)

    def test_set_active(self):
        """Assert that active flag is set correctly."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            output = self.client.post(
                "/users/{}/active/True".format(six.text_type(self.inactive_user.id)),
                data={"csrf_token": csrf_token},
                follow_redirects=True,
            )

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"User inactive_user is no longer banned" in output.data)
            self.assertTrue(self.inactive_user.active)

    def test_ban(self):
        """Assert that active flag is removed correctly."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/users")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]

            output = self.client.post(
                "/users/{}/active/False".format(six.text_type(self.user.id)),
                data={"csrf_token": csrf_token},
                follow_redirects=True,
            )

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"User user is banned" in output.data)
            self.assertFalse(self.user.active)


class BrowseLogsTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.browse_logs` view function."""

    def setUp(self):
        super(BrowseLogsTests, self).setUp()
        session = Session()
        # Add a regular user and an admin user
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)

        self.admin = models.User(email="admin@example.com", username="admin")
        admin_social_auth = social_models.UserSocialAuth(
            user_id=self.admin.id, user=self.admin
        )

        session.add_all([admin_social_auth, self.admin])
        session.commit()

        self.client = self.flask_app.test_client()

    def test_get_logs(self):
        """Assert logs are shown."""
        project = models.Project(
            name="best_project",
            homepage="https://example.com/best_project",
            backend="PyPI",
            ecosystem_name="pypi",
            check_successful=True,
            logs="Everything allright",
        )

        self.session.add(project)
        self.session.commit()

        with login_user(self.flask_app, self.user):
            output = self.client.get("/logs")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"best_project" in output.data)
            self.assertTrue(b"OK" in output.data)
            self.assertTrue(b"Everything allright" in output.data)

    def test_incorrect_page(self):
        """Assert exception is handled correctly."""
        with login_user(self.flask_app, self.admin):
            output = self.client.get("/logs?page=a")

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"/logs?page=1" in output.data)
