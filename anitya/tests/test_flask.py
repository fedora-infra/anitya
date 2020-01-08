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

"""
anitya tests for the flask application.
"""

from sqlalchemy.exc import SQLAlchemyError
from six.moves.urllib import parse
import mock

import anitya_schema
from fedora_messaging import testing as fml_testing
from social_flask_sqlalchemy import models as social_models

from anitya import ui
from anitya.db import models, Session
from anitya.lib import exceptions
from anitya.tests.base import (
    AnityaTestCase,
    DatabaseTestCase,
    create_distro,
    create_project,
    login_user,
    create_package,
)


class ShutdownSessionTests(AnityaTestCase):
    """Tests for the :func:`anitya.app.shutdown_session` function."""

    def test_session_removed_post_request(self):
        """Assert that the session is cleaned up after a request."""
        session = Session()
        self.assertTrue(session is Session())
        app = self.flask_app.test_client()
        app.get("/about", follow_redirects=False)
        self.assertFalse(session is Session())


class SettingsTests(DatabaseTestCase):
    def setUp(self):
        """Set up the Flask testing environnment"""
        super(SettingsTests, self).setUp()
        self.app = self.flask_app.test_client()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.session.commit()

    def test_login_required(self):
        """Assert this view is protected and login is required."""
        output = self.app.get("/settings/", follow_redirects=False)
        self.assertEqual(output.status_code, 302)
        self.assertEqual("/login/", parse.urlparse(output.location).path)

    def test_new_token(self):
        """Assert a user can create a new API token."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/settings/", follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {"csrf_token": csrf_token, "description": "Test token"}

                output = c.post(
                    "/settings/tokens/new", data=data, follow_redirects=True
                )

                self.assertEqual(output.status_code, 200)
                self.assertTrue(b"Test token" in output.data)

    def test_new_token_bad_csrf(self):
        """Assert a valid CSRF token is required to make a token."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                data = {"csrf_token": "no good?", "description": "Test token"}

                output = c.post(
                    "/settings/tokens/new", data=data, follow_redirects=True
                )

                self.assertEqual(output.status_code, 400)
                self.assertFalse(b"Test token" in output.data)

    def test_delete_token(self):
        """Assert a user can delete an API token."""
        session = Session()
        token = models.ApiToken(user=self.user, description="Test token")
        session.add(token)
        session.commit()

        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/settings/", follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(b"Test token" in output.data)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {"csrf_token": csrf_token}

                output = c.post(
                    "/settings/tokens/delete/{}/".format(token.token),
                    data=data,
                    follow_redirects=True,
                )

                self.assertEqual(output.status_code, 200)
                self.assertFalse(b"Test token" in output.data)
                self.assertEqual(
                    0, models.ApiToken.query.filter_by(user=self.user).count()
                )

    def test_delete_invalid_token(self):
        """Assert trying to delete an invalid token fails."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/settings/", follow_redirects=False)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {"csrf_token": csrf_token}

                output = c.post(
                    "/settings/tokens/delete/thisprobablywillnotwork/",
                    data=data,
                    follow_redirects=True,
                )

                self.assertEqual(output.status_code, 404)

    def test_delete_token_invalid_csrf(self):
        """Assert trying to delete a token without a CSRF token fails."""
        session = Session()
        token = models.ApiToken(user=self.user, description="Test token")
        session.add(token)
        session.commit()

        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                data = {"csrf_token": "not a valid token"}

                output = c.post(
                    "/settings/tokens/delete/{}/".format(token.token),
                    data=data,
                    follow_redirects=True,
                )

                self.assertEqual(output.status_code, 400)
                self.assertEqual(
                    1, models.ApiToken.query.filter_by(user=self.user).count()
                )


class NewProjectTests(DatabaseTestCase):
    """Tests for the ``/project/new`` endpoint"""

    def setUp(self):
        """Set up the Flask testing environnment"""
        super(NewProjectTests, self).setUp()
        create_distro(self.session)
        self.app = self.flask_app.test_client()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.session.commit()

    def test_protected_view(self):
        """Assert this view is protected and login is required."""
        output = self.app.get("/project/new", follow_redirects=False)
        self.assertEqual(output.status_code, 302)
        self.assertEqual("/login/", parse.urlparse(output.location).path)

    def test_authenticated_access(self):
        """Assert authenticated users have access to the view."""
        with login_user(self.flask_app, self.user):
            output = self.app.get("/project/new", follow_redirects=False)
            self.assertEqual(output.status_code, 200)

    def test_new_project(self):
        """Assert an authenticated user can create a new project"""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/new", follow_redirects=False)
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b"<h1>Add project</h1>" in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data
                )

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "csrf_token": csrf_token,
                    "name": "repo_manager",
                    "homepage": "https://pypi.python.org/pypi/repo_manager",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                }
                with fml_testing.mock_sends(anitya_schema.ProjectCreated):
                    output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project created</li>" in output.data
                )
                self.assertTrue(b"<h1>Project: repo_manager</h1>" in output.data)
            projects = models.Project.all(self.session, count=True)
            self.assertEqual(projects, 1)

    def test_new_project_no_csrf(self):
        """Assert a missing CSRF token results in an HTTP 400"""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/new", follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                data = {
                    "name": "repo_manager",
                    "homepage": "https://pypi.python.org/pypi/repo_manager",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                }
                output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 400)
                self.assertTrue(b"<h1>Add project</h1>" in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data
                )
            projects = models.Project.all(self.session, count=True)
            self.assertEqual(projects, 0)

    def test_new_project_duplicate(self):
        """Assert duplicate projects result in a HTTP 409"""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/new", follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "csrf_token": csrf_token,
                    "name": "requests",
                    "homepage": "https://pypi.python.org/pypi/requests",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                }
                with fml_testing.mock_sends(anitya_schema.ProjectCreated):
                    output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)

                # Now try to recreate the same project we did above
                output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 409)
                self.assertFalse(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project created</li>" in output.data
                )
                self.assertFalse(b"<h1>Project: repo_manager</h1>" in output.data)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Unable to create project since it already exists.</li>"
                    in output.data
                )
                self.assertTrue(b"<h1>Add project</h1>" in output.data)
            projects = models.Project.query.count()
            self.assertEqual(projects, 1)

    def test_new_project_invalid_homepage(self):
        """Assert a project with an invalid homepage results in an HTTP 400."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/new", follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "name": "fedocal",
                    "homepage": "pypi/fedocal",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                    "csrf_token": csrf_token,
                }
                output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 400)
                self.assertTrue(b"<h1>Add project</h1>" in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data
                )

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_new_project_with_check_release(self, patched):
        output = self.app.get("/project/new", follow_redirects=True)
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/new", follow_redirects=True)

                # check_release off
                data = {
                    "name": "repo_manager",
                    "homepage": "https://pypi.python.org/pypi/repo_manager",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                    "csrf_token": output.data.split(
                        b'name="csrf_token" type="hidden" value="'
                    )[1].split(b'">')[0],
                }
                with fml_testing.mock_sends(anitya_schema.ProjectCreated):
                    output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project created</li>" in output.data
                )
                patched.assert_not_called()

                # check_release_on
                data["name"] += "xxx"
                data["check_release"] = "on"
                with fml_testing.mock_sends(anitya_schema.ProjectCreated):
                    output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project created</li>" in output.data
                )
                patched.assert_called_once_with(mock.ANY, mock.ANY)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_new_project_with_mapping_check_release_error(self, patched):
        """
        Assert that error when checking for new version is handled correctly
        and project with mapping is created.
        """
        patched.side_effect = exceptions.AnityaPluginException("")
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/new", follow_redirects=True)

                # check_release on
                data = {
                    "name": "repo_manager",
                    "homepage": "https://pypi.python.org/pypi/repo_manager",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                    "csrf_token": output.data.split(
                        b'name="csrf_token" type="hidden" value="'
                    )[1].split(b'">')[0],
                    "distro": "Fedora",
                    "package_name": "repo_manager",
                    "check_release": "on",
                }

                with fml_testing.mock_sends(
                    anitya_schema.ProjectCreated, anitya_schema.ProjectMapCreated
                ):
                    output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                patched.assert_called_once_with(mock.ANY, mock.ANY)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Check failed</li>" in output.data
                )

                projects = models.Project.all(self.session)
                self.assertEqual(len(projects), 1)
                self.assertEqual(len(projects[0].package), 1)

    def test_new_project_distro_mapping(self):
        """Assert an authenticated user can create a new project with distro mapping"""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/new", follow_redirects=False)
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b"<h1>Add project</h1>" in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data
                )

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "csrf_token": csrf_token,
                    "name": "repo_manager",
                    "homepage": "https://pypi.python.org/pypi/repo_manager",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                    "distro": "Fedora",
                    "package_name": "repo_manager",
                }
                with fml_testing.mock_sends(
                    anitya_schema.ProjectCreated, anitya_schema.ProjectMapCreated
                ):
                    output = c.post("/project/new", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project created</li>" in output.data
                )
                self.assertTrue(b"<h1>Project: repo_manager</h1>" in output.data)
            projects = models.Project.all(self.session)
            self.assertEqual(len(projects), 1)
            self.assertEqual(len(projects[0].package), 1)


