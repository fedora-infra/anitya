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
anitya tests for the custom backend.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya.lib.backends.github as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from tests import Modeltests, create_distro


BACKEND = 'Github'


class GithubBackendtests(Modeltests):
    """ Github backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(GithubBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='fedocal',
            homepage='https://github.com/fedora-infra/fedocal',
            version_url='fedora-infra/fedocal',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='foobar',
            homepage='http://github.com/foo/bar',
            version_url='foobar/bar',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='pkgdb2',
            homepage='https://github.com/fedora-infra/pkgdb2',
            version_url='fedora-infra/pkgdb2',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()


    def test_get_version(self):
        """ Test the get_version function of the github backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = 'v0.9.1'
        obs = backend.GithubBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = 'v1.18.5'
        obs = backend.GithubBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the github backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            'v0.1.0', 'v0.1.1', 'v0.1.2', 'v0.2.0', 'v0.3.0', 'v0.3.1',
            'v0.4.0', 'v0.4.1', 'v0.4.2', 'v0.4.3', 'v0.4.5', 'v.0.4.6',
            'v0.4.7', 'v0.5.0', 'v0.5.1', 'v0.6.0', 'v0.6.1', 'v0.6.2',
            'v0.6.3', 'v0.7', 'v0.7.1', 'v0.8', 'v0.9', 'v0.9.1']
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = [
            'v0.1', 'v0.2', 'v0.2.1', 'v0.3', 'v0.4', 'v0.5', 'v0.6', 'v0.7',
            'v0.8', 'v1.0', 'v1.1', 'v1.2', 'v1.3', 'v1.4', 'v1.5', 'v1.6',
            'v1.7', 'v1.8', 'v1.8.1', 'v1.8.2', 'v1.9', 'v1.9.1', 'v1.9.2',
            'v1.10', 'v1.10.1', 'v1.11', 'v1.11.1', 'v1.12', 'v1.12.1',
            'v1.13', 'v1.13.1', 'v1.13.2', 'v1.13.3', 'v1.14', 'v1.14.1',
            'v1.14.2', 'v1.14.3', 'v1.14.4', 'v1.15', 'v1.16', 'v1.17', 'v1.18',
            'v1.18.1', 'v1.18.2', 'v1.18.3', 'v1.18.4', 'v1.18.5']
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GithubBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
