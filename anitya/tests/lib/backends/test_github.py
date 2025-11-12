# -*- coding: utf-8 -*-
#
# Copyright © 2018  Red Hat, Inc.
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
anitya tests for the github backend.
"""

import unittest

import mock

import anitya.lib.backends.github as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException, RateLimitException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = "GitHub"


class GithubBackendtests(DatabaseTestCase):
    """Github backend tests."""

    def setUp(self):
        """Set up the environnment, ran before every tests."""
        super().setUp()

        create_distro(self.session)
        self.create_projects()

    def create_projects(self):
        """Create some basic projects to work with."""
        self.projects = {}
        self.expected_versions = {}

        project = models.Project(
            name="fedocal",
            homepage="https://github.com/fedora-infra/fedocal",
            version_url="fedora-infra/fedocal",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_with_version_url"] = project
        self.expected_versions["valid_with_version_url"] = [
            "v.0.4.6",
            "v0.1.0",
            "v0.1.1",
            "v0.1.2",
            "v0.2.0",
            "v0.3.0",
            "v0.3.1",
            "v0.4.0",
            "v0.4.1",
            "v0.4.2",
            "v0.4.3",
            "v0.4.5",
            "v0.4.7",
            "v0.5.0",
            "v0.5.1",
            "v0.6.0",
            "v0.6.1",
            "v0.6.2",
            "v0.6.3",
            "v0.7",
            "v0.7.1",
            "v0.8",
            "v0.9",
            "v0.9.1",
            "v0.9.2",
            "v0.9.3",
            "0.10",
            "0.11",
            "0.11.1",
            "0.12",
            "0.13",
            "0.13.1",
            "0.13.2",
            "0.13.3",
            "0.14",
            "0.15",
            "0.15.1",
            "0.16",
        ]

        project = models.Project(
            name="foobar",
            homepage="https://github.com/foo/bar",
            version_url="foobar/bar",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["invalid_unknown_project"] = project

        project = models.Project(
            name="pkgdb2",
            homepage="https://github.com/fedora-infra/pkgdb2/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_without_version_url"] = project
        self.expected_versions["valid_without_version_url"] = [
            "1.21",
            "1.22",
            "1.22.1",
            "1.22.2",
            "1.23",
            "1.23.99",
            "1.23.991",
            "1.23.992",
            "1.23.993",
            "1.23.994",
            "1.23.995",
            "1.24",
            "1.24.1",
            "1.24.2",
            "1.24.3",
            "1.25",
            "1.25.1",
            "1.26",
            "1.27",
            "1.28",
            "1.28.1",
            "1.28.2",
            "1.29",
            "1.30",
            "1.30.1",
            "1.31",
            "1.32",
            "1.32.1",
            "1.32.2",
            "1.33.0",
            "1.33.1",
            "1.33.2",
            "1.33.3",
            "2.0",
            "2.0.1",
            "2.0.2",
            "2.0.3",
            "2.1",
            "2.2",
            "2.3",
            "2.4",
            "2.4.1",
            "2.4.2",
            "2.4.3",
            "2.5",
            "2.6",
            "2.6.1",
            "2.6.2",
            "2.7",
            "2.7.1",
        ]

        project = models.Project(
            name="foobar", homepage="https://github.com/foo", backend=BACKEND
        )
        self.session.add(project)
        self.projects["invalid_url_path"] = project

        project = models.Project(
            name="foobar", homepage="http://github.com/foo/bar", backend=BACKEND
        )
        self.session.add(project)
        self.projects["invalid_url_scheme"] = project

        project = models.Project(
            name="fpdc",
            homepage="https://github.com/fedora-infra/fpdc",
            backend=BACKEND,
        )
        self.session.add(project)
        self.projects["valid_no_tags_releases"] = project

        self.session.flush()

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_version_valid_with_version_url(self):
        """Test get_version() with a project with version URL."""
        project = self.projects["valid_with_version_url"]
        exp = self.expected_versions["valid_with_version_url"][-1]
        obs = backend.GithubBackend.get_version(project)
        self.assertEqual(obs, exp)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_version_invalid_unknown_project(self):
        """Test get_version() with an unknown project."""
        project = self.projects["invalid_unknown_project"]
        with self.assertRaises(AnityaPluginException):
            backend.GithubBackend.get_version(project)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_version_valid_without_version_url(self):
        """Test get_version() with a project without version URL."""
        project = self.projects["valid_without_version_url"]
        exp = self.expected_versions["valid_without_version_url"][-1]
        obs = backend.GithubBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url(self):
        """
        Assert that correct url is returned when project version url is specified.
        """
        project = models.Project(
            name="test",
            homepage="http://example.org",
            version_url="test/test",
            backend=BACKEND,
        )
        exp = "https://github.com/test/test/tags"

        obs = backend.GithubBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_homepage_only(self):
        """
        Assert that correct url is returned when only
        project homepage is specified.
        """
        project = models.Project(
            name="test", homepage="https://github.com/test/test", backend=BACKEND
        )
        exp = "https://github.com/test/test/tags"

        obs = backend.GithubBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_wrong_homepage(self):
        """
        Assert that empty url is returned when
        project homepage is wrong.
        """
        project = models.Project(
            name="test", homepage="https://example.org", backend=BACKEND
        )
        exp = ""

        obs = backend.GithubBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_releases_only(self):
        """
        Assert that correct url is returned when
        releases_only is marked
        """
        project = models.Project(
            name="test",
            homepage="https://github.com/test/test",
            backend=BACKEND,
            releases_only=True,
        )
        exp = "https://github.com/test/test/releases"
        obs = backend.GithubBackend.get_version_url(project)
        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url_contains_tags(self):
        """
        Assert that correct url is returned when
        version_url contains tags
        """
        project = models.Project(
            name="Tags Repository", version_url="fedora-infra/tags", backend=BACKEND
        )
        exp = "https://github.com/fedora-infra/tags/tags"
        obs = backend.GithubBackend.get_version_url(project)
        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url_contains_releases(self):
        """test_get_version_url_project_version_url_contains_releases"""
        project = models.Project(
            name="Releases Repository",
            version_url="fedora-infra/releases",
            backend=BACKEND,
            releases_only=True,
        )
        exp = "https://github.com/fedora-infra/releases/releases"
        obs = backend.GithubBackend.get_version_url(project)
        self.assertEqual(obs, exp)

    def test_get_version_url_homepage_slash(self):
        """
        Assert that correct url is returned when
        project homepage ends with '/'.
        """
        project = models.Project(
            name="test", homepage="https://github.com/test/test/", backend=BACKEND
        )
        exp = "https://github.com/test/test/tags"

        obs = backend.GithubBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_version_url_slash(self):
        """
        Assert that correct url is returned when
        version url ends with '/'.
        """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            version_url="test/test/",
            backend=BACKEND,
        )
        exp = "https://github.com/test/test/tags"

        obs = backend.GithubBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_versions_valid_with_version_url(self):
        """Test get_versions() with a project with version URL."""
        project = self.projects["valid_with_version_url"]
        exp = self.expected_versions["valid_with_version_url"]
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_versions_invalid_unknown_project(self):
        """Test get_versions() with a valid latest known cursor."""
        project = self.projects["invalid_unknown_project"]
        with self.assertRaises(AnityaPluginException):
            backend.GithubBackend.get_versions(project)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_versions_valid_without_version_url(self):
        """Test get_versions() with a project without version URL."""
        project = self.projects["valid_without_version_url"]
        exp = self.expected_versions["valid_without_version_url"]
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    def test_get_versions_invalid_homepage_url_path(self):
        """Test get_versions() for an invalid homepage URL path.

        Paths for projects on GitHub must be `owner/project`."""
        project = self.projects["invalid_url_path"]
        with self.assertRaises(AnityaPluginException) as excinfo:
            backend.GithubBackend.get_versions(project)

        excstring = str(excinfo.exception)
        self.assertIn("Project foobar was incorrectly set up.", excstring)
        self.assertIn("Can't parse owner and repo.", excstring)

    def test_get_versions_invalid_homepage_url_scheme(self):
        """Test get_versions() for a project with invalid homepage URL scheme.

        GitHub projects have to use https://, not http://."""
        project = self.projects["invalid_url_scheme"]
        with self.assertRaises(AnityaPluginException) as excinfo:
            backend.GithubBackend.get_versions(project)

        excstring = str(excinfo.exception)
        self.assertIn("Project foobar was incorrectly set up.", excstring)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": None})
    def test_get_versions_no_token(self):
        """Test the get_versions function of the github backend
        without specified token.
        """
        project = self.projects["valid_with_version_url"]
        self.assertRaises(
            AnityaPluginException, backend.GithubBackend.get_versions, project
        )

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "Not_found"})
    def test_get_versions_unauthorized(self):
        """Test the get_versions function of the github backend
        with invalid token.
        """
        project = self.projects["valid_with_version_url"]
        self.assertRaises(
            AnityaPluginException, backend.GithubBackend.get_versions, project
        )

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "Not_found"})
    @mock.patch("anitya.lib.backends.github.API_URL", "foobar")
    def test_get_versions_invalid_url(self):
        """Test the get_versions function of the github backend
        with invalid URL.
        """
        project = self.projects["valid_with_version_url"]
        self.assertRaises(
            AnityaPluginException, backend.GithubBackend.get_versions, project
        )

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_versions_no_version_retrieved(self):
        """Test the get_versions function of the github backend
        with project which doesn't have any tag.
        """
        project = self.projects["valid_no_tags_releases"]
        self.assertRaises(
            AnityaPluginException, backend.GithubBackend.get_versions, project
        )

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    @mock.patch("anitya.lib.backends.http_session.post")
    def test_get_versions_403(self, mock_post):
        """Test the get_versions function of the github when response status code
        is 403.
        """
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 403
        mock_resp.ok = False
        mock_post.return_value = mock_resp
        project = self.projects["valid_without_version_url"]
        backend.reset_time = "1970-01-01T00:00:00Z"
        self.assertRaises(
            RateLimitException, backend.GithubBackend.get_versions, project
        )
        self.assertEqual(backend.reset_time, "1970-01-01T00:00:00Z")

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_plexus_utils(self):
        """Regression test for issue #286"""
        project = models.Project(
            version_url="codehaus-plexus/plexus-archiver",
            version_prefix="plexus-archiver-",
            backend=BACKEND,
        )
        version = backend.GithubBackend().get_version(project)
        self.assertEqual("plexus-archiver-3.6.0", version)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_get_versions_releases_only(self):
        """Test the get_versions functions with releases only."""
        project = models.Project(
            name="the-new-hotness",
            homepage="https://github.com/fedora-infra/the-new-hotness",
            version_url="fedora-infra/the-new-hotness",
            backend=BACKEND,
            releases_only=True,
        )
        exp = [
            "0.10.0",
            "0.10.1",
            "0.11.0",
            "0.11.1",
            "0.11.2",
            "0.11.3",
            "0.11.4",
            "0.11.5",
            "0.11.6",
            "0.11.7",
            "0.11.8",
            "0.11.9",
            "0.12.0",
        ]
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    @mock.patch.dict(
        "anitya.config.config",
        {"GITHUB_ACCESS_TOKEN": "foobar"},
    )
    def test_get_versions_filter(self):
        """Test the get_versions functions with releases only."""
        project = models.Project(
            name="the-new-hotness",
            homepage="https://github.com/fedora-infra/the-new-hotness",
            version_url="fedora-infra/the-new-hotness",
            backend=BACKEND,
            releases_only=True,
            version_filter=".9",
        )
        exp = [
            "0.10.0",
            "0.10.1",
            "0.11.0",
            "0.11.1",
            "0.11.2",
            "0.11.3",
            "0.11.4",
            "0.11.5",
            "0.11.6",
            "0.11.7",
            "0.11.8",
            "0.12.0",
            "0.13.0",
            "0.13.1",
            "0.13.2",
            "0.13.3",
            "0.13.4",
        ]
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


