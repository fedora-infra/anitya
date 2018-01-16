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
anitya tests for the flask application.
'''

from six.moves.urllib import parse
import mock

from anitya.db import models, Session
from anitya.tests.base import (AnityaTestCase, DatabaseTestCase, create_distro, create_project,
                               login_user)


class ShutdownSessionTests(AnityaTestCase):
    """Tests for the :func:`anitya.app.shutdown_session` function."""

    def test_session_removed_post_request(self):
        """Assert that the session is cleaned up after a request."""
        session = Session()
        self.assertTrue(session is Session())
        app = self.flask_app.test_client()
        app.get('/about', follow_redirects=False)
        self.assertFalse(session is Session())


class SettingsTests(DatabaseTestCase):

    def setUp(self):
        """Set up the Flask testing environnment"""
        super(SettingsTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        session.add(self.user)
        session.commit()

    def test_login_required(self):
        """Assert this view is protected and login is required."""
        output = self.app.get('/settings/', follow_redirects=False)
        self.assertEqual(output.status_code, 302)
        self.assertEqual('/login/', parse.urlparse(output.location).path)

    def test_new_token(self):
        """Assert a user can create a new API token."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/settings/', follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {'csrf_token': csrf_token, 'description': 'Test token'}

                output = c.post('/settings/tokens/new', data=data, follow_redirects=True)

                self.assertEqual(output.status_code, 200)
                self.assertTrue(b'Test token' in output.data)

    def test_new_token_bad_csrf(self):
        """Assert a valid CSRF token is required to make a token."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                data = {'csrf_token': 'no good?', 'description': 'Test token'}

                output = c.post('/settings/tokens/new', data=data, follow_redirects=True)

                self.assertEqual(output.status_code, 400)
                self.assertFalse(b'Test token' in output.data)

    def test_delete_token(self):
        """Assert a user can delete an API token."""
        session = Session()
        token = models.ApiToken(user=self.user, description='Test token')
        session.add(token)
        session.commit()

        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/settings/', follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(b'Test token' in output.data)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {'csrf_token': csrf_token}

                output = c.post('/settings/tokens/delete/{}/'.format(token.token),
                                data=data, follow_redirects=True)

                self.assertEqual(output.status_code, 200)
                self.assertFalse(b'Test token' in output.data)
                self.assertEqual(0, models.ApiToken.query.filter_by(user=self.user).count())

    def test_delete_invalid_token(self):
        """Assert trying to delete an invalid token fails."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/settings/', follow_redirects=False)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {'csrf_token': csrf_token}

                output = c.post('/settings/tokens/delete/thisprobablywillnotwork/',
                                data=data, follow_redirects=True)

                self.assertEqual(output.status_code, 404)

    def test_delete_token_invalid_csrf(self):
        """Assert trying to delete a token without a CSRF token fails."""
        session = Session()
        token = models.ApiToken(user=self.user, description='Test token')
        session.add(token)
        session.commit()

        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                data = {'csrf_token': 'not a valid token'}

                output = c.post('/settings/tokens/delete/{}/'.format(token.token),
                                data=data, follow_redirects=True)

                self.assertEqual(output.status_code, 400)
                self.assertEqual(1, models.ApiToken.query.filter_by(user=self.user).count())


class NewProjectTests(DatabaseTestCase):
    """Tests for the ``/project/new`` endpoint"""

    def setUp(self):
        """Set up the Flask testing environnment"""
        super(NewProjectTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        session.add(self.user)
        session.commit()

    def test_protected_view(self):
        """Assert this view is protected and login is required."""
        output = self.app.get('/project/new', follow_redirects=False)
        self.assertEqual(output.status_code, 302)
        self.assertEqual('/login/', parse.urlparse(output.location).path)

    def test_authenticated_access(self):
        """Assert authenticated users have access to the view."""
        with login_user(self.flask_app, self.user):
            output = self.app.get('/project/new', follow_redirects=False)
            self.assertEqual(output.status_code, 200)

    def test_new_project(self):
        """Assert an authenticated user can create a new project"""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/new', follow_redirects=False)
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b'<h1>Add project</h1>' in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data)

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'csrf_token': csrf_token,
                    'name': 'repo_manager',
                    'homepage': 'https://pypi.python.org/pypi/repo_manager',
                    'backend': 'PyPI',
                }
                output = c.post(
                    '/project/new', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Project created</li>' in output.data)
                self.assertTrue(
                    b'<h1>Project: repo_manager</h1>' in output.data)
            projects = models.Project.all(self.session, count=True)
            self.assertEqual(projects, 1)

    def test_new_project_no_csrf(self):
        """Assert a missing CSRF token results in an HTTP 400"""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/new', follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                data = {
                    'name': 'repo_manager',
                    'homepage': 'https://pypi.python.org/pypi/repo_manager',
                    'backend': 'PyPI',
                }
                output = c.post(
                    '/project/new', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 400)
                self.assertTrue(b'<h1>Add project</h1>' in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data)
            projects = models.Project.all(self.session, count=True)
            self.assertEqual(projects, 0)

    def test_new_project_duplicate(self):
        """Assert duplicate projects result in a HTTP 409"""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/new', follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'csrf_token': csrf_token,
                    'name': 'requests',
                    'homepage': 'https://pypi.python.org/pypi/requests',
                    'backend': 'PyPI',
                }
                output = c.post(
                    '/project/new', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)

                # Now try to recreate the same project we did above
                output = c.post(
                    '/project/new', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 409)
                self.assertFalse(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Project created</li>' in output.data)
                self.assertFalse(
                    b'<h1>Project: repo_manager</h1>' in output.data)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Unable to create project since it already exists.</li>'
                    in output.data)
                self.assertTrue(b'<h1>Add project</h1>' in output.data)
            projects = models.Project.query.count()
            self.assertEqual(projects, 1)

    def test_new_project_invalid_homepage(self):
        """Assert a project with an invalid homepage results in an HTTP 400."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/new', follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'name': 'fedocal',
                    'homepage': 'pypi/fedocal',
                    'backend': 'PyPI',
                    'csrf_token': csrf_token,
                }
                output = c.post(
                    '/project/new', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 400)
                self.assertTrue(b'<h1>Add project</h1>' in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data)

    @mock.patch('anitya.lib.utilities.check_project_release')
    def test_new_project_with_check_release(self, patched):
        output = self.app.get('/project/new', follow_redirects=True)
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/new', follow_redirects=True)

                # check_release off
                data = {
                    'name': 'repo_manager',
                    'homepage': 'https://pypi.python.org/pypi/repo_manager',
                    'backend': 'PyPI',
                    'csrf_token': output.data.split(
                        b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0],
                }
                output = c.post(
                    '/project/new', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Project created</li>' in output.data)
                patched.assert_not_called()

                # check_release_on
                data['name'] += 'xxx'
                data['check_release'] = 'on'
                output = c.post(
                    '/project/new', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Project created</li>' in output.data)
                patched.assert_called_once_with(mock.ANY, mock.ANY)


class FlaskTest(DatabaseTestCase):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskTest, self).setUp()

        self.flask_app.config['TESTING'] = True
        self.app = self.flask_app.test_client()

    def test_index(self):
        """ Test the index function. """
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)

        expected = b"""
      <h2><span class="glyphicon glyphicon-bullhorn"></span> Announce</h2>
      <p>We monitor upstream releases and broadcast them on
      <a href="http://fedmsg.com">fedmsg</a>, the FEDerated MeSsaGe bus. </p>
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
        output = self.app.get('/about')
        self.assertEqual(output.status_code, 302)
        self.assertEqual(
            output.headers['Location'],
            'http://localhost/static/docs/index.html'
        )

    def test_fedmsg(self):
        """Assert the legacy fedmsg endpoint redirects to documentation"""
        output = self.app.get('/fedmsg')
        self.assertEqual(output.status_code, 302)
        self.assertEqual(
            output.headers['Location'],
            'http://localhost/static/docs/user-guide.html'
        )

    def test_project(self):
        """ Test the project function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/project/1/')
        self.assertEqual(output.status_code, 200)

        expected = b"""
            <p><a property="doap:homepage" href="http://www.geany.org/"
               target="_blank" rel="noopener noreferrer">http://www.geany.org/
             </a><p>"""

        self.assertTrue(expected in output.data)

        output = self.app.get('/project/10/')
        self.assertEqual(output.status_code, 404)

    def test_projects(self):
        """ Test the projects function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/projects/')
        self.assertEqual(output.status_code, 200)

        expected = b"""
                <a href="http://www.geany.org/" target="_blank" rel="noopener noreferrer">
                  http://www.geany.org/
                </a>"""
        self.assertTrue(expected in output.data)

        expected = (
            b'\n                <a href="https://fedorahosted.org/r2spec/" target="_blank"'
            b' rel="noopener noreferrer">\n                  '
            b'https://fedorahosted.org/r2spec/\n                </a>'
        )
        self.assertTrue(expected in output.data)

        expected = b"""
                <a href="http://subsurface.hohndel.org/" target="_blank" rel="noopener noreferrer">
                  http://subsurface.hohndel.org/
                </a>"""
        self.assertTrue(expected in output.data)

        self.assertEqual(output.data.count(b'<a href="/project/'), 3)

        output = self.app.get('/projects/?page=ab')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/'), 3)

    def test_distros(self):
        """ Test the distros function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/distros/')
        self.assertEqual(output.status_code, 200)

        expected = b"Here is the list of all the distributions"
        self.assertTrue(expected in output.data)

        output = self.app.get('/distros/?page=ab')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)

    def test_distro(self):
        """ Test the distro function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/distro/Fedora/')
        self.assertEqual(output.status_code, 200)

        expected = b"""
  <blockquote>
      Oups this is embarrassing, it seems that no projects are being
      monitored currently.
  </blockquote>"""
        self.assertTrue(expected in output.data)
        self.assertTrue(
            b'form action="/distro/Fedora/search/" role="form" '
            b'class="form-inline">' in output.data)
        self.assertTrue(
            b'<h1>Projects of Fedora monitored</h1>' in output.data)

        output = self.app.get('/distro/Fedora/?page=ab')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)
        self.assertTrue(
            b'form action="/distro/Fedora/search/" role="form" '
            b'class="form-inline">' in output.data)
        self.assertTrue(
            b'<h1>Projects of Fedora monitored</h1>' in output.data)

    def test_distro_projects_search(self):
        """ Test the distro_projects_search function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/distro/Fedora/search/gua')
        self.assertEqual(output.status_code, 200)

        expected = b"""
    <blockquote>
        Oups this is embarrassing, it seems that no projects are being
        monitored currently.
        <p><a href="/project/new?name=gua">Click Here</a> to add this project instead. </p>
    </blockquote>"""
        self.assertTrue(expected in output.data)
        self.assertTrue(
            b'form action="/distro/Fedora/search/" role="form">'
            in output.data)
        self.assertTrue(
            b'<h1>Search projects in Fedora</h1>' in output.data)

    def test_projects_search(self):
        """ Test the projects_search function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/projects/search/g')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count(b'<a href="/project/'), 1)

        output = self.app.get('/projects/search/g*')
        self.assertEqual(output.status_code, 200)
        expected = b"""
                  <a href="http://www.geany.org/" target="_blank" rel="noopener noreferrer">
                    http://www.geany.org/
                  </a>"""
        self.assertTrue(expected in output.data)

        self.assertEqual(output.data.count(b'<a href="/project/'), 1)

        output = self.app.get('/projects/search/?page=ab')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)
        self.assertEqual(output.data.count(b'<a href="/project/'), 3)

        output = self.app.get(
            '/projects/search/geany*', follow_redirects=True)
        self.assertEqual(output.status_code, 200)

        expected = b'<li class="list-group-item list-group-item-default">' \
            b'Only one result matching with an ' \
            b'exact match, redirecting</li>'
        self.assertTrue(expected in output.data)


class EditProjectTests(DatabaseTestCase):

    def setUp(self):
        """Set up the Flask testing environnment"""
        super(EditProjectTests, self).setUp()
        self.app = self.flask_app.test_client()
        # Make a user to login with
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        session.add(self.user)
        session.commit()
        create_distro(self.session)
        create_project(self.session)

    def test_protected_view(self):
        """Assert this view is protected and login is required."""
        with self.flask_app.test_client() as client:
            output = client.get('/project/1/edit', follow_redirects=False)
            self.assertEqual(output.status_code, 302)
            self.assertEqual('/login/', parse.urlparse(output.location).path)

    def test_authenticated_access(self):
        """Assert authenticated users have access to the view."""
        with login_user(self.flask_app, self.user):
            output = self.app.get('/project/1/edit', follow_redirects=False)
            self.assertEqual(output.status_code, 200)

    def test_non_existing_project(self):
        """Assert trying to edit a project that doesn't exist returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.app.get('/project/idonotexist/edit', follow_redirects=False)
            self.assertEqual(output.status_code, 404)

    def test_no_csrf_token(self):
        """Assert trying to edit a project without a CSRF token results in no change."""
        with login_user(self.flask_app, self.user):
            data = {
                'name': 'repo_manager',
                'homepage': 'https://pypi.python.org/pypi/repo_manager',
                'backend': 'PyPI',
            }

            output = self.app.post('/project/1/edit', data=data)
            self.assertEqual(200, output.status_code)
            self.assertEqual('geany', models.Project.query.get(1).name)

    def test_edit_project(self):
        """ Test the edit_project function. """
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/1/edit', follow_redirects=False)
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b'<h1>Edit project</h1>' in output.data)
                self.assertTrue(
                    b'<td><label for="regex">Regex</label></td>' in output.data)

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'name': 'repo_manager',
                    'homepage': 'https://pypi.python.org/pypi/repo_manager',
                    'backend': 'PyPI',
                    'csrf_token': csrf_token,
                }

                output = c.post(
                    '/project/1/edit', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Project edited</li>' in output.data)
                self.assertTrue(
                    b'<h1>Project: repo_manager</h1>' in output.data)

    def test_edit_to_duplicate_project(self):
        """Assert trying to edit a project to make a duplicate fails."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/1/edit', follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'name': 'R2spec',
                    'homepage': 'https://fedorahosted.org/r2spec/',
                    'backend': 'folder',
                    'csrf_token': csrf_token,
                }

                output = c.post(
                    '/project/1/edit', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-warning">'
                    b'Could not edit this project. Is there '
                    b'already a project with these name and homepage?</li>'
                    in output.data)
                self.assertTrue(b'<h1>Project: geany</h1>' in output.data)
                self.assertEqual('geany', models.Project.query.get(1).name)

    @mock.patch('anitya.lib.utilities.check_project_release')
    def test_with_check_release(self, patched):
        """Assert when ``check_release='on'`` it checks the project's release."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/1/edit', follow_redirects=False)
                self.assertEqual(output.status_code, 200)
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'name': 'repo_manager',
                    'homepage': 'https://pypi.python.org/pypi/repo_manager',
                    'backend': 'PyPI',
                    'csrf_token': csrf_token,
                    'check_release': 'on',
                }
                output = c.post(
                    '/project/1/edit', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Project edited</li>' in output.data)
                patched.assert_called_once_with(mock.ANY, mock.ANY)


class MapProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.ui.map_project` view."""

    def setUp(self):
        super(MapProjectTests, self).setUp()
        create_distro(self.session)
        create_project(self.session)
        self.client = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        session.add(self.user)
        session.commit()

    def test_protected_view(self):
        """Assert this view is protected and login is required."""
        output = self.client.get('/project/1/map', follow_redirects=False)
        self.assertEqual(output.status_code, 302)
        self.assertEqual('/login/', parse.urlparse(output.location).path)

    def test_authenticated_access(self):
        """Assert authenticated users have access to the view."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/project/1/map', follow_redirects=False)
            self.assertEqual(output.status_code, 200)

    def test_non_existing_project(self):
        """Assert trying to edit a project that doesn't exist returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.client.get('/project/idonotexist/map', follow_redirects=False)
            self.assertEqual(output.status_code, 404)

    def test_no_csrf_token(self):
        """Assert trying to edit a project without a CSRF token results in no change."""
        with login_user(self.flask_app, self.user):
            data = {
                'package_name': 'geany',
                'distro': 'CentOS',
            }
            output = self.client.post('/project/1/map', data=data, follow_redirects=False)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(0, models.Packages.query.count())

    def test_map_project(self):
        """Assert projects can be mapped to distributions."""
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/1/map')
                self.assertEqual(output.status_code, 200)

                self.assertTrue(b'<h1>Project: geany</h1>' in output.data)
                self.assertTrue(
                    b'<td><label for="distro">Distribution</label></td>' in output.data)

                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'package_name': 'geany',
                    'distro': 'CentOS',
                    'csrf_token': csrf_token,
                }

                output = c.post('/project/1/map', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-default">'
                    b'Mapping added</li>' in output.data)
                self.assertTrue(b'<h1>Project: geany</h1>' in output.data)
                self.assertEqual(1, models.Packages.query.count())

    def test_map_same_distro(self):
        """
        Assert that projects can't have two mappings with the same name to the
        same distribution.
        """
        with login_user(self.flask_app, self.user):
            with self.flask_app.test_client() as c:
                output = c.get('/project/1/map')
                csrf_token = output.data.split(
                    b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
                data = {
                    'package_name': 'geany',
                    'distro': 'CentOS',
                    'csrf_token': csrf_token,
                }

                output = c.post('/project/1/map', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                output = c.post('/project/1/map', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    b'<li class="list-group-item list-group-item-danger">'
                    b'Could not edit the mapping of geany on '
                    b'CentOS, there is already a package geany on CentOS '
                    b'as part of the project <a href="/project/1/">geany'
                    b'</a>.</li>'
                    in output.data)
                self.assertTrue(
                    b'<h1>Project: geany</h1>' in output.data)


class EditProjectMappingTests(DatabaseTestCase):
    """Tests for the :func:`anitya.ui.edit_project_mapping` view."""

    def setUp(self):
        super(EditProjectMappingTests, self).setUp()

        # Set up a mapping to edit
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.distro1 = models.Distro(name='CentOS')
        self.distro2 = models.Distro(name='Fedora')
        self.project = models.Project(
            name='python_project',
            homepage='https://example.com/python_project',
            backend='PyPI',
            ecosystem_name='pypi',
        )
        self.package = models.Packages(
            package_name='python_project', distro=self.distro1.name, project=self.project)
        session.add_all([self.user, self.distro1, self.distro2, self.project, self.package])
        session.commit()
        self.client = self.flask_app.test_client()

    def test_edit_project_mapping_package_name(self):
        """Assert a project's package name can be edited."""
        with login_user(self.flask_app, self.user):
            pre_edit_output = self.client.get('/project/1/map/1')
            csrf_token = pre_edit_output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {
                'package_name': 'Python Project',
                'distro': self.distro1.name,
                'csrf_token': csrf_token,
            }
            output = self.client.post('/project/1/map/1', data=data, follow_redirects=True)

            self.assertEqual(pre_edit_output.status_code, 200)
            self.assertEqual(output.status_code, 200)

            packages = models.Packages.query.all()
            self.assertEqual(1, len(packages))
            self.assertEqual('Python Project', packages[0].package_name)

    def test_edit_project_mapping_distro(self):
        """Assert a project's package distro can be edited."""
        with login_user(self.flask_app, self.user):
            pre_edit_output = self.client.get('/project/1/map/1')
            csrf_token = pre_edit_output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {
                'package_name': self.project.name,
                'distro': self.distro2.name,
                'csrf_token': csrf_token,
            }
            output = self.client.post('/project/1/map/1', data=data, follow_redirects=True)

            self.assertEqual(pre_edit_output.status_code, 200)
            self.assertEqual(output.status_code, 200)

            packages = models.Packages.query.all()
            self.assertEqual(1, len(packages))
            self.assertEqual(self.distro2.name, packages[0].distro)

    def test_clashing_package_name(self):
        """Assert two projects can't map to the same package name in a distro."""
        # Set up a package to clash with.
        session = Session()
        best_project = models.Project(
            name='best_project',
            homepage='https://example.com/best_project',
            backend='PyPI',
            ecosystem_name='pypi',
        )
        best_package = models.Packages(
            package_name='best_project', distro=self.distro1.name, project=best_project)
        session.add_all([best_project, best_package])
        session.commit()

        with login_user(self.flask_app, self.user):
            pre_edit_output = self.client.get('/project/1/map/1')
            csrf_token = pre_edit_output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]
            data = {
                'package_name': self.project.name,
                'distro': self.distro1.name,
                'csrf_token': csrf_token,
            }
            output = self.client.post('/project/1/map/1', data=data, follow_redirects=True)

            self.assertEqual(output.status_code, 200)
            self.assertEqual(2, models.Packages.query.count())
            self.assertEqual(1, models.Packages.query.filter_by(
                package_name='best_project').count())
            self.assertEqual(1, models.Packages.query.filter_by(
                package_name='python_project').count())
            self.assertTrue(b'Could not edit the mapping' in output.data)

    def test_invalid_map_id(self):
        """Assert trying to edit a mapping with an invalid package ID returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/project/1/map/42', data={})
            self.assertEqual(output.status_code, 404)

    def test_invalid_project_id(self):
        """Assert trying to edit a mapping with an invalid project ID returns HTTP 404."""
        with login_user(self.flask_app, self.user):
            output = self.client.post('/project/42/map/1', data={})
            self.assertEqual(output.status_code, 404)
