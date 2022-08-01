# -*- coding: utf-8 -*-
#
# Copyright © 2022 Erol Keskin <erolkeskin.dev@gmail.com>
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

"""
Anitya tests for the cgit backend.
"""

import unittest

import anitya.lib.backends.cgit as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "cgit"


class CgitBackendtests(DatabaseTestCase):
    """cgit backend tests."""

    def setUp(self):
        """Set up the environment, ran before every tests."""
        super(CgitBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        self.projects = {}

        project = models.Project(
            homepage="https://git.zx2c4.com/cgit",
            name="cgit",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_homepage"] = project

        project = models.Project(
            homepage="https://www.gnu.org/software/gnuzilla",
            name="GNUzilla",
            version_url="https://git.savannah.gnu.org/cgit/gnuzilla.git",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_version_url"] = project

        project = models.Project(
            homepage="https://git.savannah.gnu.org/cgit/alisp.git",
            name="A list implementation",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_without_release"] = project

        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the cgit backend."""

        project = self.projects["valid_with_homepage"]
        exp = "v1.2.3"
        obs = backend.CgitBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["valid_with_version_url"]
        exp = "v60.7.0"
        obs = backend.CgitBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["valid_without_release"]
        self.assertRaises(
            AnityaPluginException, backend.CgitBackend.get_version, project
        )

    def test_get_version_url_project_homepage_only(self):
        """
        Assert that correct url is returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = "https://git.zx2c4.com/cgit/refs/tags"
        obs = backend.CgitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_slash_homepage(self):
        """
        Assert that correct url is returned
        when homepage is ending with slash
        """

        project = models.Project(homepage="https://git.zx2c4.com/cgit/")
        exp = "https://git.zx2c4.com/cgit/refs/tags"
        obs = backend.CgitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url_only(self):
        """
        Assert that correct url is returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = "https://git.savannah.gnu.org/cgit/gnuzilla.git/refs/tags"
        obs = backend.CgitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_slash_version_url(self):
        """
        Assert that correct url is returned
        when version_url is ending with slash
        """
        project = models.Project(
            version_url="https://git.savannah.gnu.org/cgit/gnuzilla.git/"
        )
        exp = "https://git.savannah.gnu.org/cgit/gnuzilla.git/refs/tags"
        obs = backend.CgitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_homepage_only(self):
        """
        Assert that correct versions are returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = [
            "v0.1",
            "v0.2",
            "v0.3",
            "v0.4",
            "v0.5",
            "v0.6",
            "v0.6.1",
            "v0.6.2",
            "v0.6.3",
            "v0.7",
            "v0.7.1",
            "v0.7.2",
            "v0.8",
            "v0.8.1",
            "v0.8.1.1",
            "v0.8.2",
            "v0.8.2.1",
            "v0.8.2.2",
            "v0.8.3",
            "v0.8.3.1",
            "v0.8.3.2",
            "v0.8.3.3",
            "v0.8.3.4",
            "v0.8.3.5",
            "v0.9",
            "v0.9.0.1",
            "v0.9.0.2",
            "v0.9.0.3",
            "v0.9.1",
            "v0.9.2",
            "v0.10",
            "v0.10.1",
            "v0.10.2",
            "v0.11.0",
            "v0.11.1",
            "v0.11.2",
            "v0.12",
            "v1.0",
            "v1.1",
            "v1.2",
            "v1.2.1",
            "v1.2.2",
            "v1.2.3",
        ]
        obs = backend.CgitBackend.get_ordered_versions(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_version_url_only(self):
        """
        Assert that correct versions are returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = [
            "v31.2.0",
            "v31.4.0",
            "v31.5.0",
            "v31.6.0",
            "v31.8.0",
            "v38.3.0",
            "v45.7.0",
            "v52.0.2",
            "v52.1.0",
            "v60.2.0",
            "v60.3.0",
            "v60.7.0",
        ]
        obs = backend.CgitBackend.get_ordered_versions(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_without_any_release(self):
        """
        Assert that exception is thrown
        when no release found for project
        """

        project = self.projects["valid_without_release"]
        self.assertRaises(
            AnityaPluginException, backend.CgitBackend.get_versions, project
        )


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(CgitBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
