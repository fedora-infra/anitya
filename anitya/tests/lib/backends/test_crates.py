# -*- coding: utf-8 -*-
#
# Copyright © 2017  Red Hat, Inc.
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
"""
Tests for the :mod:`anitya.lib.backends.crates` module.
"""

from __future__ import unicode_literals

import unittest

import mock

from anitya.db import models
from anitya.lib.backends import crates
from anitya.lib.exceptions import AnityaPluginException, RateLimitException
from anitya.tests.base import DatabaseTestCase


class CratesBackendTests(DatabaseTestCase):
    """Crates backend tests."""

    def setUp(self):
        """Set up the environnment, run before every test"""
        super().setUp()
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        project1 = models.Project(
            name="itoa", homepage="https://crates.io/crates/itoa", backend="crates.io"
        )
        project2 = models.Project(
            name="pleasedontmakethisprojectitllbreakmytests",
            homepage="https://crates.io/crates/somenonsensehomepage",
            backend="crates.io",
        )
        self.session.add(project1)
        self.session.add(project2)
        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the crates backend."""
        project = models.Project.by_id(self.session, 1)
        self.assertEqual("1.0.18", crates.CratesBackend.get_version(project))

    def test_get_version_missing(self):
        """Assert an exception is raised if a project doesn't exist and get_version is called"""
        project = models.Project.get(self.session, 2)
        self.assertRaises(
            AnityaPluginException, crates.CratesBackend.get_version, project
        )

    def test_get_version_url(self):
        """Assert that correct sparse index url is returned."""
        cases = [
            ("a", "https://index.crates.io/1/a"),
            ("ab", "https://index.crates.io/2/ab"),
            ("syn", "https://index.crates.io/3/s/syn"),
            ("test", "https://index.crates.io/te/st/test"),
            ("zgvariant", "https://index.crates.io/zg/va/zgvariant"),
            ("MyCrate", "https://index.crates.io/my/cr/mycrate"),
        ]
        for name, exp in cases:
            project = models.Project(
                name=name, homepage="http://example.org", backend="crates.io"
            )
            obs = crates.CratesBackend.get_version_url(project)
            self.assertEqual(obs, exp)

    def test_get_versions(self):
        """Test the get_versions function of the crates backend."""
        project = models.Project.by_id(self.session, 1)
        versions = crates.CratesBackend.get_versions(project)
        self.assertEqual("1.0.18", versions[0])
        self.assertEqual("0.1.0", versions[-1])
        self.assertIn("0.2.1", versions)

    def test_get_ordered_versions(self):
        """Test the get_ordered_versions function of the crates backend."""
        project = models.Project.by_id(self.session, 1)
        versions = crates.CratesBackend.get_ordered_versions(project)
        self.assertEqual("1.0.18", versions[0])
        self.assertEqual("0.1.0", versions[-1])
        self.assertIn("0.2.1", versions)

    @mock.patch("anitya.lib.backends.crates.CratesBackend.call_url")
    def test__get_versions_no_json(self, mock_call_url):
        """Assert we handle getting non-JSON responses gracefully"""
        mock_call_url.return_value.status_code = 200
        mock_call_url.return_value.text = "not a json string\n"
        project = models.Project.by_id(self.session, 1)
        with self.assertRaises(AnityaPluginException) as cm:
            crates.CratesBackend._get_versions(project)  # pylint: disable=W0212
        self.assertIn("Failed to decode JSON", str(cm.exception))

    def test_get_versions_not_modified(self):
        """Assert that not modified response is handled correctly"""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp_url = "https://index.crates.io/it/oa/itoa"

        with mock.patch("anitya.lib.backends.BaseBackend.call_url") as m_call:
            m_call.return_value = mock.Mock(status_code=304)
            versions = crates.CratesBackend.get_versions(project)

            m_call.assert_called_with(exp_url, last_change=None)
            self.assertEqual(versions, [])

    @mock.patch("anitya.lib.backends.crates.CratesBackend.call_url")
    def test__get_versions_rate_limited(self, mock_call_url):
        """Assert 429 response raises RateLimitException."""
        mock_call_url.return_value.status_code = 429
        mock_call_url.return_value.headers = {"Retry-After": "60"}
        project = models.Project.by_id(self.session, 1)
        with self.assertRaises(RateLimitException):
            crates.CratesBackend._get_versions(project)

    @mock.patch("anitya.lib.backends.crates.CratesBackend.call_url")
    def test__get_versions_rate_limited_default(self, mock_call_url):
        """Assert 429 response without Retry-After defaults to 1 hour."""
        mock_call_url.return_value.status_code = 429
        mock_call_url.return_value.headers = {}
        project = models.Project.by_id(self.session, 1)
        with self.assertRaises(RateLimitException):
            crates.CratesBackend._get_versions(project)

    @mock.patch("anitya.lib.backends.crates.CratesBackend.call_url")
    def test__get_versions_rate_limited_http_date(self, mock_call_url):
        """Assert 429 response with HTTP-date Retry-After is parsed."""
        mock_call_url.return_value.status_code = 429
        mock_call_url.return_value.headers = {
            "Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"
        }
        project = models.Project.by_id(self.session, 1)
        with self.assertRaises(RateLimitException):
            crates.CratesBackend._get_versions(project)

    @mock.patch("anitya.lib.backends.crates.CratesBackend.call_url")
    def test__get_versions_rate_limited_invalid_date(self, mock_call_url):
        """Assert 429 response with invalid Retry-After date falls back to 1 hour."""
        mock_call_url.return_value.status_code = 429
        mock_call_url.return_value.headers = {"Retry-After": "not-a-valid-date"}
        project = models.Project.by_id(self.session, 1)
        with self.assertRaises(RateLimitException):
            crates.CratesBackend._get_versions(project)

    @mock.patch("anitya.lib.backends.crates.CratesBackend.call_url")
    def test_get_versions_yanked_filtered(self, mock_call_url):
        """Assert yanked versions are excluded."""
        mock_call_url.return_value.status_code = 200
        mock_call_url.return_value.text = (
            '{"name":"foo","vers":"1.0.0","yanked":false}\n'
            '{"name":"foo","vers":"1.0.1","yanked":true}\n'
            '{"name":"foo","vers":"1.1.0","yanked":false}\n'
        )
        project = models.Project(
            name="foo", homepage="https://crates.io/crates/foo", backend="crates.io"
        )
        self.assertEqual(["1.1.0", "1.0.0"], crates.CratesBackend.get_versions(project))
        self.assertEqual("1.1.0", crates.CratesBackend.get_version(project))

    @mock.patch("anitya.lib.backends.crates.CratesBackend.call_url")
    def test_get_version_all_yanked(self, mock_call_url):
        """Assert AnityaPluginException when no active versions found."""
        mock_call_url.return_value.status_code = 200
        mock_call_url.return_value.text = (
            '{"name":"foo","vers":"1.0.0","yanked":true}\n'
        )
        project = models.Project(
            name="foo", homepage="https://crates.io/crates/foo", backend="crates.io"
        )
        with self.assertRaises(AnityaPluginException):
            crates.CratesBackend.get_version(project)

    def test_is_url_valid(self):
        """Test the is_url_valid function of the crates backend."""
        self.assertTrue(
            crates.CratesBackend.is_url_valid("https://crates.io/crates/clap/")
        )
        self.assertFalse(crates.CratesBackend.is_url_valid("https://example.com"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