class FlaskTest(DatabaseTestCase):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskTest, self).setUp()

        self.flask_app.config["TESTING"] = True
        self.app = self.flask_app.test_client()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.session.commit()

    def test_index(self):
        """ Test the index function. """
        output = self.app.get("/")
        self.assertEqual(output.status_code, 200)

        expected = b"""
      <h2><span class="glyphicon glyphicon-bullhorn"></span> Announce</h2>
      <p>We monitor upstream releases and broadcast them on
      <a href="https://fedmsg.readthedocs.io/en/stable/">fedmsg</a>, the FEDerated MeSsaGe bus. </p>
      <p>Use <a href="https://apps.fedoraproject.org/notifications">fedmsg
      notifications (FMN)</a>, to set up your own, <em>personalized</em>,
      alerts.</p>"""

        self.assertTrue(expected in output.data)

        expected = b"""
      <h2><span class="glyphicon glyphicon-search"></span> Search</h2>
      <p>Currently 0 projects are being monitored by Anitya.
      Your project of interest might be there, or not. To check it
      <a href="/projects/">browse the list of all projects</a>
      or simply search for them!</p>"""

        self.assertTrue(expected in output.data)

    def test_about(self):
        """Assert the legacy about endpoint redirects to documentation"""
        output = self.app.get("/about")
        self.assertEqual(output.status_code, 302)
        self.assertEqual(
            output.headers["Location"], "http://localhost/static/docs/index.html"
        )

    def test_fedmsg(self):
        """Assert the legacy fedmsg endpoint redirects to documentation"""
        output = self.app.get("/fedmsg")
        self.assertEqual(output.status_code, 302)
        self.assertEqual(
            output.headers["Location"], "http://localhost/static/docs/user-guide.html"
        )

    def test_project(self):
        """ Test the project function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get("/project/1/")
        self.assertEqual(output.status_code, 200)

        expected = b"""
            <p><a property="doap:homepage" href="https://www.geany.org/"
               target="_blank" rel="noopener noreferrer">https://www.geany.org/
             </a><p>"""

        self.assertTrue(expected in output.data)

        output = self.app.get("/project/10/")
        self.assertEqual(output.status_code, 404)

    def test_projects(self):
        """ Test the projects function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get("/projects/")
        self.assertEqual(output.status_code, 200)

        expected = b"""
                <a href="https://www.geany.org/" target="_blank" rel="noopener noreferrer">
                  https://www.geany.org/
                </a>"""
        self.assertTrue(expected in output.data)

        expected = (
            b'\n                <a href="https://fedorahosted.org/r2spec/" target="_blank"'
            b' rel="noopener noreferrer">\n                  '
            b"https://fedorahosted.org/r2spec/\n                </a>"
        )
        self.assertTrue(expected in output.data)

        expected = b"""
                <a href="https://subsurface-divelog.org/" target="_blank" rel="noopener noreferrer">
                  https://subsurface-divelog.org/
                </a>"""
        self.assertTrue(expected in output.data)

        self.assertEqual(output.data.count(b'<a href="/project/'), 3)

        output = self.app.get("/projects/?page=ab")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/'), 3)

    def test_distros(self):
        """ Test the distros function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get("/distros/")
        self.assertEqual(output.status_code, 200)

        expected = b"Here is the list of all the distributions"
        self.assertTrue(expected in output.data)

        output = self.app.get("/distros/?page=ab")
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)

    def test_distro(self):
        """ Test the distro function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get("/distro/Fedora/")
        self.assertEqual(output.status_code, 200)

        expected = b"""
  <blockquote>
      Oups this is embarrassing, it seems that no projects are being
      monitored currently.
  </blockquote>"""
        self.assertTrue(expected in output.data)
        self.assertTrue(
            b'form action="/distro/Fedora/search/" role="form" '
            b'class="form-inline">' in output.data
        )
        self.assertTrue(b"<h1>Projects of Fedora monitored</h1>" in output.data)

        output = self.app.get("/distro/Fedora/?page=ab")
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)
        self.assertTrue(
            b'form action="/distro/Fedora/search/" role="form" '
            b'class="form-inline">' in output.data
        )
        self.assertTrue(b"<h1>Projects of Fedora monitored</h1>" in output.data)

    def test_distro_projects_search(self):
        """ Test the distro_projects_search function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get("/distro/Fedora/search/gua")
        self.assertEqual(output.status_code, 200)

        expected = b"""
    <blockquote>
        Oups this is embarrassing, it seems that no projects are being
        monitored currently.
        <p><a href="/project/new?name=gua">Click Here</a> to add this project instead. </p>
    </blockquote>"""
        self.assertIn(expected, output.data)
        self.assertIn(b'form action="/distro/Fedora/search/">', output.data)
        self.assertIn(b"<h1>Search projects in Fedora</h1>", output.data)

    def test_distro_projects_search_pattern(self):
        """
        Assert that `anitya.ui.distro_project_search` returns
        correct project when pattern is used.
        """
        create_distro(self.session)
        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/distro/Fedora/search/g")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)

    def test_distro_projects_search_incorrect(self):
        """
        Assert that `anitya.ui.distro_project_search` returns
        correct project when incorrect page is set.
        """
        create_distro(self.session)
        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/distro/Fedora/search/?page=ab")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)

    def test_distro_projects_search_exact(self):
        """
        Assert that `anitya.ui.distro_project_search` returns
        correct project when exact argument is set.
        """
        create_distro(self.session)
        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/distro/Fedora/search/?exact=1")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)

    def test_distro_projects_search_flash(self):
        """
        Assert that `anitya.ui.distro_project_search` shows
        flash message when redirect happens.
        """
        create_distro(self.session)
        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/distro/Fedora/search/geany*", follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        expected = (
            b'<li class="list-group-item list-group-item-default">'
            b"Only one result matching with an "
            b"exact match, redirecting</li>"
        )
        self.assertTrue(expected in output.data)

    def test_projects_search(self):
        """ Test the projects_search function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get("/projects/search/g")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)

        output = self.app.get("/projects/search/g*")
        self.assertEqual(output.status_code, 200)
        expected = b"""
                  <a href="https://www.geany.org/" target="_blank" rel="noopener noreferrer">
                    https://www.geany.org/
                  </a>"""
        self.assertTrue(expected in output.data)

        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)

        output = self.app.get("/projects/search/?page=ab")
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)
        self.assertEqual(output.data.count(b'<a href="/project/'), 3)

        output = self.app.get("/projects/search/?exact=1")
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)
        self.assertEqual(output.data.count(b'<a href="/project/'), 3)

        output = self.app.get("/projects/search/geany*", follow_redirects=True)
        self.assertEqual(output.status_code, 200)

        expected = (
            b'<li class="list-group-item list-group-item-default">'
            b"Only one result matching with an "
            b"exact match, redirecting</li>"
        )
        self.assertTrue(expected in output.data)

    def test_logout_redirect(self):
        """Assert the logout logouts user"""
        with login_user(self.flask_app, self.user):
            output = self.app.get("/logout")
            self.assertEqual(output.status_code, 302)
            self.assertEqual(output.headers["Location"], "http://localhost/")

    def test_logout(self):
        """Assert the logout logouts user"""
        login_user(self.flask_app, self.user)
        output = self.app.get("/logout", follow_redirects=True)
        output = self.app.get("/project/new", follow_redirects=False)
        self.assertEqual(output.status_code, 302)
        self.assertEqual("/login/", parse.urlparse(output.location).path)

    def test_projects_search_by_name(self):
        """ Test the project_name function. """
        create_project(self.session)

        output = self.app.get("/project/geany")
        self.assertIn(output.status_code, [301, 308])
        self.assertEqual(output.headers["Location"], "http://localhost/project/geany/")

    def test_projects_search_by_name_slash(self):
        """ Assert that `anitya.ui.project_name` renders
        page with correct project. """
        create_project(self.session)

        output = self.app.get("/project/geany/")
        self.assertEqual(output.status_code, 200)
        expected = b"<h1>Project: geany</h1>"
        self.assertTrue(expected in output.data)

    def test_projects_search_by_name_incorrect_page(self):
        """
        Assert that `anitya.ui.project_name` automatically
        converts incorrect page value.
        """
        create_project(self.session)
        expected = b"<h1>Project: geany</h1>"

        output = self.app.get("/project/geany/?page=ab")
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)

    def test_projects_search_by_name_pattern(self):
        """
        Assert that `anitya.ui.project_name` renders correct
        project if pattern name is provided.
        """
        create_project(self.session)
        project = models.Project(
            name="geany_project",
            homepage="https://example.com/geany_project",
            backend="PyPI",
            ecosystem_name="pypi",
        )
        self.session.add(project)
        self.session.commit()

        output = self.app.get("/project/geany*/")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/'), 2)

    def test_projects_updated(self):
        """
        Assert that `anitya.ui.project_updated` renders
        correct projects.
        """
        create_project(self.session)

        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        output = self.app.get("/projects/updates/")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)

    def test_projects_updated_incorrect_page(self):
        """
        Assert that `anitya.ui.project_updated` automatically
        changes incorrect page.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        output = self.app.get("/projects/updates/?page=ab")
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)

    def test_projects_updated_incorrect_status(self):
        """
        Assert that `anitya.ui.project_updated` shows flash message
        when incorrect status is provided.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        output = self.app.get("/projects/updates/status")
        expected = (
            b'<li class="list-group-item list-group-item-warning">'
            b"status is invalid, you should use one of: "
            b"new, updated, failed, never_updated, odd; using default: "
            b'`updated`</li><li class="list-group-item list-group-item-default">'
            b"Returning all the projects regardless of how/if their version was "
            b"retrieved correctly</li>"
        )
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)


