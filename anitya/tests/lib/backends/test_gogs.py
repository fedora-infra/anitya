# -*- coding: utf-8 -*-
#
# Copyright © 2022 Erol Keskin
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
Anitya tests for the GitLab backend.
"""

import unittest

import anitya.lib.backends.gogs as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "Gogs"


class GogsBackendtests(DatabaseTestCase):
    """BitBucket backend tests."""

    def setUp(self):
        """Set up the environment, ran before every tests."""
        super(GogsBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        self.projects = {}

        project = models.Project(
            name="libreboot",
            homepage="https://notabug.org/libreboot/lbmk",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_homepage"] = project

        project = models.Project(
            name="lbwww",
            homepage="https://libreboot.org",
            version_url="https://notabug.org/libreboot/lbwww",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_version_url"] = project

        project = models.Project(
            name="osboot",
            homepage="https://notabug.org/osboot/osbmk",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_without_release"] = project

        project = models.Project(
            name="invalid url",
            backend=BACKEND,
            homepage="https://gogs.io/project_with_malformed_url",
        )
        self.session.add(project)
        self.projects["invalid_homepage"] = project

        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the Gogs backend."""

        project = self.projects["valid_with_homepage"]
        exp = "20220710"
        obs = backend.GogsBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["valid_with_version_url"]
        exp = "20220710"
        obs = backend.GogsBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["valid_without_release"]
        self.assertRaises(
            AnityaPluginException, backend.GogsBackend.get_version, project
        )

        project = self.projects["invalid_homepage"]
        self.assertRaises(
            AnityaPluginException, backend.GogsBackend.get_version, project
        )

    def test_get_version_url_project_homepage_only(self):
        """
        Assert that correct url is returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = "https://notabug.org/libreboot/lbmk/releases"
        obs = backend.GogsBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_slash_homepage(self):
        """
        Assert that correct url is returned
        when homepage is ending with slash
        """

        project = models.Project(homepage="https://gogs.io/group/project/")
        exp = "https://gogs.io/group/project/releases"
        obs = backend.GogsBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url_only(self):
        """
        Assert that correct url is returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = "https://notabug.org/libreboot/lbwww/releases"
        obs = backend.GogsBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_slash_version_url(self):
        """
        Assert that correct url is returned
        when version_url is ending with slash
        """
        project = models.Project(version_url="https://gogs.io/group/project/")
        exp = "https://gogs.io/group/project/releases"
        obs = backend.GogsBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_invalid_homepage(self):
        """
        Assert that empty url is returned
        when project has invalid url
        """

        project = self.projects["invalid_homepage"]
        obs = backend.GogsBackend.get_version_url(project)

        self.assertEqual(obs, "")

    def test_get_versions_project_homepage_only(self):
        """
        Assert that correct versions are returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = ["20210522", "20211122", "20220710"]
        obs = backend.GogsBackend.get_ordered_versions(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_version_url_only(self):
        """
        Assert that correct versions are returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = ["20211122", "20220710"]
        obs = backend.GogsBackend.get_ordered_versions(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_invalid_homepage(self):
        """
        Assert that exception is thrown
        when invalid homepage is specified
        """

        project = self.projects["invalid_homepage"]
        self.assertRaises(
            AnityaPluginException, backend.GogsBackend.get_versions, project
        )

    def test_get_versions_project_without_any_release(self):
        """
        Assert that exception is thrown
        when no release found for project
        """

        project = self.projects["valid_without_release"]
        self.assertRaises(
            AnityaPluginException, backend.GogsBackend.get_versions, project
        )


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GogsBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
