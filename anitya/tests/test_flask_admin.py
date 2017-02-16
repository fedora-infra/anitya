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

import datetime
import json
import unittest
import sys
import os

import flask

import anitya
from anitya.lib import model
from anitya.tests.base import (Modeltests, create_distro, create_project,
                               create_package, create_flagged_project)


class FlaskAdminTest(Modeltests):
    """ Flask tests for the admin controller. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskAdminTest, self).setUp()

        anitya.app.APP.config['TESTING'] = True
        anitya.SESSION = self.session
        anitya.ui.SESSION = self.session
        anitya.app.SESSION = self.session
        anitya.admin.SESSION = self.session
        anitya.api.SESSION = self.session
        self.app = anitya.app.APP.test_client()

    def test_add_distro(self):
        """ Test the add_distro function. """
        output = self.app.get('/distro/add', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            b'<ul id="flashes" class="list-group">'
            b'<li class="list-group-item list-group-item-warning">'
            b'Login required</li></ul>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/distro/add', follow_redirects=True)
            self.assertEqual(output.status_code, 401)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/distro/add')
            self.assertEqual(output.status_code, 200)

            self.assertTrue(b'<h1>Add a new disribution</h1>' in output.data)
            self.assertIn(
                b'<td><input id="name" name="name" tabindex="1" type="text"'
                b' value=""></td>', output.data)

            data = {
                'name': 'Debian',
            }

            output = c.post(
                '/distro/add', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Add a new disribution</h1>' in output.data)
            self.assertIn(
                b'<td><input id="name" name="name" tabindex="1" type="text"'
                b' value="Debian"></td>', output.data)

            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]

            data['csrf_token'] = csrf_token

            output = c.post(
                '/distro/add', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Distributions participating</h1>' in output.data)
            self.assertTrue(
                b'<a href="/distro/Debian/edit">' in output.data)

            output = c.post(
                '/distro/add', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'class="list-group-item list-group-item-danger">'
                b'Could not add this distro, already exists?</'
                in output.data)
            self.assertTrue(
                b'<h1>Distributions participating</h1>' in output.data)
            self.assertTrue(
                b'<a href="/distro/Debian/edit">' in output.data)

    def test_edit_distro(self):
        """ Test the edit_distro function. """
        self.test_add_distro()

        output = self.app.get('/distro/Debian/edit', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            b'<ul id="flashes" class="list-group">'
            b'<li class="list-group-item list-group-item-warning">'
            b'Login required</li></ul>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/distro/foobar/edit', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get('/distro/Debian/edit', follow_redirects=True)
            self.assertEqual(output.status_code, 401)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/distro/Debian/edit', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Edit disribution: Debian</h1>' in output.data)
            self.assertIn(
                b'<td><input id="name" name="name" tabindex="1" type="text" '
                b'value="Debian"></td>', output.data)

            data = {
                'name': 'debian',
            }

            output = c.post(
                '/distro/Debian/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Edit disribution: Debian</h1>' in output.data)
            self.assertIn(
                b'<td><input id="name" name="name" tabindex="1" type="text"'
                b' value="debian"></td>', output.data)

            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]

            data['csrf_token'] = csrf_token

            output = c.post(
                '/distro/Debian/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Distributions participating</h1>' in output.data)
            self.assertTrue(
                b'<a href="/distro/debian/edit">' in output.data)

    def test_delete_project(self):
        """ Test the delete_project function. """
        create_distro(self.session)
        create_project(self.session)

        output = self.app.get('/project/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            b'<ul id="flashes" class="list-group">'
            b'<li class="list-group-item list-group-item-warning">'
            b'Login required</li></ul>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/project/100/delete', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get('/project/1/delete', follow_redirects=True)
            self.assertEqual(output.status_code, 401)

        output = c.get('/projects/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(b'<h1>Projects monitored</h1>' in output.data)
        self.assertEqual(output.data.count(b'<a href="/project/1'), 1)
        self.assertEqual(output.data.count(b'<a href="/project/2'), 1)
        self.assertEqual(output.data.count(b'<a href="/project/3'), 1)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/project/1/delete', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Delete project geany?</h1>' in output.data)
            self.assertTrue(
                b'<button type="submit" name="confirm" value="Yes"'
                in output.data)

            data = {
                'confirm': 'Yes',
            }

            output = c.post(
                '/project/1/delete', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Delete project geany?</h1>' in output.data)
            self.assertTrue(
                b'<button type="submit" name="confirm" value="Yes"'
                in output.data)

            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]

            data['csrf_token'] = csrf_token
            del(data['confirm'])

            output = c.post(
                '/project/1/delete', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Project: geany</h1>' in output.data)

            data['confirm'] = True

            output = c.post(
                '/project/1/delete', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Projects monitored</h1>' in output.data)
            self.assertTrue(
                b'<li class="list-group-item list-group-item-default">'
                b'Project geany has been removed</li>'
                in output.data)
            self.assertEqual(output.data.count(b'<a href="/project/1'), 0)
            self.assertEqual(output.data.count(b'<a href="/project/2'), 1)
            self.assertEqual(output.data.count(b'<a href="/project/3'), 1)

    def test_delete_project_mapping(self):
        """ Test the delete_project_mapping function. """
        create_distro(self.session)
        create_project(self.session)
        create_package(self.session)

        output = self.app.get(
            '/project/1/delete/Fedora/geany', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            b'<ul id="flashes" class="list-group">'
            b'<li class="list-group-item list-group-item-warning">'
            b'Login required</li></ul>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get(
                '/project/100/delete/Fedora/geany', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get(
                '/project/1/delete/CentOS/geany', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get(
                '/project/1/delete/Fedora/geany2', follow_redirects=True)
            self.assertEqual(output.status_code, 404)

            output = c.get(
                '/project/1/delete/Fedora/geany', follow_redirects=True)
            self.assertEqual(output.status_code, 401)

        output = c.get('/project/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(b'<h1>Project: geany</h1>' in output.data)
        self.assertTrue(b'<td>Fedora</td>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/project/1/delete/Fedora/geany', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Project: geany - Delete package</h1>' in output.data)
            self.assertTrue(
                b'<button type="submit" name="confirm" value="Yes"'
                in output.data)

            data = {
                'confirm': 'Yes',
            }

            output = c.post(
                '/project/1/delete/Fedora/geany', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'<h1>Project: geany - Delete package</h1>' in output.data)
            self.assertTrue(
                b'<button type="submit" name="confirm" value="Yes"'
                in output.data)

            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]

            data['csrf_token'] = csrf_token
            del(data['confirm'])

            output = c.post(
                '/project/1/delete/Fedora/geany', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Project: geany</h1>' in output.data)
            self.assertTrue(b'<td>Fedora</td>' in output.data)

            data['confirm'] = True

            output = c.post(
                '/project/1/delete/Fedora/geany', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                b'class="list-group-item list-group-item-default">'
                b'Mapping for geany has been removed</li>'
                in output.data)
            self.assertTrue(b'<h1>Project: geany</h1>' in output.data)
            self.assertFalse(b'<td>Fedora</td>' in output.data)

    def test_browse_logs(self):
        """ Test the browse_logs function. """
        self.test_add_distro()

        output = self.app.get('/logs', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            b'<ul id="flashes" class="list-group">'
            b'<li class="list-group-item list-group-item-warning">'
            b'Login required</li></ul>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/logs', follow_redirects=True)
            self.assertEqual(output.status_code, 200)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/logs')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Logs</h1>' in output.data)
            self.assertTrue(b'added the distro named: Debian' in output.data)

            output = c.get('/logs?page=abc&limit=def&from_date=ghi')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Logs</h1>' in output.data)
            self.assertTrue(b'added the distro named: Debian' in output.data)

            output = c.get('/logs?from_date=%s' % datetime.datetime.utcnow().date())
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Logs</h1>' in output.data)
            self.assertTrue(b'added the distro named: Debian' in output.data)

            # the Debian log shouldn't show up if the "from date" is tomorrow
            tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)
            output = c.get('/logs?from_date=%s' % tomorrow)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Logs</h1>' in output.data)
            self.assertFalse(b'added the distro named: Debian' in output.data)

    def test_browse_flags(self):
        """ Test the browse_flags function. """

        create_flagged_project(self.session)

        output = self.app.get('/flags', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            b'<ul id="flashes" class="list-group">'
            b'<li class="list-group-item list-group-item-warning">'
            b'Login required</li></ul>' in output.data)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/flags', follow_redirects=True)
            self.assertEqual(output.status_code, 401)

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.get('/flags')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Flags</h1>' in output.data)
            self.assertTrue(b'geany' in output.data)

            output = c.get('/flags?page=abc&limit=def&from_date=ghi')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Flags</h1>' in output.data)
            self.assertTrue(b'geany' in output.data)

            output = c.get('/flags?from_date=%s' % datetime.datetime.utcnow().date())
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Flags</h1>' in output.data)
            self.assertTrue(b'geany' in output.data)

            # geany shouldn't show up if the "from date" is tomorrow
            tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)
            output = c.get('/flags?from_date=%s' % tomorrow)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Flags</h1>' in output.data)
            self.assertFalse(b'geany' in output.data)

            output = c.get('/flags?from_date=%s&project=geany' % datetime.datetime.utcnow().date())
            self.assertEqual(output.status_code, 200)
            self.assertTrue(b'<h1>Flags</h1>' in output.data)
            self.assertTrue(b'geany' in output.data)

    def test_flag_project(self):
        """ Test setting the flag state of a project. """

        flag = create_flagged_project(self.session)

        project = model.Project.by_name(self.session, 'geany')[0]
        self.assertEqual(len(project.flags), 1)
        self.assertEqual(project.flags[0].state, 'open')

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'some_invalid_openid_url'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.post('/flags/{0}/set/closed'.format(flag.id),
                           follow_redirects=True)

            # Non-admin ID will complain, insufficient creds
            self.assertEqual(output.status_code, 401)

        # Nothing should have changed.
        project = model.Project.by_name(self.session, 'geany')[0]
        self.assertEqual(len(project.flags), 1)
        self.assertEqual(project.flags[0].state, 'open')

        self.assertEqual(flag.state, 'open')

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.post('/flags/{0}/set/closed'.format(flag.id),
                           follow_redirects=True)
            self.assertEqual(output.status_code, 200)

            # Now the flag state should *not* have toggled because while we did
            # provide a valid admin openid, we did not provide a CSRF token.
            project = model.Project.by_name(self.session, 'geany')[0]
            self.assertEqual(len(project.flags), 1)
            self.assertEqual(project.flags[0].state, 'open')

            # Go ahead and get the csrf token from the page and try again.
            data = {}

            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]

            data['csrf_token'] = csrf_token

            output = c.post('/flags/{0}/set/closed'.format(flag.id),
                            data=data,
                            follow_redirects=True)
            self.assertEqual(output.status_code, 200)

        # Now the flag state should have toggled.
        project = model.Project.by_name(self.session, 'geany')[0]
        self.assertEqual(len(project.flags), 1)
        self.assertEqual(project.flags[0].state, 'closed')

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.post('/flags/{0}/set/open'.format(flag.id),
                           follow_redirects=True)

            # Get a new CSRF Token
            output = c.get('/distro/add')
            csrf_token = output.data.split(
                b'name="csrf_token" type="hidden" value="')[1].split(b'">')[0]

            # Grab the CSRF token again so we can toggle the flag again
            data = {'csrf_token': csrf_token}

            output = c.post('/flags/{0}/set/open'.format(flag.id),
                            data=data,
                            follow_redirects=True)
            self.assertEqual(output.status_code, 200)

        # Make sure we can toggle the flag again.
        project = model.Project.by_name(self.session, 'geany')[0]
        self.assertEqual(len(project.flags), 1)
        self.assertEqual(project.flags[0].state, 'open')

        with anitya.app.APP.test_client() as c:
            with c.session_transaction() as sess:
                sess['openid'] = 'http://pingou.id.fedoraproject.org/'
                sess['fullname'] = 'Pierre-Yves C.'
                sess['nickname'] = 'pingou'
                sess['email'] = 'pingou@pingoured.fr'

            output = c.post('/flags/{0}/set/nonsense'.format(flag.id),
                           follow_redirects=True)
            self.assertEqual(output.status_code, 422)

        # Make sure that passing garbage doesn't change anything.
        project = model.Project.by_name(self.session, 'geany')[0]
        self.assertEqual(len(project.flags), 1)
        self.assertEqual(project.flags[0].state, 'open')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskAdminTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