class EditProjectTests(DatabaseTestCase):
    def setUp(self):
        """Set up the Flask testing environnment"""
        super(EditProjectTests, self).setUp()
        self.app = self.flask_app.test_client()
        # Make a user to login with
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.session.commit()
        create_distro(self.session)
        create_project(self.session)

    def test_protected_view(self):
        """Assert this view is protected and login is required."""
        with self.flask_app.test_client() as client:
            output = client.get("/project/1/edit", follow_redirects=False)
            self.assertEqual(output.status_code, 302)
            self.assertEqual("/login/", parse.urlparse(output.location).path)

    def test_authenticated_access(self):
        """Assert authenticated users have access to the view."""
        with login_user(self.flask_app, self.user):
            output = self.app.get("/project/1/edit", follow_redirects=False)
            self.assertEqual(output.status_code, 200)

    def test_non_existing_project(self):
        """Assert trying to edit a project that doesn't exist returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.app.get("/project/idonotexist/edit", follow_redirects=False)
            self.assertEqual(output.status_code, 404)

    def test_no_csrf_token(self):
        """Assert trying to edit a project without a CSRF token results in no change."""
        with login_user(self.flask_app, self.user):
            data = {
                "name": "repo_manager",
                "homepage": "https://pypi.python.org/pypi/repo_manager",
                "backend": "PyPI",
                "version_scheme": "RPM",
            }

            output = self.app.post("/project/1/edit", data=data)
            self.assertEqual(200, output.status_code)
            self.assertEqual("geany", models.Project.query.get(1).name)

    def test_edit_project(self):
        """ Test the edit_project function. """
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/1/edit", follow_redirects=False)
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b"<h1>Edit project</h1>" in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data
                )

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "name": "repo_manager",
                    "homepage": "https://pypi.python.org/pypi/repo_manager",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                    "csrf_token": csrf_token,
                }

                with fml_testing.mock_sends(anitya_schema.ProjectEdited):
                    output = c.post("/project/1/edit", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project edited</li>" in output.data
                )
                self.assertTrue(b"<h1>Project: repo_manager</h1>" in output.data)

    def test_edit_project_no_change(self):
        """ Test the edit_project function. """
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/1/edit", follow_redirects=False)
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b"<h1>Edit project</h1>" in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data
                )

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "csrf_token": csrf_token,
                    "name": "geany",
                    "homepage": "https://www.geany.org/",
                    "backend": "custom",
                    "version_scheme": "RPM",
                }

                output = c.post("/project/1/edit", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project edited - No changes were made</li>" in output.data
                )

    def test_edit_to_duplicate_project(self):
        """Assert trying to edit a project to make a duplicate fails."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/1/edit", follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "name": "R2spec",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "backend": "folder",
                    "version_scheme": "RPM",
                    "csrf_token": csrf_token,
                }

                with fml_testing.mock_sends(anitya_schema.ProjectEdited):
                    output = c.post("/project/1/edit", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-warning">'
                    b"Could not edit this project. Is there "
                    b"already a project with these name and homepage?</li>"
                    in output.data
                )
                self.assertTrue(b"<h1>Project: geany</h1>" in output.data)
                self.assertEqual("geany", models.Project.query.get(1).name)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_with_check_release(self, patched):
        """Assert when ``check_release='on'`` it checks the project's release."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/1/edit", follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "name": "repo_manager",
                    "homepage": "https://pypi.python.org/pypi/repo_manager",
                    "backend": "PyPI",
                    "version_scheme": "RPM",
                    "csrf_token": csrf_token,
                    "check_release": "on",
                }
                with fml_testing.mock_sends(anitya_schema.ProjectEdited):
                    output = c.post("/project/1/edit", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Project edited</li>" in output.data
                )
                patched.assert_called_once_with(mock.ANY, mock.ANY)


class MapProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.ui.map_project` view."""

    def setUp(self):
        super(MapProjectTests, self).setUp()
        create_distro(self.session)
        create_project(self.session)
        self.client = self.flask_app.test_client()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.session.commit()

    def test_protected_view(self):
        """Assert this view is protected and login is required."""
        output = self.client.get("/project/1/map", follow_redirects=False)
        self.assertEqual(output.status_code, 302)
        self.assertEqual("/login/", parse.urlparse(output.location).path)

    def test_authenticated_access(self):
        """Assert authenticated users have access to the view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/project/1/map", follow_redirects=False)
            self.assertEqual(output.status_code, 200)

    def test_non_existing_project(self):
        """Assert trying to edit a project that doesn't exist returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/project/idonotexist/map", follow_redirects=False)
            self.assertEqual(output.status_code, 404)

    def test_no_csrf_token(self):
        """Assert trying to edit a project without a CSRF token results in no change."""
        with login_user(self.flask_app, self.user):
            data = {"package_name": "geany", "distro": "CentOS"}
            output = self.client.post(
                "/project/1/map", data=data, follow_redirects=False
            )
            self.assertEqual(output.status_code, 200)
            self.assertEqual(0, models.Packages.query.count())

    def test_map_project(self):
        """Assert projects can be mapped to distributions."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/1/map")
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b"<h1>Project: geany</h1>" in output.data)
                self.assertTrue(
                    b'<td><label for="distro">Distribution</label></td>' in output.data
                )

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "package_name": "geany",
                    "distro": "Fedora",
                    "csrf_token": csrf_token,
                }

                with fml_testing.mock_sends(anitya_schema.ProjectMapCreated):
                    output = c.post("/project/1/map", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b"Mapping added</li>" in output.data
                )
                self.assertTrue(b"<h1>Project: geany</h1>" in output.data)
                self.assertEqual(1, models.Packages.query.count())

    def test_map_same_distro(self):
        """
        Assert that projects can't have two mappings with the same name to the
        same distribution.
        """
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get("/project/1/map")
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "package_name": "geany",
                    "distro": "Fedora",
                    "csrf_token": csrf_token,
                }

                with fml_testing.mock_sends(anitya_schema.ProjectMapCreated):
                    output = c.post("/project/1/map", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                output = c.post("/project/1/map", data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-danger">'
                    b"Could not edit the mapping of geany on "
                    b"Fedora, there is already a package geany on Fedora "
                    b'as part of the project <a href="/project/1/">geany'
                    b"</a>.</li>" in output.data
                )
                self.assertTrue(b"<h1>Project: geany</h1>" in output.data)


class EditProjectMappingTests(DatabaseTestCase):
    """Tests for the :func:`anitya.ui.edit_project_mapping` view."""

    def setUp(self):
        super(EditProjectMappingTests, self).setUp()

        # Set up a mapping to edit
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.distro1 = models.Distro(name="CentOS")
        self.distro2 = models.Distro(name="Fedora")
        self.project = models.Project(
            name="python_project",
            homepage="https://example.com/python_project",
            backend="PyPI",
            ecosystem_name="pypi",
        )
        self.package = models.Packages(
            package_name="python_project",
            distro_name=self.distro1.name,
            project=self.project,
        )
        session.add_all(
            [self.user, self.distro1, self.distro2, self.project, self.package]
        )
        session.commit()
        self.client = self.flask_app.test_client()

    def test_edit_project_mapping_package_name(self):
        """Assert a project's package name can be edited."""
        with login_user(self.flask_app, self.user):
            pre_edit_output = self.client.get("/project/1/map/1")
            csrf_token = pre_edit_output.data.split(
                b'name="csrf_token" type="hidden" value="'
            )[1].split(b'">')[0]
            data = {
                "package_name": "Python Project",
                "distro": self.distro1.name,
                "csrf_token": csrf_token,
            }
            with fml_testing.mock_sends(anitya_schema.ProjectMapEdited):
                output = self.client.post(
                    "/project/1/map/1", data=data, follow_redirects=True
                )

            self.assertEqual(pre_edit_output.status_code, 200)
            self.assertEqual(output.status_code, 200)

            packages = models.Packages.query.all()
            self.assertEqual(1, len(packages))
            self.assertEqual("Python Project", packages[0].package_name)

    def test_edit_project_mapping_distro(self):
        """Assert a project's package distro can be edited."""
        with login_user(self.flask_app, self.user):
            pre_edit_output = self.client.get("/project/1/map/1")
            csrf_token = pre_edit_output.data.split(
                b'name="csrf_token" type="hidden" value="'
            )[1].split(b'">')[0]
            data = {
                "package_name": self.project.name,
                "distro": self.distro2.name,
                "csrf_token": csrf_token,
            }
            with fml_testing.mock_sends(anitya_schema.ProjectMapEdited):
                output = self.client.post(
                    "/project/1/map/1", data=data, follow_redirects=True
                )

            self.assertEqual(pre_edit_output.status_code, 200)
            self.assertEqual(output.status_code, 200)

            packages = models.Packages.query.all()
            self.assertEqual(1, len(packages))
            self.assertEqual(self.distro2.name, packages[0].distro_name)

    def test_clashing_package_name(self):
        """Assert two projects can't map to the same package name in a distro."""
        # Set up a package to clash with.
        session = Session()
        best_project = models.Project(
            name="best_project",
            homepage="https://example.com/best_project",
            backend="PyPI",
            ecosystem_name="pypi",
        )
        best_package = models.Packages(
            package_name="best_project",
            distro_name=self.distro1.name,
            project=best_project,
        )
        session.add_all([best_project, best_package])
        session.commit()

        with login_user(self.flask_app, self.user):
            pre_edit_output = self.client.get("/project/1/map/1")
            csrf_token = pre_edit_output.data.split(
                b'name="csrf_token" type="hidden" value="'
            )[1].split(b'">')[0]
            data = {
                "package_name": self.project.name,
                "distro": self.distro1.name,
                "csrf_token": csrf_token,
            }
            output = self.client.post(
                "/project/1/map/1", data=data, follow_redirects=True
            )

            self.assertEqual(output.status_code, 200)
            self.assertEqual(2, models.Packages.query.count())
            self.assertEqual(
                1, models.Packages.query.filter_by(package_name="best_project").count()
            )
            self.assertEqual(
                1,
                models.Packages.query.filter_by(package_name="python_project").count(),
            )
            self.assertTrue(b"Could not edit the mapping" in output.data)

    def test_invalid_map_id(self):
        """Assert trying to edit a mapping with an invalid package ID returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/project/1/map/42", data={})
            self.assertEqual(output.status_code, 404)

    def test_invalid_project_id(self):
        """Assert trying to edit a mapping with an invalid project ID returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/project/42/map/1", data={})
            self.assertEqual(output.status_code, 404)

    def test_anitya_exception(self):
        """Assert handling of exception."""
        with mock.patch.object(
            self.session, "flush", mock.Mock(side_effect=[SQLAlchemyError(), None])
        ):
            with login_user(self.flask_app, self.user):
                pre_edit_output = self.client.get("/project/1/map/1")
                csrf_token = pre_edit_output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {
                    "package_name": self.project.name,
                    "distro": self.distro2.name,
                    "csrf_token": csrf_token,
                }
                output = self.client.post(
                    "/project/1/map/1", data=data, follow_redirects=True
                )

                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b"Could not add the mapping of python_project to Fedora, "
                    b"please inform an admin." in output.data
                )


