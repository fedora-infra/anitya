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
Anitya tests for the SourceHut backend.
"""

import unittest

import mock

import anitya.lib.backends.sourcehut as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "SourceHut"


class SourceHutBackendTests(DatabaseTestCase):
    """SourceHut backend tests."""

    def setUp(self):
        """Set up the environment, ran before every tests."""
        super().setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        self.projects = {}

        project = models.Project(
            homepage="https://git.sr.ht/~sircmpwn/builds.sr.ht/",
            name="builds.sr.ht",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_homepage"] = project

        project = models.Project(
            homepage="scdoc",
            name="scdoc",
            version_url="sircmpwn/scdoc",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_version_url"] = project

        project = models.Project(
            homepage="https://git.sr.ht/~sircmpwn/hare",
            name="hare",
            version_url="sircmpwn/hare",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_without_release"] = project

        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the SourceHut backend."""

        project = self.projects["valid_with_homepage"]
        exp = "0.82.8"
        obs = backend.SourceHutBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["valid_with_version_url"]
        exp = "1.11.2"
        obs = backend.SourceHutBackend.get_version(project)
        self.assertEqual(obs, exp)

        project = self.projects["valid_without_release"]
        self.assertRaises(
            AnityaPluginException, backend.SourceHutBackend.get_version, project
        )

    def test_get_version_url_project_homepage_only(self):
        """
        Assert that correct url is returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = "https://git.sr.ht/~sircmpwn/builds.sr.ht/refs/rss.xml"
        obs = backend.SourceHutBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url_only(self):
        """
        Assert that correct url is returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = "https://git.sr.ht/~sircmpwn/scdoc/refs/rss.xml"
        obs = backend.SourceHutBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_versions_invalid_url(self):
        """
        Assert that exception is raised
        when invalid url is specified
        """
        project = models.Project(
            homepage="https://git.sr.ht/~",
            name="invalid",
            backend=BACKEND,
        )

        self.assertRaises(
            AnityaPluginException, backend.SourceHutBackend.get_versions, project
        )

    def test_get_versions_invalid_status_code(self):
        """
        Assert that exception is raised
        when invalid url is specified
        """
        project = models.Project(
            homepage="https://git.sr.ht/~sircmpwn/hare",
            name="invalid",
            backend=BACKEND,
        )
        exp_url = "https://git.sr.ht/~sircmpwn/hare/refs/rss.xml"

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.return_value = mock.Mock(status_code=404)
            self.assertRaises(
                AnityaPluginException, backend.SourceHutBackend.get_versions, project
            )

            m_call.assert_called_with(exp_url, None)

    def test_get_versions_not_modified(self):
        """
        Assert that get_version behave correctly
        when url returns response with 304 status code
        """
        project = models.Project(
            homepage="https://git.sr.ht/~sircmpwn/hare",
            name="invalid",
            backend=BACKEND,
        )
        exp_url = "https://git.sr.ht/~sircmpwn/hare/refs/rss.xml"

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.return_value = mock.Mock(status_code=304)
            versions = backend.SourceHutBackend.get_versions(project)

            m_call.assert_called_with(exp_url, None)
            self.assertEqual(versions, [])

    def test_get_versions_project_homepage_only(self):
        """
        Assert that correct versions are returned
        when only homepage is specified
        """

        project = self.projects["valid_with_homepage"]
        exp = [
            "0.82.7",
            "0.82.6",
            "0.82.8",
            "0.82.3",
            "0.82.4",
            "0.82.2",
            "0.82.1",
            "0.81.2",
            "0.82.5",
            "0.82.0",
            "0.81.1",
            "0.81.0",
            "0.80.0",
            "0.79.2",
            "0.79.1",
            "0.79.0",
            "0.78.0",
            "0.77.0",
            "0.76.0",
            "0.75.3",
        ]
        obs = backend.SourceHutBackend.get_versions(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_version_url_only(self):
        """
        Assert that correct versions are returned
        when only version_url is specified
        """

        project = self.projects["valid_with_version_url"]
        exp = [
            "1.11.2",
            "1.11.1",
            "1.11.0",
            "1.10.1",
            "1.10.0",
            "1.9.7",
            "1.9.6",
            "1.9.5",
            "1.9.4",
            "1.9.3",
            "1.9.2",
            "1.9.1",
            "1.9.0",
            "1.8.1",
            "1.8.0",
            "1.6.1",
            "1.6.0",
            "1.5.2",
            "1.5.1",
            "1.5.0",
        ]
        obs = backend.SourceHutBackend.get_versions(project)

        self.assertEqual(obs, exp)

    def test_get_versions_project_without_any_release(self):
        """
        Assert that exception is thrown
        when no release found for project
        """

        project = self.projects["valid_without_release"]
        self.assertRaises(
            AnityaPluginException, backend.SourceHutBackend.get_versions, project
        )


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(SourceHutBackendTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