class JsonTests(unittest.TestCase):
    """
    Unit tests for json related functions
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None
        self.project = models.Project(
            name="foobar",
            homepage="https://foobar.com",
            version_url="foo/bar",
            backend=BACKEND,
        )

    def test_prepare_query(self):
        """Assert query creation"""
        exp = """
{
    repository(owner: "foo", name: "bar") {
        refs (refPrefix: "refs/tags/", orderBy: {field: TAG_COMMIT_DATE, direction: ASC}, last: 50) {
            totalCount
            edges {
                node {
                    name target { commitUrl }
                }
            }
        }
    }
    rateLimit {
        limit
        remaining
        resetAt
    }
}"""  # noqa: E501

        obs = backend.prepare_query("foo", "bar", False)
        self.assertEqual(exp, obs)

    def test_prepare_query_releases(self):
        """Assert query creation with releases_only set"""
        exp = """
{
    repository(owner: "foo", name: "bar") {
        releases (orderBy: {field: CREATED_AT, direction: ASC}, last: 50) {
            totalCount
            edges {
                node {
                    name tag { name target { commitUrl } }
                }
            }
        }
    }
    rateLimit {
        limit
        remaining
        resetAt
    }
}"""

        obs = backend.prepare_query("foo", "bar", True)
        self.assertMultiLineEqual(exp, obs)

    def test_parse_json(self):
        """Test parsing a JSON response without errors."""
        json = {
            "data": {
                "repository": {
                    "refs": {
                        "totalCount": 1,
                        "edges": [
                            {
                                "node": {
                                    "name": "1.0",
                                    "target": {
                                        "commitUrl": "https://foobar.com/foo/bar/commits/12345678"
                                    },
                                },
                            }
                        ],
                    },
                },
                "rateLimit": {"limit": 5000, "remaining": 5000, "resetAt": "dummy"},
            }
        }
        exp = [
            {
                "version": "1.0",
                "commit_url": "https://foobar.com/foo/bar/commits/12345678",
            }
        ]
        obs = backend.parse_json(json, self.project)
        self.assertEqual(exp, obs)

    def test_parse_json_with_errors(self):
        """Test parsing JSON flagging errors."""
        json = {"errors": [{"type": "FOO", "message": "BAR"}]}

        with self.assertRaises(AnityaPluginException) as excinfo:
            backend.parse_json(json, self.project)

        self.assertIn('"FOO": "BAR"', str(excinfo.exception))

    def test_parse_json_threshold_exceeded(self):
        """Test behavior when rate limit threshold is exceeded."""
        # Limit reached
        json = {
            "data": {
                "repository": {"refs": {"totalCount": 0}},
                "rateLimit": {
                    "limit": 5000,
                    "remaining": 0,
                    "resetAt": "2008-09-03T20:56:35.450686",
                },
            }
        }
        with self.assertRaises(RateLimitException):
            backend.parse_json(json, self.project)
        self.assertEqual(backend.reset_time, "2008-09-03T20:56:35.450686")

    def test_parse_json_tag_missing(self):
        """Test parsing a JSON skips releases where tag is missing."""
        project = models.Project(
            name="foobar",
            homepage="https://foobar.com",
            version_url="foo/bar",
            backend=BACKEND,
            releases_only=True,
        )
        json = {
            "data": {
                "repository": {
                    "releases": {
                        "totalCount": 1,
                        "edges": [
                            {
                                "node": {"name": "This is a release", "tag": None},
                            },
                        ],
                    },
                },
                "rateLimit": {"limit": 5000, "remaining": 5000, "resetAt": "dummy"},
            }
        }
        obs = backend.parse_json(json, project)
        self.assertEqual([], obs)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GithubBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