class AddDistroTests(DatabaseTestCase):
    """Tests for the :func:`anitya.admin.add_distro` view function."""

    def setUp(self):
        super(AddDistroTests, self).setUp()

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

        self.client = self.flask_app.test_client()

    def test_no_csrf_token(self):
        """Assert submitting without a CSRF token, no change is made."""
        with login_user(self.flask_app, self.user):
            output = self.client.post("/distro/add", data={"name": "Fedora"})
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.count())

    def test_invalid_csrf_token(self):
        """Assert submitting with an invalid CSRF token, no change is made."""
        with login_user(self.flask_app, self.user):
            output = self.client.post(
                "/distro/add", data={"csrf_token": "abc", "name": "Fedora"}
            )
            self.assertEqual(200, output.status_code)
            self.assertEqual(0, models.Distro.query.count())

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_add_distro(self, mock_method):
        """Assert admins can add distributions."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/distro/add")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"name": "Fedora", "csrf_token": csrf_token}

            output = self.client.post("/distro/add", data=data, follow_redirects=True)

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"Distribution added" in output.data)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_duplicate_distro(self, mock_method):
        """Assert trying to create a duplicate distribution results in HTTP 409."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/distro/add")
            csrf_token = output.data.split(b'name="csrf_token" type="hidden" value="')[
                1
            ].split(b'">')[0]
            data = {"name": "Fedora", "csrf_token": csrf_token}

            create_output = self.client.post(
                "/distro/add", data=data, follow_redirects=True
            )
            self.assertEqual(200, output.status_code)
            dup_output = self.client.post(
                "/distro/add", data=data, follow_redirects=True
            )

            self.assertEqual(200, output.status_code)
            self.assertTrue(b"Distribution added" in create_output.data)
            self.assertTrue(b"Could not add this distro" in dup_output.data)


