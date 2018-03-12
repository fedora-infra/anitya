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
anitya tests for the Maven backend.
'''

import unittest

from anitya.lib.backends.maven import MavenBackend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = 'Maven Central'


class MavenBackendTest(DatabaseTestCase):
    """ custom backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(MavenBackendTest, self).setUp()

        create_distro(self.session)

    def assert_plexus_version(self, **kwargs):
        project = models.Project(backend=BACKEND, **kwargs)
        exp = '1.3.8'
        obs = MavenBackend.get_version(project)
        self.assertEqual(obs, exp)

    def assert_invalid(self, **kwargs):
        project = models.Project(backend=BACKEND, **kwargs)
        self.assertRaises(
            AnityaPluginException,
            MavenBackend.get_version,
            project
        )

    def test_maven_nonexistent(self):
        self.assert_invalid(
            name='foo',
            homepage='https://example.com',
        )

    def test_maven_coordinates_in_version_url(self):
        self.assert_plexus_version(
            name='plexus-maven-plugin',
            version_url='org.codehaus.plexus:plexus-maven-plugin',
            homepage='https://plexus.codehaus.org/',
        )

    def test_maven_coordinates_in_name(self):
        self.assert_plexus_version(
            name='org.codehaus.plexus:plexus-maven-plugin',
            homepage='https://plexus.codehaus.org/',
        )

    def test_maven_bad_coordinates(self):
        self.assert_invalid(
            name='plexus-maven-plugin',
            homepage='https://plexus.codehaus.org/',
            version_url='plexus-maven-plugin',
        )

    def test_maven_get_version_by_url(self):
        self.assert_plexus_version(
            name='plexus-maven-plugin',
            homepage='https://repo1.maven.org/maven2/'
                     'org/codehaus/plexus/plexus-maven-plugin/',
        )

    def test_dots_in_artifact_id(self):
        project = models.Project(
            backend=BACKEND,
            name='felix-gogo-shell',
            homepage='https://www.apache.org/dist/felix/',
            version_url='org.apache.felix:org.apache.felix.gogo.shell',
        )
        exp = '1.0.0'
        obs = MavenBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_maven_get_versions(self):
        project = models.Project(
            backend=BACKEND,
            name='plexus-maven-plugin',
            version_url='org.codehaus.plexus:plexus-maven-plugin',
            homepage='https://plexus.codehaus.org/',
        )
        exp = ['1.1-alpha-7', '1.1', '1.1.1', '1.1.2', '1.1.3', '1.2', '1.3',
               '1.3.1', '1.3.2', '1.3.3', '1.3.4', '1.3.5', '1.3.6', '1.3.7',
               '1.3.8']
        obs = MavenBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MavenBackendTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
