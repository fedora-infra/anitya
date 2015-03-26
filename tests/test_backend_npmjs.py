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

import anitya.lib.backends.npmjs as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from tests import Modeltests, create_distro, skip_jenkins


BACKEND = 'npmjs'


class NpmjsBackendtests(Modeltests):
    """ Drupal backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(NpmjsBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='request',
            homepage='https://www.npmjs.org/package/request',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='foobarasd',
            homepage='https://www.npmjs.org/package/foobarasd',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='colors',
            homepage='https://www.npmjs.org/package/colors',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """ Test the get_version function of the npmjs backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '2.54.0'
        obs = backend.NpmjsBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.NpmjsBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '1.0.3'
        obs = backend.NpmjsBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the debian backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            '0.8.3', '0.9.0', '0.9.1', '0.9.5', '0.10.0', '1.0.0', '1.1.0',
            '1.1.1', '1.2.0', '1.9.0', '1.9.1', '1.9.2', '1.9.3', '1.9.5',
            '1.9.7', '1.9.8', '1.9.9', '2.0.0', '2.0.1', '2.0.2', '2.0.3',
            '2.0.4', '2.0.5', '2.1.0', '2.1.1', '2.2.0', '2.2.5', '2.2.6',
            '2.2.9', '2.9.0', '2.9.1', '2.9.2', '2.9.3', '2.9.100',
            '2.9.150', '2.9.151', '2.9.152', '2.9.153', '2.9.200',
            '2.9.201', '2.9.202', '2.9.203', '2.10.0', '2.11.0', '2.11.1',
            '2.11.2', '2.11.3', '2.11.4', '2.12.0', '2.14.0', '2.16.0',
            '2.16.2', '2.16.4', '2.16.6', '2.18.0', '2.19.0', '2.20.0',
            '2.21.0', '2.22.0', '2.23.0', '2.24.0', '2.25.0', '2.26.0',
            '2.27.0', '2.28.0', '2.29.0', '2.30.0', '2.31.0', '2.32.0',
            '2.33.0', '2.34.0', '2.35.0', '2.36.0', '2.37.0', '2.38.0',
            '2.39.0', '2.40.0', '2.41.0', '2.42.0', '2.43.0', '2.44.0',
            '2.45.0', '2.46.0', '2.47.0', '2.48.0', '2.49.0', '2.50.0',
            '2.51.0', '2.52.0', '2.53.0', '2.54.0',
        ]
        obs = backend.NpmjsBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.NpmjsBackend.get_versions,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = [
            '0.3.0', '0.5.0', '0.5.1', '0.6.0', '0.6.0-1', '0.6.1', '0.6.2',
            '1.0.0', '1.0.1', '1.0.2', '1.0.3',
        ]
        obs = backend.NpmjsBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(NpmjsBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