class FlagProjecTests(DatabaseTestCase):
    """Tests for the :func:`anitya.ui.flag_project` view."""

    def setUp(self):
        super(FlagProjecTests, self).setUp()

        create_project(self.session)
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        self.session.add(self.user)
        self.session.add(user_social_auth)
        self.session.commit()
        self.client = self.flask_app.test_client()

    def test_flag_project(self):
        """ Assert flaging project."""
        with login_user(self.flask_app, self.user):
            pre_edit_output = self.client.get("/project/1/flag")
            csrf_token = pre_edit_output.data.split(
                b'name="csrf_token" type="hidden" value="'
            )[1].split(b'">')[0]
            data = {"reason": "Unfit for humanity", "csrf_token": csrf_token}
            with fml_testing.mock_sends(anitya_schema.ProjectFlag):
                output = self.client.post(
                    "/project/1/flag", data=data, follow_redirects=True
                )

            self.assertEqual(output.status_code, 200)
            flags = self.session.query(models.ProjectFlag).all()
            self.assertEqual(len(flags), 1)
            self.assertEqual(flags[0].project_id, 1)

    def test_invalid_project(self):
        """ Assert abort with invalid project."""
        with login_user(self.flask_app, self.user):
            output = self.client.get("/project/99/flag")
            self.assertEqual(output.status_code, 404)

    def test_anitya_exception(self):
        """Assert handling of exception."""
        with mock.patch.object(
            self.session, "flush", mock.Mock(side_effect=[SQLAlchemyError(), None])
        ):
            with login_user(self.flask_app, self.user):
                pre_edit_output = self.client.get("/project/1/flag")
                csrf_token = pre_edit_output.data.split(
                    b'name="csrf_token" type="hidden" value="'
                )[1].split(b'">')[0]
                data = {"reason": "Unfit for humanity", "csrf_token": csrf_token}
                with fml_testing.mock_sends():
                    output = self.client.post(
                        "/project/1/flag", data=data, follow_redirects=True
                    )

                self.assertEqual(output.status_code, 200)
                self.assertTrue(b"Could not flag this project." in output.data)


class UiTests(DatabaseTestCase):
    """Tests for the functions in `anitya.ui` class."""

    def test_format_examples(self):
        """ Assert format examples testing. """
        output = ui.format_examples(["http://example.com"])

        self.assertEqual(output, "<a href='http://example.com'>http://example.com</a> ")

    def test_format_examples_none(self):
        """ Assert format examples testing. """
        output = ui.format_examples(None)

        self.assertEqual(output, "")
