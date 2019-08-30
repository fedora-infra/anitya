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
    """ folder backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FolderBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = models.Project(
            name="gnash",
            homepage="https://www.gnu.org/software/gnash/",
            version_url="https://ftp.gnu.org/pub/gnu/gnash/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="fake",
            homepage="https://pypi.python.org/pypi/repo_manager_fake",
            backend=BACKEND,
            insecure=True,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="subsurface",
            homepage="https://subsurface-divelog.org/",
            version_url="https://subsurface-divelog.org/downloads/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_folder_get_version(self):
        """ Test the get_version function of the folder backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "0.8.10"
        obs = backend.FolderBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.FolderBackend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = "4.7.7"
        obs = backend.FolderBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_url(self):
        """ Assert that correct url is returned. """
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
        pid = 2
        project = models.Project.get(self.session, pid)

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
        pid = 2
        project = models.Project.get(self.session, pid)

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.return_value = mock.Mock(status_code=304)
            versions = backend.FolderBackend.get_versions(project)

            m_call.assert_called_with(
                project.version_url, last_change=None, insecure=True
            )
            self.assertEqual(versions, [])

    def test_folder_get_versions(self):
        """ Test the get_versions function of the folder backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            "0.7.1",
            "0.7.2",
            "0.8.0",
            "0.8.1",
            "0.8.2",
            "0.8.3",
            "0.8.4",
            "0.8.5",
            "0.8.6",
            "0.8.7",
            "0.8.8",
            "0.8.9",
            "0.8.10",
        ]
        obs = backend.FolderBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.FolderBackend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
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
        ]
        obs = backend.FolderBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FolderBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
