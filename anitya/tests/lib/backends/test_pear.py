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
from unittest import mock

import anitya.lib.backends.pear as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "PEAR"


class PearBackendtests(DatabaseTestCase):
    """Pear backend tests."""

    def setUp(self):
        """Set up the environnment, ran before every tests."""
        super().setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        project = models.Project(
            name="PHP-UML",
            homepage="https://pear.php.net/package/PHP_UML",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="foo", homepage="https://pear.php.net/package/foo", backend=BACKEND
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the custom backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "1.6.2"
        obs = backend.PearBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.PearBackend.get_version, project
        )

        pid = 1
        project = models.Project.get(self.session, pid)
        with mock.patch.object(backend.PearBackend, "get_versions", return_value=[]):
            self.assertRaises(
                AnityaPluginException, backend.PearBackend.get_version, project
            )

    def test_get_version_url(self):
        """
        Assert that correct url is returned.
        """
        project = models.Project(
            name="test", homepage="https://example.org", backend=BACKEND
        )
        exp = "https://pear.php.net/rest/r/test/allreleases.xml"

        obs = backend.PearBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_dash(self):
        """
        Assert that correct url is returned when project name contains '-'.
        """
        project = models.Project(
            name="te-st", homepage="https://example.org", backend=BACKEND
        )
        exp = "https://pear.php.net/rest/r/te_st/allreleases.xml"

        obs = backend.PearBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """Test the get_versions function of the custom backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            "0.4.2",
            "0.4.4",
            "0.5.0",
            "0.5.1",
            "0.5.2",
            "0.5.3",
            "1.0.0",
            "1.0.1",
            "1.5.0",
            "1.5.1",
            "1.5.2",
            "1.5.3",
            "1.5.4",
            "1.5.5",
            "1.6.0",
            "1.6.1",
            "1.6.2",
        ]
        obs = backend.PearBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.PearBackend.get_version, project
        )

    def test_pear_check_feed(self):
        """Test the check_feed method of the pear backend."""
        generator = backend.PearBackend.check_feed()
        items = list(generator)

        self.assertEqual(
            items[0],
            (
                "File_Therion",
                "https://pear.php.net/package/File_Therion",
                "PEAR",
                "0.1.0",
            ),
        )
        self.assertEqual(
            items[1],
            ("Net_URL2", "https://pear.php.net/package/Net_URL2", "PEAR", "2.1.2"),
        )
        # etc...

    @mock.patch("anitya.lib.backends.pear.PearBackend.call_url")
    def test_pear_check_feed_single_item(self, mock_call):
        """Test check_feed handles single-item feed without TypeError."""
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
            ' xmlns="http://purl.org/rss/1.0/">'
            "<channel><title>PEAR</title></channel>"
            "<item><title>Auth 1.2.3</title></item>"
            "</rdf:RDF>"
        )
        mock_resp = mock.Mock()
        mock_resp.text = xml
        mock_call.return_value = mock_resp

        items = list(backend.PearBackend.check_feed())
        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0],
            ("Auth", "https://pear.php.net/package/Auth", "PEAR", "1.2.3"),
        )

    @mock.patch("anitya.lib.backends.pear.PearBackend.call_url")
    def test_pear_check_feed_invalid_title(self, mock_call):
        """Test check_feed handles unparseable titles gracefully without crashing."""
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
            ' xmlns="http://purl.org/rss/1.0/">'
            "<channel><title>PEAR</title></channel>"
            "<item><title>InvalidTitleWithoutVersion</title></item>"
            "<item><title>PHP_UML 1.6.2</title></item>"
            "<item><title></title></item>"
            "<item><description>Item without title tag</description></item>"
            "</rdf:RDF>"
        )
        mock_resp = mock.Mock()
        mock_resp.text = xml
        mock_call.return_value = mock_resp

        items = list(backend.PearBackend.check_feed())
        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0],
            ("PHP_UML", "https://pear.php.net/package/PHP_UML", "PEAR", "1.6.2"),
        )

    @mock.patch("anitya.lib.backends.pear.PearBackend.call_url")
    def test_pear_check_feed_empty(self, mock_call):
        """Test check_feed handles empty feed without KeyError."""
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
            ' xmlns="http://purl.org/rss/1.0/">'
            "<channel><title>PEAR</title></channel>"
            "</rdf:RDF>"
        )
        mock_resp = mock.Mock()
        mock_resp.text = xml
        mock_call.return_value = mock_resp

        items = list(backend.PearBackend.check_feed())
        self.assertEqual(len(items), 0)

    def test_is_url_valid(self):
        """Test the is_url_valid function of the Pear backend."""
        self.assertTrue(
            backend.PearBackend.is_url_valid("https://pear.php.net/package/Auth/")
        )
        self.assertTrue(
            backend.PearBackend.is_url_valid("http://pear.php.net/package/Auth/")
        )
        self.assertTrue(
            backend.PearBackend.is_url_valid("https://pear.php.net/package/PHP_UML")
        )
        self.assertFalse(backend.PearBackend.is_url_valid("https://example.com"))

    def test_parse_url(self):
        """Test the parse_url function of the Pear backend."""
        cases = [
            ("https://pear.php.net/package/Auth", "Auth"),
            ("https://pear.php.net/package/Auth/", "Auth"),
            ("http://pear.php.net/package/Auth", "Auth"),
            ("https://pear.php.net/package/Auth/1.2.3", "Auth"),
            ("https://pear.php.net/package/Auth-1.2.3", "Auth"),
            ("https://pear.php.net/package/Auth/download", "Auth"),
            ("https://pear.php.net/package-info.php?package=Auth", "Auth"),
            (
                "https://pear.php.net/package-info.php?package=Auth&view=releases",
                "Auth",
            ),
            (
                "https://pear.php.net/package/Auth?view=releases#changelog",
                "Auth",
            ),
            ("https://pear.php.net/other/Auth", "Auth"),
        ]
        for url, exp_name in cases:
            with self.subTest(url=url):
                output = backend.PearBackend.parse_url(url)
                exp = {
                    "name": exp_name,
                    "homepage": f"https://pear.php.net/package/{exp_name}",
                    "backend": "PEAR",
                    "version_url": f"https://pear.php.net/package/{exp_name}",
                    "version_scheme": "RPM",
                }
                self.assertEqual(output, exp)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PearBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
