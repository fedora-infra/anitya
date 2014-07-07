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
from tests import Modeltests, create_distro


BACKEND = 'GNOME'


class GnomeBackendtests(Modeltests):
    """ custom backend tests. """

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
        exp = '3.13'
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
        exp = '3.13'
        obs = backend.GnomeBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_custom_get_versions(self):
        """ Test the get_versions function of the gnome backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            '0.0', '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
            '1.8', '1.9', '1.10', '1.11', '1.12', '2.21', '2.22', '2.23',
            '2.24', '2.25', '2.26', '2.27', '2.28', '2.29', '2.30', '2.31',
            '2.32', '2.91', '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6',
            '3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13']
        obs = backend.GnomeBackend.get_ordered_versions(project)
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
            '2.19', '2.20', '2.21', '2.22', '2.23', '2.24', '2.25', '2.26',
            '2.27', '2.28', '2.29', '2.30', '2.31', '2.32', '2.90', '2.91',
            '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8',
            '3.9', '3.10', '3.11', '3.12', '3.13']
        obs = backend.GnomeBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GnomeBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
