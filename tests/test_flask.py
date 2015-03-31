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

__requires__ = ['SQLAlchemy >= 0.8']
import pkg_resources

import json
import unittest
import sys
import os

import flask

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya
from anitya.lib import model
from tests import Modeltests, create_distro, create_project


class FlaskTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskTest, self).setUp()

        anitya.app.APP.config['TESTING'] = True
        anitya.SESSION = self.session
        anitya.ui.SESSION = self.session
        anitya.app.SESSION = self.session
        anitya.admin.SESSION = self.session
        anitya.api.SESSION = self.session
        self.app = anitya.app.APP.test_client()

    def test_index(self):
        """ Test the index function. """
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)

        expected = """
      <h2><span class="glyphicon glyphicon-bullhorn"></span> Announce</h2>
      <p>We monitor upstream releases and broadcast them on
      <a href="http://fedmsg.com">fedmsg</a>, the FEDerated MeSsaGe bus. </p>
      <p>Use <a href="https://apps.fedoraproject.org/notifications">fedmsg
      notifications (FMN)</a>, to set up your own, <em>personalized</em>,
      alerts.</p>"""

        self.assertTrue(expected in output.data)

        expected = """
      <h2><span class="glyphicon glyphicon-search"></span> Search</h2>
      <p>Currently 0 projects are being monitored by Anitya.
      Your project of interest might be there, or not. To check it
      <a href="/projects/">browse the list of all projects</a>
      or simply search for them!</p>"""

        self.assertTrue(expected in output.data)

    def test_about(self):
        """ Test the about function. """
        output = self.app.get('/about')
        self.assertEqual(output.status_code, 200)

        expected = """
<h1 class="title">Anitya</h1>
<p>Anitya is a project version monitoring system.</p>
<p>Every-day Anitya checks if there is a new version available and broadcast the
new versions found via a message bus: <a class="reference external" href="http://fedmsg.com/">fedmsg</a>
(<a class="reference external" href="fedmsg">More information on fedmsg for anitya</a>).</p>
<p>Anyone with an OpenID account can register a new application on Anitya. To
do so, all you need is the project name and its home page, the combination
of both must be unique. In order to retrieve the new version, you can specify
a backend for the project hosting. More information below.</p>"""

        self.assertTrue(expected in output.data)

    def test_project(self):
        """ Test the project function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/project/1/')
        self.assertEqual(output.status_code, 200)

        expected = """
            <p><a property="doap:homepage" href="http://www.geany.org/"
               target="_blank">http://www.geany.org/
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

        expected = """
                <a href="http://www.geany.org/" target="_blank">
                  http://www.geany.org/
                </a>"""
        self.assertTrue(expected in output.data)

        expected = """
                <a href="https://fedorahosted.org/r2spec/" target="_blank">
                  https://fedorahosted.org/r2spec/
                </a>"""
        self.assertTrue(expected in output.data)

        expected = """
                <a href="http://subsurface.hohndel.org/" target="_blank">
                  http://subsurface.hohndel.org/
                </a>"""
        self.assertTrue(expected in output.data)

        self.assertEqual(output.data.count('<a href="/project/'), 3)

        output = self.app.get('/projects/?page=ab')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count('<a href="/project/'), 3)

    def test_distros(self):
        """ Test the distros function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/distros/')
        self.assertEqual(output.status_code, 200)

        expected = "Here is the list of all the distributions"
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

        expected = """
  <blockquote>
      Oups this is embarrassing, it seems that no projects are being
      monitored currently.
  </blockquote>"""
        self.assertTrue(expected in output.data)
        self.assertTrue(
            'form action="/distro/Fedora/search/" role="form">'
            in output.data)
        self.assertTrue(
            '<h1>Projects of Fedora monitored</h1>' in output.data)

        output = self.app.get('/distro/Fedora/?page=ab')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)
        self.assertTrue(
            'form action="/distro/Fedora/search/" role="form">'
            in output.data)
        self.assertTrue(
            '<h1>Projects of Fedora monitored</h1>' in output.data)

    def test_distro_projects_search(self):
        """ Test the distro_projects_search function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/distro/Fedora/search/gua')
        self.assertEqual(output.status_code, 200)

        expected = """
    <blockquote>
        Oups this is embarrassing, it seems that no projects are being
        monitored currently.
    </blockquote>"""
        self.assertTrue(expected in output.data)
        self.assertTrue(
            'form action="/distro/Fedora/search/" role="form">'
            in output.data)
        self.assertTrue(
            '<h1>Search projects in Fedora</h1>' in output.data)

    def test_projects_search(self):
        """ Test the projects_search function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/projects/search/g')
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count('<a href="/project/'), 1)

        output = self.app.get('/projects/search/g*')
        self.assertEqual(output.status_code, 200)
        expected = """
                  <a href="http://www.geany.org/" target="_blank">
                    http://www.geany.org/
                  </a>"""
        self.assertTrue(expected in output.data)

        self.assertEqual(output.data.count('<a href="/project/'), 1)

        output = self.app.get('/projects/search/?page=ab')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(expected in output.data)
        self.assertEqual(output.data.count('<a href="/project/'), 3)

        output = self.app.get(
            '/projects/search/geany*', follow_redirects=True)
        self.assertEqual(output.status_code, 200)

        expected = '<li class="message">Only one result matching with an '\
            'exact match, redirecting</li>'
        self.assertTrue(expected in output.data)

    def test_new_project(self):
        """ Test the new_project function. """
        output = self.app.get('/project/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="errors">Login required</li>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/project/new', follow_redirects=True)
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h1>Add project</h1>' in output.data)
            self.assertTrue(
                '<td><label for="regex">Regex</label></td>' in output.data)

            data = {
                'name': 'repo_manager',
                'homepage': 'https://pypi.python.org/pypi/repo_manager',
                'backend': 'PyPI',
            }

            output = c.post(
                '/project/new', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Add project</h1>' in output.data)
            self.assertTrue(
                '<td><label for="regex">Regex</label></td>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data['csrf_token'] = csrf_token

            output = c.post(
                '/project/new', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Project created</li>' in output.data)
            self.assertTrue(
                '<h1>Project: repo_manager</h1>' in output.data)

            output = c.post(
                '/project/new', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertFalse(
                '<li class="message">Project created</li>' in output.data)
            self.assertFalse(
                '<h1>Project: repo_manager</h1>' in output.data)
            self.assertTrue(
                '="message">Could not add this project, already exists?</'
                in output.data)
            self.assertTrue('<h1>Add project</h1>' in output.data)


        projects = model.Project.all(self.session, count=True)
        self.assertEqual(projects, 1)

    def test_edit_project(self):
        """ Test the edit_project function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/project/1/edit', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="errors">Login required</li>' in output.data)

        projects = model.Project.all(self.session)
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[0].id, 1)
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[1].id, 3)
        self.assertEqual(projects[2].name, 'subsurface')
        self.assertEqual(projects[2].id, 2)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/project/10/edit', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get('/project/1/edit', follow_redirects=True)
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h1>Edit project</h1>' in output.data)
            self.assertTrue(
                '<td><label for="regex">Regex</label></td>' in output.data)

            data = {
                'name': 'repo_manager',
                'homepage': 'https://pypi.python.org/pypi/repo_manager',
                'backend': 'PyPI',
            }

            output = c.post(
                '/project/1/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Edit project</h1>' in output.data)
            self.assertTrue(
                '<td><label for="regex">Regex</label></td>' in output.data)

            # This should works just fine
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data['csrf_token'] = csrf_token

            output = c.post(
                '/project/1/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Project edited</li>' in output.data)
            self.assertTrue(
                '<h1>Project: repo_manager</h1>' in output.data)

            # This should fail, the R2spec project already exists
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
                '<li class="errors">Could not edit this project. Is there '
                'already a project with these name and homepage?</li>'
                in output.data)
            self.assertTrue(
                '<h1>Project: repo_manager</h1>' in output.data)

        projects = model.Project.all(self.session)
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].name, 'R2spec')
        self.assertEqual(projects[0].id, 3)
        self.assertEqual(projects[1].name, 'repo_manager')
        self.assertEqual(projects[1].id, 1)
        self.assertEqual(projects[2].name, 'subsurface')
        self.assertEqual(projects[2].id, 2)

    def test_map_project(self):
        """ Test the map_project function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/project/1/map', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="errors">Login required</li>' in output.data)

        projects = model.Project.all(self.session)
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(len(projects[0].packages), 0)
        self.assertEqual(projects[0].id, 1)
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[1].id, 3)
        self.assertEqual(len(projects[1].packages), 0)
        self.assertEqual(projects[2].name, 'subsurface')
        self.assertEqual(projects[2].id, 2)
        self.assertEqual(len(projects[2].packages), 0)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/project/10/map', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get('/project/1/map', follow_redirects=True)
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h1>Project: geany</h1>' in output.data)
            self.assertTrue(
                '<td><label for="distro">Distribution</label></td>'
                in output.data)

            data = {
                'package_name': 'geany',
                'distro': 'CentOS',
            }

            output = c.post(
                '/project/1/map', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Project: geany</h1>' in output.data)
            self.assertTrue(
                '<td><label for="distro">Distribution</label></td>'
                in output.data)

            # This should works just fine
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data['csrf_token'] = csrf_token

            output = c.post(
                '/project/1/map', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Mapping added</li>' in output.data)
            self.assertTrue(
                '<h1>Project: geany</h1>' in output.data)

            # This should fail, the mapping already exists
            data = {
                'package_name': 'geany',
                'distro': 'CentOS',
                'csrf_token': csrf_token,
            }

            output = c.post(
                '/project/1/map', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Could not edit the mapping of geany on '
                'CentOS, there is already a package geany on CentOS '
                'as part of the project <a href="/project/1/">geany'
                '</a>.</li>'
                in output.data)
            self.assertTrue(
                '<h1>Project: geany</h1>' in output.data)

        projects = model.Project.all(self.session)
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[0].id, 1)
        self.assertEqual(len(projects[0].packages), 1)
        self.assertEqual(projects[0].packages[0].package_name, 'geany')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[1].id, 3)
        self.assertEqual(len(projects[1].packages), 0)
        self.assertEqual(projects[2].name, 'subsurface')
        self.assertEqual(projects[2].id, 2)
        self.assertEqual(len(projects[2].packages), 0)

    def test_edit_project_mapping(self):
        """ Test the edit_project_mapping function. """
        self.test_map_project()

        projects = model.Project.all(self.session)
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[0].id, 1)
        self.assertEqual(len(projects[0].packages), 1)
        self.assertEqual(projects[0].packages[0].package_name, 'geany')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[1].id, 3)
        self.assertEqual(len(projects[1].packages), 0)
        self.assertEqual(projects[2].name, 'subsurface')
        self.assertEqual(projects[2].id, 2)
        self.assertEqual(len(projects[2].packages), 0)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/project/10/map/1', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get('/project/1/map/10', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get('/project/1/map/1', follow_redirects=True)
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h1>Project: geany</h1>' in output.data)
            self.assertTrue(
                '<td><label for="distro">Distribution</label></td>'
                in output.data)

            data = {
                'package_name': 'geany2',
                'distro': 'CentOS',
            }

            output = c.post(
                '/project/1/map/1', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h1>Project: geany</h1>' in output.data)
            self.assertTrue(
                '<td><label for="distro">Distribution</label></td>'
                in output.data)

            # This should works just fine
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data['csrf_token'] = csrf_token

            output = c.post(
                '/project/1/map/1', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Mapping edited</li>' in output.data)
            self.assertTrue(
                '<h1>Project: geany</h1>' in output.data)

            # This should fail, the mapping already exists
            data = {
                'package_name': 'geany2',
                'distro': 'CentOS',
                'csrf_token': csrf_token,
            }

            output = c.post(
                '/project/1/map/1', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">Could not edit the mapping of geany2 on '
                'CentOS, there is already a package geany2 on CentOS '
                'as part of the project <a href="/project/1/">geany'
                '</a>.</li>'
                in output.data)
            self.assertTrue(
                '<h1>Project: geany</h1>' in output.data)

        projects = model.Project.all(self.session)
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[0].id, 1)
        self.assertEqual(len(projects[0].packages), 1)
        self.assertEqual(projects[0].packages[0].package_name, 'geany2')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[1].id, 3)
        self.assertEqual(len(projects[1].packages), 0)
        self.assertEqual(projects[2].name, 'subsurface')
        self.assertEqual(projects[2].id, 2)
        self.assertEqual(len(projects[2].packages), 0)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
