# -*- coding: utf-8 -*-
#
# Copyright © 2023 Erol Keskin <erolkeskin.dev@gmail.com>
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
Anitya tests for the Gitea backend.
"""

import unittest

import anitya.lib.backends.gitea as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "Gitea"


class GiteaBackendtests(DatabaseTestCase):
    """Gitea backend tests."""

    def setUp(self):
        """Set up the environment, ran before every tests."""
        super().setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        self.projects = {}

        project = models.Project(
            name="freedroid",
            homepage="https://codeberg.org/freedroid/freedroid-src.git",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_homepage"] = project

        project = models.Project(
            name="forgejo",
            homepage="https://forgejo.org/",
            version_url="https://codeberg.org/forgejo/forgejo",
            backend=BACKEND,
            releases_only=True,
        )
        self.session.add(project)
        self.projects["valid_with_version_url"] = project

        project = models.Project(
            name="invalid url",
            backend=BACKEND,
            homepage="https://gitea.com/project_with_malformed_url",
        )
        self.session.add(project)
        self.projects["invalid_homepage"] = project

        project = models.Project(
            name="invalid project",
            backend=BACKEND,
            homepage="https://gitea.com/project_with_malformed_url/invalid_project",
        )
        self.session.add(project)
        self.projects["invalid_owner_repo"] = project

        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the Gitea backend."""

        project = self.projects["valid_with_homepage"]
        exp = "1.0"
        obs = backend.GiteaBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["valid_with_version_url"]
        exp = "v1.20.4-0"
        obs = backend.GiteaBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["invalid_homepage"]
        self.assertRaises(
            AnityaPluginException, backend.GiteaBackend.get_version, project
        )

    def test_get_version_url_project_homepage_only(self):
        """
        Assert that correct url is returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = "https://codeberg.org/api/v1/repos/freedroid/freedroid-src/tags"
        obs = backend.GiteaBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_slash_homepage(self):
        """
        Assert that correct url is returned
        when homepage is ending with slash
        """

        project = models.Project(homepage="https://codeberg.org/dnkl/foot/")
        exp = "https://codeberg.org/api/v1/repos/dnkl/foot/tags"
        obs = backend.GiteaBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url_only(self):
        """
        Assert that correct url is returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = "https://codeberg.org/api/v1/repos/forgejo/forgejo/releases"
        obs = backend.GiteaBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_slash_version_url(self):
        """
        Assert that correct url is returned
        when version_url is ending with slash
        """
        project = models.Project(version_url="https://codeberg.org/dnkl/foot/")
        exp = "https://codeberg.org/api/v1/repos/dnkl/foot/tags"
        obs = backend.GiteaBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_invalid_homepage(self):
        """
        Assert that empty url is returned
        when project has invalid url
        """

        project = self.projects["invalid_homepage"]
        obs = backend.GiteaBackend.get_version_url(project)

        self.assertEqual(obs, "")

    def test_get_versions_project_homepage_only(self):
        """
        Assert that correct versions are returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = [
            "0.10.4+",
            "0.11rc1",
            "0.11",
            "0.12rc1",
            "0.12",
            "0.13rc1",
            "0.13rc2",
            "0.13",
            "0.14rc1",
            "0.14rc3",
            "0.14",
            "0.14.1",
            "0.15rc1",
            "0.15rc2",
            "0.15",
            "0.15.1",
            "0.16rc1",
            "0.16rc2",
            "0.16rc3",
            "0.16",
            "0.16.1",
            "1.0rc1",
            "1.0rc2",
            "1.0rc3",
            "1.0",
        ]
        obs = backend.GiteaBackend.get_ordered_versions(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_version_url_only(self):
        """
        Assert that correct versions are returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = [
            "v1.18.0-rc0",
            "v1.18.0-rc1-2",
            "v1.18.0-rc1-1",
            "v1.18.0-rc1",
            "v1.18.0-0",
            "v1.18.0-1",
            "v1.18.1-0",
            "v1.18.2-0",
            "v1.18.2-1",
            "v1.18.3-0",
            "v1.18.3-1",
            "v1.18.3-2",
            "v1.18.5-0",
            "v1.19.0-2",
            "v1.19.0-3",
            "v1.19.1-0",
            "v1.19.2-0",
            "v1.19.3-0",
            "v1.19.4-0",
            "v1.20.1-0",
            "v1.20.2-0",
            "v1.20.3-0",
            "v1.20.4-0",
        ]
        obs = backend.GiteaBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    def test_get_versions_project_invalid_homepage(self):
        """
        Assert that exception is thrown
        when invalid homepage is specified
        """

        project = self.projects["invalid_homepage"]
        self.assertRaises(
            AnityaPluginException, backend.GiteaBackend.get_versions, project
        )

    def test_get_versions_project_invalid_owner_repo(self):
        """
        Assert that exception is thrown
        when invalid owner/repository is specified
        """

        project = self.projects["invalid_owner_repo"]
        self.assertRaises(
            AnityaPluginException, backend.GiteaBackend.get_versions, project
        )


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GiteaBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
