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
from __future__ import unicode_literals

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest

import anitya.lib.backends.google as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import Modeltests, create_distro, skip_jenkins


BACKEND = 'Google code'


class GoogleBackendtests(Modeltests):
    """ custom backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(GoogleBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='arduino',
            homepage='https://code.google.com/p/arduino/',
            backend=BACKEND,
            version_scheme=model.GENERIC_VERSION,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='foo',
            homepage='https://code.google.com/p/foo',
            backend=BACKEND,
            version_scheme=model.GENERIC_VERSION,
        )
        self.session.add(project)
        self.session.commit()


    def test_cpan_get_version(self):
        """ Test the get_version function of the custom backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '1.0.5'
        obs = backend.GoogleBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GoogleBackend.get_version,
            project
        )


    def test_cpan_get_versions(self):
        """ Test the get_versions function of the custom backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            '0017', '0018', '0019', '0020', '0021', '0022', '0023',
            '1.0', '1.0.1', '1.0.2', '1.0.3', '1.0.4', '1.0.5'
        ]
        obs = backend.GoogleBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GoogleBackend.get_version,
            project
        )


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GoogleBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
