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

import anitya.lib.backends.gnome as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from tests import Modeltests, create_distro, skip_jenkins


BACKEND = 'GNOME'


class GnomeBackendtests(Modeltests):
    """ custom backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(GnomeBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='evolution-data-server',
            homepage='https://git.gnome.org/browse/evolution-data-server/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='fake',
            homepage='https://pypi.python.org/pypi/repo_manager_fake',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='gnome-control-center',
            homepage='https://git.gnome.org/browse/gnome-control-center/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_custom_get_version(self):
        """ Test the get_version function of the gnome backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '3.16.0'
        obs = backend.GnomeBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GnomeBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '3.16.0'
        obs = backend.GnomeBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_custom_get_versions(self):
        """ Test the get_versions function of the gnome backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            '0.0.3', '0.0.4', '0.0.5', '0.0.6', '0.0.7', '0.0.90', '0.0.91',
            '0.0.92', '0.0.93', '0.0.94', '0.0.94.1', '0.0.95', '0.0.96',
            '0.0.97', '0.0.98', '0.0.99', '1.0.0', '1.0.1', '1.0.2',
            '1.0.3', '1.0.4', '1.1.0', '1.1.1', '1.1.2', '1.1.3', '1.1.4',
            '1.1.4.1', '1.1.4.2', '1.1.5', '1.1.6', '1.2.0', '1.2.1',
            '1.2.2', '1.2.3', '1.3.1', '1.3.2', '1.3.3', '1.3.3.1', '1.3.4',
            '1.3.5', '1.3.6', '1.3.6.1', '1.3.7', '1.3.8', '1.4.0',
            '1.4.1', '1.4.1.1', '1.4.2', '1.4.2.1', '1.5.1', '1.5.2',
            '1.5.3', '1.5.4', '1.5.5', '1.5.90', '1.5.91', '1.5.92',
            '1.6.0', '1.6.1', '1.6.2', '1.6.3', '1.7.1', '1.7.2',
            '1.7.3', '1.7.4', '1.7.90', '1.7.90.1', '1.7.91', '1.7.92',
            '1.8.0', '1.8.1', '1.8.2', '1.8.3', '1.9.1', '1.9.2', '1.9.3',
            '1.9.4', '1.9.5', '1.9.6', '1.9.6.1', '1.9.91', '1.9.92', '1.10.0',
            '1.10.1', '1.10.2', '1.10.3', '1.10.3.1', '1.11.1', '1.11.2',
            '1.11.3', '1.11.4', '1.11.5', '1.11.6', '1.11.6.1', '1.11.90',
            '1.11.91', '1.11.92', '1.12.0', '1.12.1', '1.12.2', '1.12.3',
            '2.21.1', '2.21.2', '2.21.3', '2.21.4', '2.21.5', '2.21.5.1',
            '2.21.90', '2.21.91', '2.21.92', '2.22.0', '2.22.1', '2.22.1.1',
            '2.22.2', '2.22.3', '2.23.1', '2.23.2', '2.23.3', '2.23.4',
            '2.23.5', '2.23.6', '2.23.90', '2.23.90.1', '2.23.91', '2.23.92',
            '2.24.0', '2.24.1', '2.24.1.1', '2.24.2', '2.24.3', '2.24.4',
            '2.24.4.1', '2.24.5', '2.25.1', '2.25.2', '2.25.3', '2.25.4',
            '2.25.5', '2.25.90', '2.25.91', '2.25.92', '2.26.0', '2.26.1',
            '2.26.1.1', '2.26.2', '2.26.3', '2.27.1', '2.27.2', '2.27.3',
            '2.27.4', '2.27.5', '2.27.90', '2.27.91', '2.27.92', '2.28.0',
            '2.28.1', '2.28.2', '2.28.3', '2.28.3.1', '2.29.1', '2.29.2',
            '2.29.3', '2.29.4', '2.29.5', '2.29.6', '2.29.90', '2.29.91',
            '2.29.92', '2.30.0', '2.30.1', '2.30.2', '2.30.2.1', '2.30.3',
            '2.31.1', '2.31.2', '2.31.3', '2.31.3.1', '2.31.4', '2.31.5',
            '2.31.6', '2.31.90', '2.31.91', '2.31.92', '2.31.92.1', '2.32.0',
            '2.32.1', '2.32.2', '2.32.3', '2.91.0', '2.91.1', '2.91.1.1',
            '2.91.2', '2.91.3', '2.91.4', '2.91.4.1', '2.91.5', '2.91.6',
            '2.91.90', '2.91.91', '2.91.92', '3.0.0', '3.0.1', '3.0.2',
            '3.0.2.1', '3.0.3', '3.0.3.1', '3.1.1', '3.1.2', '3.1.3', '3.1.4',
            '3.1.5', '3.1.90', '3.1.91', '3.1.92', '3.2.0', '3.2.1', '3.2.2',
            '3.2.3', '3.3.1', '3.3.1.1', '3.3.2', '3.3.3', '3.3.4', '3.3.5',
            '3.3.90', '3.3.91', '3.3.92', '3.4.0', '3.4.1', '3.4.2', '3.4.3',
            '3.4.4', '3.5.1', '3.5.2', '3.5.3', '3.5.3.1', '3.5.4', '3.5.5',
            '3.5.90', '3.5.91', '3.5.92', '3.6.0', '3.6.1', '3.6.2', '3.6.3',
            '3.6.4', '3.7.1', '3.7.2', '3.7.2.1', '3.7.3', '3.7.4', '3.7.5',
            '3.7.90', '3.7.91', '3.7.92', '3.8.0', '3.8.1', '3.8.2', '3.8.3',
            '3.8.4', '3.8.5', '3.9.1', '3.9.2', '3.9.3', '3.9.4', '3.9.5',
            '3.9.90', '3.9.91', '3.9.92', '3.10.0', '3.10.1', '3.10.2',
            '3.10.3', '3.10.4', '3.11.1', '3.11.2', '3.11.3', '3.11.4',
            '3.11.5', '3.11.90', '3.11.91', '3.11.92', '3.12.0', '3.12.1',
            '3.12.2', '3.12.3', '3.12.4', '3.12.5', '3.12.6', '3.12.7',
            '3.12.7.1', '3.12.8', '3.12.9', '3.12.10', '3.12.11', '3.13.1',
            '3.13.2', '3.13.3', '3.13.4', '3.13.5', '3.13.6', '3.13.7',
            '3.13.8', '3.13.9', '3.13.10', '3.13.90', '3.15.91', '3.15.92',
            '3.16.0'
        ]
        obs = backend.GnomeBackend.get_ordered_versions(project)
        #print [str(o) for o in obs]
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GnomeBackend.get_versions,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = [
            '2.19.1', '2.19.3', '2.19.4', '2.19.5', '2.19.6', '2.19.90',
            '2.19.91', '2.19.92', '2.20.0', '2.20.0.1', '2.20.1', '2.20.3',
            '2.21.1', '2.21.2', '2.21.4', '2.21.5', '2.21.90', '2.21.92',
            '2.22.0', '2.22.1', '2.22.2', '2.22.2.1', '2.23.1', '2.23.2',
            '2.23.3', '2.23.4', '2.23.5', '2.23.6', '2.23.90', '2.24.0',
            '2.24.0.1', '2.25.1', '2.25.2', '2.25.3', '2.25.90', '2.25.92',
            '2.26.0', '2.27.3', '2.27.4', '2.27.4.1', '2.27.5', '2.27.90',
            '2.27.91', '2.28.0', '2.28.1', '2.29.4', '2.29.6', '2.29.90',
            '2.29.91', '2.29.92', '2.30.0', '2.30.1', '2.31.1', '2.31.2',
            '2.31.3', '2.31.4', '2.31.4.1', '2.31.4.2', '2.31.5', '2.31.6',
            '2.31.90', '2.31.91', '2.31.92', '2.31.92.1', '2.32.0', '2.32.1',
            '2.90.1', '2.91.0', '2.91.2', '2.91.3', '2.91.3.1', '2.91.4',
            '2.91.5', '2.91.6', '2.91.90', '2.91.91', '2.91.92', '2.91.93',
            '3.0.0', '3.0.0.1', '3.0.1', '3.0.1.1', '3.0.2', '3.1.3',
            '3.1.4', '3.1.5', '3.1.90', '3.1.91', '3.1.92', '3.2.0', '3.2.1',
            '3.2.2', '3.2.3', '3.3.2', '3.3.3', '3.3.4', '3.3.4.1', '3.3.5',
            '3.3.90', '3.3.91', '3.3.92', '3.4.0', '3.4.1', '3.4.2', '3.4.3',
            '3.4.3.1', '3.5.2', '3.5.3', '3.5.4', '3.5.5', '3.5.6', '3.5.90',
            '3.5.91', '3.5.92', '3.6.0', '3.6.1', '3.6.2', '3.6.3', '3.7.1',
            '3.7.3', '3.7.4', '3.7.5', '3.7.5.1', '3.7.90', '3.7.91',
            '3.7.92', '3.8.0', '3.8.1', '3.8.1.5', '3.8.2', '3.8.3', '3.8.4',
            '3.8.4.1', '3.8.5', '3.8.6', '3.9.2', '3.9.2.1', '3.9.3', '3.9.5',
            '3.9.90', '3.9.90.1', '3.9.91', '3.9.92', '3.10.0', '3.10.1',
            '3.10.2', '3.10.3', '3.11.1', '3.11.2', '3.11.3', '3.11.5',
            '3.11.90', '3.11.91', '3.11.92', '3.12.0', '3.12.1', '3.13.1',
            '3.13.2', '3.13.3', '3.13.4', '3.13.90', '3.13.91', '3.13.92',
            '3.14.0', '3.14.1', '3.14.2', '3.14.3', '3.14.4', '3.15.4',
            '3.15.90', '3.15.91', '3.15.92', '3.16.0'
        ]
        obs = backend.GnomeBackend.get_ordered_versions(project)
        #print [str(o) for o in obs]
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GnomeBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
