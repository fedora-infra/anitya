# -*- coding: utf-8 -*-
#
# Copyright © 2014-2019  Red Hat, Inc.
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

import mock

import anitya.lib.backends.npmjs as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "npmjs"


class NpmjsBackendtests(DatabaseTestCase):
    """Drupal backend tests."""

    def setUp(self):
        """Set up the environnment, ran before every tests."""
        super().setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        project = models.Project(
            name="request",
            homepage="https://www.npmjs.org/package/request",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="non-existent-package-that-does-not-exist",
            homepage="https://www.npmjs.org/package/non-existent-package-that-does-not-exist",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="colors",
            homepage="https://www.npmjs.org/package/colors",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the npmjs backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "2.83.0"
        obs = backend.NpmjsBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.NpmjsBackend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = "1.2.0"
        obs = backend.NpmjsBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_url(self):
        """
        Assert that correct url is returned.
        """
        project = models.Project(
            name="test", homepage="https://example.org", backend=BACKEND
        )
        exp = "https://registry.npmjs.org/test"

        obs = backend.NpmjsBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_not_modified(self):
        """Assert that not modified response is handled correctly"""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp_url = "https://registry.npmjs.org/request"

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.return_value = mock.Mock(status_code=304)
            versions = backend.NpmjsBackend.get_version(project)

            m_call.assert_called_with(exp_url, last_change=None)
            self.assertEqual(versions, None)

    def test_get_versions(self):
        """Test the get_versions function of the npmjs backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            "0.8.3",
            "0.9.0",
            "0.9.1",
            "0.9.5",
            "0.10.0",
            "1.0.0",
            "1.1.0",
            "1.1.1",
            "1.2.0",
            "1.9.0",
            "1.9.1",
            "1.9.2",
            "1.9.3",
            "1.9.5",
            "1.9.7",
            "1.9.8",
            "1.9.9",
            "2.0.0",
            "2.0.1",
            "2.0.2",
            "2.0.3",
            "2.0.4",
            "2.0.5",
            "2.1.0",
            "2.1.1",
            "2.2.0",
            "2.2.5",
            "2.2.6",
            "2.2.9",
            "2.9.0",
            "2.9.1",
            "2.9.2",
            "2.9.3",
            "2.9.100",
            "2.9.150",
            "2.9.151",
            "2.9.152",
            "2.9.153",
            "2.9.200",
            "2.9.201",
            "2.9.202",
            "2.9.203",
            "2.10.0",
            "2.11.0",
            "2.11.1",
            "2.11.2",
            "2.11.3",
            "2.11.4",
            "2.12.0",
            "2.14.0",
            "2.16.0",
            "2.16.2",
            "2.16.4",
            "2.16.6",
            "2.18.0",
            "2.19.0",
            "2.20.0",
            "2.21.0",
            "2.22.0",
            "2.23.0",
            "2.24.0",
            "2.25.0",
            "2.26.0",
            "2.27.0",
            "2.28.0",
            "2.29.0",
            "2.30.0",
            "2.31.0",
            "2.32.0",
            "2.33.0",
            "2.34.0",
            "2.35.0",
            "2.36.0",
            "2.37.0",
            "2.38.0",
            "2.39.0",
            "2.40.0",
            "2.41.0",
            "2.42.0",
            "2.43.0",
            "2.44.0",
            "2.45.0",
            "2.46.0",
            "2.47.0",
            "2.48.0",
            "2.49.0",
            "2.50.0",
            "2.51.0",
            "2.52.0",
            "2.53.0",
            "2.54.0",
            "2.55.0",
            "2.56.0",
            "2.57.0",
            "2.58.0",
            "2.59.0",
            "2.60.0",
            "2.61.0",
            "2.62.0",
            "2.63.0",
            "2.64.0",
            "2.65.0",
            "2.66.0",
            "2.67.0",
            "2.68.0",
            "2.69.0",
            "2.70.0",
            "2.71.0",
            "2.72.0",
            "2.73.0",
            "2.74.0",
            "2.75.0",
            "2.76.0",
            "2.77.0",
            "2.78.0",
            "2.79.0",
            "2.80.0",
            "2.81.0",
            "2.82.0",
            "2.83.0",
        ]
        obs = backend.NpmjsBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.NpmjsBackend.get_versions, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = [
            "0.3.0",
            "0.5.0",
            "0.5.1",
            "0.6.0",
            "0.6.0-1",
            "0.6.1",
            "0.6.2",
            "1.0.0",
            "1.0.1",
            "1.0.2",
            "1.0.3",
            "1.1.0",
            "1.1.1",
            "1.1.2",
            "1.2.0-rc0",
            "1.2.0",
        ]
        obs = backend.NpmjsBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    def test_get_versions_not_modified(self):
        """Assert that not modified response is handled correctly"""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp_url = "https://registry.npmjs.org/request"

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.return_value = mock.Mock(status_code=304)
            versions = backend.NpmjsBackend.get_versions(project)

            m_call.assert_called_with(exp_url, last_change=None)
            self.assertEqual(versions, [])

    def test_npmjs_check_feed(self):
        """Test the check_feed method of the npmjs backend."""
        generator = backend.NpmjsBackend.check_feed()
        items = sorted(generator)

        self.assertEqual(
            items[0],
            (
                "2d-density",
                "https://github.com/nilestanner/2d-density#readme",
                "npmjs",
                "1.0.0",
            ),
        )
        self.assertEqual(
            items[1],
            (
                "2d-density",
                "https://github.com/nilestanner/2d-density#readme",
                "npmjs",
                "1.0.1",
            ),
        )
        self.assertEqual(
            items[2],
            (
                "angular-stackblitz",
                "https://npmjs.org/package/angular-stackblitz",
                "npmjs",
                "0.0.0",
            ),
        )
        # etc...


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(NpmjsBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
