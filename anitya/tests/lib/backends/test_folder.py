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
anitya tests for the folder backend.
"""

import unittest

import mock

import anitya.lib.backends.folder as backend  # NOQA
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException  # NOQA
from anitya.tests.base import DatabaseTestCase, create_distro  # NOQA

BACKEND = "folder"


class FolderBackendtests(DatabaseTestCase):
    """folder backend tests."""

    def setUp(self):
        """Set up the environnment, ran before every tests."""
        super(FolderBackendtests, self).setUp()

        create_distro(self.session)

    def test_get_version_gnash(self):
        """
        Assert that latest version of the gnash project is received correctly.
        """
        project = models.Project(
            name="gnash",
            homepage="https://www.gnu.org/software/gnash/",
            version_url="https://ftp.gnu.org/pub/gnu/gnash/",
            backend=BACKEND,
        )

        exp = "0.8.10"
        obs = backend.FolderBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_subsurface(self):
        """
        Assert that latest version of the subsurface project is received correctly.
        """
        project = models.Project(
            name="subsurface",
            homepage="https://subsurface-divelog.org/",
            version_url="https://subsurface-divelog.org/downloads/",
            backend=BACKEND,
        )

        exp = "4.9.10"
        obs = backend.FolderBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_phpMyAdmin(self):
        """
        Assert that latest version of the phpMyAdmin project is received correctly.
        """
        project = models.Project(
            name="subsurface",
            homepage="https://www.phpmyadmin.net/",
            version_url="https://www.phpmyadmin.net/files/",
            backend=BACKEND,
        )

        exp = "5.1.0"
        obs = backend.FolderBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_url(self):
        """Assert that correct url is returned."""
        project = models.Project(
            name="test",
            homepage="http://example.org",
            version_url="http://example.org/releases",
            backend=BACKEND,
        )
        exp = project.version_url

        obs = backend.FolderBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_folder_get_versions_insecure(self):
        """Assert projects with insecure=True get the URL insecurely"""
        project = models.Project(
            name="test",
            homepage="http://example.org",
            version_url="http://example.org/releases",
            backend=BACKEND,
            insecure=True,
        )

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.side_effect = backend.BaseBackend.call_url
            self.assertRaises(
                AnityaPluginException, backend.FolderBackend.get_versions, project
            )
            m_call.assert_called_with(
                project.version_url, last_change=None, insecure=True
            )

    def test_folder_get_versions_not_modified(self):
        """Assert that not modified response is handled correctly"""
        project = models.Project(
            name="test",
            homepage="http://example.org",
            version_url="http://example.org/releases",
            backend=BACKEND,
            insecure=True,
        )

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.return_value = mock.Mock(status_code=304)
            versions = backend.FolderBackend.get_versions(project)

            m_call.assert_called_with(
                project.version_url, last_change=None, insecure=True
            )
            self.assertEqual(versions, [])

    def test_get_versions_gnash(self):
        """
        Assert that versions of the gnash project is received correctly.
        """
        project = models.Project(
            name="gnash",
            homepage="https://www.gnu.org/software/gnash/",
            version_url="https://ftp.gnu.org/pub/gnu/gnash/",
            backend=BACKEND,
        )

        exp = [
            "0.7.1",
            "0.7.2",
            "0.8.0",
            "0.8.1",
            "0.8.10",
            "0.8.2",
            "0.8.3",
            "0.8.4",
            "0.8.5",
            "0.8.6",
            "0.8.7",
            "0.8.8",
            "0.8.9",
        ]
        obs = backend.FolderBackend.get_versions(project)
        self.assertEqual(sorted(obs), exp)

    def test_get_versions_subsurface(self):
        """
        Assert that versions of the subsurface project is received correctly.
        """
        project = models.Project(
            name="subsurface",
            homepage="https://subsurface-divelog.org/",
            version_url="https://subsurface-divelog.org/downloads/",
            backend=BACKEND,
        )

        exp = [
            "3.1.1",
            "4.0",
            "4.0.1",
            "4.0.2",
            "4.0.3",
            "4.1",
            "4.2",
            "4.3",
            "4.4.0",
            "4.4.1",
            "4.4.2",
            "4.5.0",
            "4.5.1",
            "4.5.2",
            "4.5.3",
            "4.5.4",
            "4.5.5",
            "4.5.6",
            "4.6.0",
            "4.6.1",
            "4.6.2",
            "4.6.3",
            "4.6.4",
            "4.7.1",
            "4.7.2",
            "4.7.3",
            "4.7.4",
            "4.7.5",
            "4.7.6",
            "4.7.7",
            "4.7.8",
            "4.8.0",
            "4.8.1",
            "4.8.2",
            "4.8.3",
            "4.8.4",
            "4.8.5",
            "4.8.6",
            "4.9.0",
            "4.9.1",
            "4.9.10",
            "4.9.2",
            "4.9.3",
            "4.9.4",
            "4.9.5",
            "4.9.6",
            "4.9.7",
            "4.9.8",
            "4.9.9",
        ]
        obs = backend.FolderBackend.get_versions(project)
        self.assertEqual(sorted(obs), exp)

    def test_get_versions_phpMyAdmin(self):
        """
        Assert that versions of the phpMyAdmin project is received correctly.
        This test case is for https://github.com/fedora-infra/anitya/issues/1056
        """
        project = models.Project(
            name="subsurface",
            homepage="https://www.phpmyadmin.net/",
            version_url="https://www.phpmyadmin.net/files/",
            backend=BACKEND,
        )

        exp = [
            "0.9.0",
            "1.1.0",
            "1.2.0",
            "1.3.0",
            "1.3.1",
            "2.0.5",
            "2.1.0",
            "2.10.2",
            "2.10.3",
            "2.11.10.1",
            "2.11.11",
            "2.11.11.1",
            "2.11.11.2",
            "2.11.11.3",
            "2.2.0",
            "2.3.0",
            "2.4.0",
            "2.5.0",
            "2.6.0",
            "2.7.0",
            "2.8.0",
            "2.9.0",
            "3.0.0",
            "3.1.0",
            "3.2.0",
            "3.3.0",
            "3.3.10",
            "3.3.10.1",
            "3.3.10.2",
            "3.3.10.3",
            "3.3.10.4",
            "3.3.10.5",
            "3.3.5.1",
            "3.3.6",
            "3.3.7",
            "3.3.8",
            "3.3.8.1",
            "3.3.9",
            "3.3.9.1",
            "3.3.9.2",
            "3.4.0",
            "3.4.1",
            "3.4.10",
            "3.4.10.1",
            "3.4.10.2",
            "3.4.11",
            "3.4.11.1",
            "3.4.2",
            "3.4.3",
            "3.4.3.1",
            "3.4.3.2",
            "3.4.4",
            "3.4.5",
            "3.4.6",
            "3.4.7",
            "3.4.7.1",
            "3.4.8",
            "3.4.9",
            "3.5.0",
            "3.5.1",
            "3.5.2",
            "3.5.2.1",
            "3.5.2.2",
            "3.5.3",
            "3.5.4",
            "3.5.5",
            "3.5.6",
            "3.5.7",
            "3.5.8",
            "3.5.8.1",
            "3.5.8.2",
            "4.0.0",
            "4.0.1",
            "4.0.10",
            "4.0.10.1",
            "4.0.10.10",
            "4.0.10.11",
            "4.0.10.12",
            "4.0.10.13",
            "4.0.10.14",
            "4.0.10.15",
            "4.0.10.16",
            "4.0.10.17",
            "4.0.10.18",
            "4.0.10.19",
            "4.0.10.2",
            "4.0.10.20",
            "4.0.10.3",
            "4.0.10.4",
            "4.0.10.5",
            "4.0.10.6",
            "4.0.10.7",
            "4.0.10.8",
            "4.0.10.9",
            "4.0.2",
            "4.0.3",
            "4.0.4",
            "4.0.4.1",
            "4.0.4.2",
            "4.0.5",
            "4.0.6",
            "4.0.7",
            "4.0.8",
            "4.0.9",
            "4.1.0",
            "4.1.1",
            "4.1.10",
            "4.1.11",
            "4.1.12",
            "4.1.13",
            "4.1.14",
            "4.1.14.1",
            "4.1.14.2",
            "4.1.14.3",
            "4.1.14.4",
            "4.1.14.5",
            "4.1.14.6",
            "4.1.14.7",
            "4.1.14.8",
            "4.1.2",
            "4.1.3",
            "4.1.4",
            "4.1.5",
            "4.1.6",
            "4.1.7",
            "4.1.8",
            "4.1.9",
            "4.2.0",
            "4.2.1",
            "4.2.10",
            "4.2.10.1",
            "4.2.11",
            "4.2.12",
            "4.2.13",
            "4.2.13.1",
            "4.2.13.2",
            "4.2.13.3",
            "4.2.2",
            "4.2.3",
            "4.2.4",
            "4.2.5",
            "4.2.6",
            "4.2.7",
            "4.2.7.1",
            "4.2.8",
            "4.2.8.1",
            "4.2.9",
            "4.2.9.1",
            "4.3.0",
            "4.3.1",
            "4.3.10",
            "4.3.11",
            "4.3.11.1",
            "4.3.12",
            "4.3.13",
            "4.3.13.1",
            "4.3.13.2",
            "4.3.13.3",
            "4.3.2",
            "4.3.3",
            "4.3.4",
            "4.3.5",
            "4.3.6",
            "4.3.7",
            "4.3.8",
            "4.3.9",
            "4.4.0",
            "4.4.1",
            "4.4.1.1",
            "4.4.10",
            "4.4.11",
            "4.4.12",
            "4.4.13",
            "4.4.13.1",
            "4.4.14",
            "4.4.14.1",
            "4.4.15",
            "4.4.15.1",
            "4.4.15.10",
            "4.4.15.2",
            "4.4.15.3",
            "4.4.15.4",
            "4.4.15.5",
            "4.4.15.6",
            "4.4.15.7",
            "4.4.15.8",
            "4.4.15.9",
            "4.4.2",
            "4.4.3",
            "4.4.4",
            "4.4.5",
            "4.4.6",
            "4.4.6.1",
            "4.4.7",
            "4.4.8",
            "4.4.9",
            "4.5.0",
            "4.5.0.1",
            "4.5.0.2",
            "4.5.1",
            "4.5.2",
            "4.5.3",
            "4.5.3.1",
            "4.5.4",
            "4.5.4.1",
            "4.5.5",
            "4.5.5.1",
            "4.6.0",
            "4.6.0-alpha1",
            "4.6.0-rc1",
            "4.6.0-rc2",
            "4.6.1",
            "4.6.2",
            "4.6.3",
            "4.6.4",
            "4.6.5",
            "4.6.5.1",
            "4.6.5.2",
            "4.6.6",
            "4.7.0",
            "4.7.0-beta1",
            "4.7.0-rc1",
            "4.7.1",
            "4.7.2",
            "4.7.3",
            "4.7.4",
            "4.7.5",
            "4.7.6",
            "4.7.7",
            "4.7.8",
            "4.7.9",
            "4.8.0",
            "4.8.0-alpha1",
            "4.8.0-rc1",
            "4.8.0.1",
            "4.8.1",
            "4.8.2",
            "4.8.3",
            "4.8.4",
            "4.8.5",
            "4.9.0",
            "4.9.0.1",
            "4.9.1",
            "4.9.2",
            "4.9.3",
            "4.9.4",
            "4.9.5",
            "4.9.6",
            "4.9.7",
            "5.0.0",
            "5.0.0-alpha1",
            "5.0.0-rc1",
            "5.0.1",
            "5.0.2",
            "5.0.3",
            "5.0.4",
            "5.1.0",
            "5.1.0-rc1",
            "5.1.0-rc2",
        ]
        obs = backend.FolderBackend.get_versions(project)
        self.assertEqual(sorted(obs), exp)

    def test_get_versions_fake_project(self):
        """
        Assert that exception is raised when calling project that doesn't exists.
        """
        project = models.Project(
            name="fake",
            homepage="https://www.fake.com/",
            version_url="https://www.fake.com/files/",
            backend=BACKEND,
        )

        self.assertRaises(
            AnityaPluginException, backend.FolderBackend.get_version, project
        )


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FolderBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
