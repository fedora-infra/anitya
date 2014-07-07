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

import anitya.lib.backends.drupal6 as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from tests import Modeltests, create_distro


BACKEND = 'Drupal6'


class Drupal6Backendtests(Modeltests):
    """ Drupal backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(Drupal6Backendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='wysiwyg',
            homepage='https://www.drupal.org/project/wysiwyg',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='foo',
            homepage='http://pecl.php.net/package/foo',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='admin_menu',
            homepage='https://www.drupal.org/project/admin_menu',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()


    def test_get_version(self):
        """ Test the get_version function of the debian backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '2.4'
        obs = backend.Drupal6Backend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.Drupal6Backend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '1.8'
        obs = backend.Drupal6Backend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the debian backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = ['2.4']
        obs = backend.Drupal6Backend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.Drupal6Backend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = ['1.8']
        obs = backend.Drupal6Backend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Drupal6Backendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
