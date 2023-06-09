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

"""
anitya tests for the custom backend.
"""

import unittest

import anitya.lib.backends.drupal7 as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "Drupal7"


class Drupal7Backendtests(DatabaseTestCase):
    """Drupal backend tests."""

    def setUp(self):
        """Set up the environnment, ran before every tests."""
        super().setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        project = models.Project(
            name="wysiwyg",
            homepage="https://www.drupal.org/project/wysiwyg",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="foo", homepage="https://pecl.php.net/package/foo", backend=BACKEND
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="admin_menu",
            homepage="https://www.drupal.org/project/admin_menu",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the debian backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "2.2"
        obs = backend.Drupal7Backend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.Drupal7Backend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = "3.0-rc5"
        obs = backend.Drupal7Backend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_url(self):
        """Assert that correct url is returned."""
        project = models.Project(
            name="test",
            homepage="http://example.org",
            version_url="http://example.org/releases",
            backend=BACKEND,
        )
        exp = "https://updates.drupal.org/release-history/test/7.x"

        obs = backend.Drupal7Backend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_drupal7_prefix(self):
        """
        Assert that correct url is returned when project name has 'drupal7:' prefix.
        """
        project = models.Project(
            name="drupal7:test",
            homepage="http://example.org",
            version_url="http://example.org/releases",
            backend=BACKEND,
        )
        exp = "https://updates.drupal.org/release-history/test/7.x"

        obs = backend.Drupal7Backend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_contains_dash(self):
        """
        Assert that correct url is returned when project name contains '-'.
        """
        project = models.Project(
            name="te-st",
            homepage="http://example.org",
            version_url="http://example.org/releases",
            backend=BACKEND,
        )
        exp = "https://updates.drupal.org/release-history/te_st/7.x"

        obs = backend.Drupal7Backend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """Test the get_versions function of the debian backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = ["2.x-dev", "2.0", "2.1", "2.2"]
        obs = backend.Drupal7Backend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.Drupal7Backend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = ["3.x-dev", "3.0-rc1", "3.0-rc2", "3.0-rc3", "3.0-rc4", "3.0-rc5"]
        obs = backend.Drupal7Backend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Drupal7Backendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
