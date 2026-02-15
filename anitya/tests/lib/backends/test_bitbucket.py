# -*- coding: utf-8 -*-
#
# Copyright © 2015  Red Hat, Inc.
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
anitya tests for the bitbucket backend.
"""

import unittest
from unittest.mock import Mock, patch

import anitya.lib.backends.bitbucket as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "BitBucket"


class BitBucketBackendtests(DatabaseTestCase):
    """BitBucket backend tests."""

    def setUp(self):
        """Set up the environnment, ran before every tests."""
        super().setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        project = models.Project(
            name="sqlalchemy",
            homepage="https://bitbucket.org/zzzeek/sqlalchemy",
            version_url="zzzeek/sqlalchemy",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="foobar",
            homepage="https://bitbucket.org/foo/bar",
            version_url="foobar/bar",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="cherrypy",
            homepage="https://bitbucket.org/cherrypy/cherrypy",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    @patch("anitya.lib.backends.bitbucket.requests.get")
    def test_get_version(self, mock_get):
        """Test the get_version function of the BitBucket backend."""
        mock_response = Mock()
        # The Anitya sorter orders versions ascending, so the "latest" is at the end.
        mock_response.json.return_value = {
            "values": [{"name": "rel_1_1_2"}, {"name": "rel_1_1_3"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "rel_1_1_3"
        obs = backend.BitBucketBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        # Simulate a network failure or bad request for project 2
        mock_get.side_effect = Exception("Network Error")
        self.assertRaises(
            AnityaPluginException, backend.BitBucketBackend.get_version, project
        )
        mock_get.side_effect = None  # Reset the side effect for the next test

        mock_response.json.return_value = {
            "values": [{"name": "5.1.0"}, {"name": "v5.2.0"}]
        }
        mock_get.return_value = mock_response
        pid = 3
        project = models.Project.get(self.session, pid)
        exp = "v5.2.0"
        obs = backend.BitBucketBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_url_only_homepage(self):
        """
        Assert that correct url is returned when only
        homepage is specified.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://bitbucket.org/cherrypy/cherrypy",
            backend=BACKEND,
        )
        exp = "https://api.bitbucket.org/2.0/repositories/cherrypy/cherrypy/refs/tags?sort=-target.date"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url(self):
        """
        Assert that correct url is returned when
        version_url is specified.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://example.org",
            version_url="https://bitbucket.org/cherrypy/cherrypy",
            backend=BACKEND,
        )
        exp = "https://api.bitbucket.org/2.0/repositories/cherrypy/cherrypy/refs/tags?sort=-target.date"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_slash_homepage(self):
        """
        Assert that correct url is returned when
        homepage ends with /.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://bitbucket.org/cherrypy/cherrypy/",
            backend=BACKEND,
        )
        exp = "https://api.bitbucket.org/2.0/repositories/cherrypy/cherrypy/refs/tags?sort=-target.date"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_slash_version_url(self):
        """
        Assert that correct url is returned when
        version_url ends with /.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://example.org",
            version_url="https://bitbucket.org/cherrypy/cherrypy/",
            backend=BACKEND,
        )
        exp = "https://api.bitbucket.org/2.0/repositories/cherrypy/cherrypy/refs/tags?sort=-target.date"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_wrong_homepage(self):
        """
        Assert that correct url is returned when wrong
        homepage is provided.
        """
        project = models.Project(
            name="cherrypy", homepage="https://wrong.org", backend=BACKEND
        )
        exp = ""

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    @patch("anitya.lib.backends.bitbucket.requests.get")
    def test_get_versions(self, mock_get):
        """Test the get_versions function of the BitBucket backend."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "values": [{"name": "rel_1_1_2"}, {"name": "rel_1_1_3"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        pid = 1
        project = models.Project.get(self.session, pid)
        exp = ["rel_1_1_2", "rel_1_1_3"]
        obs = backend.BitBucketBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        mock_get.side_effect = Exception("Network Error")
        self.assertRaises(
            AnityaPluginException, backend.BitBucketBackend.get_versions, project
        )
        mock_get.side_effect = None

        mock_response.json.return_value = {
            "values": [{"name": "5.1.0"}, {"name": "v5.2.0"}]
        }
        mock_get.return_value = mock_response
        pid = 3
        project = models.Project.get(self.session, pid)
        exp = ["5.1.0", "v5.2.0"]
        obs = backend.BitBucketBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(BitBucketBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
