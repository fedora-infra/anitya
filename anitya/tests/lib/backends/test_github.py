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

'''
anitya tests for the github backend.
'''

import unittest

import mock

import anitya.lib.backends.github as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException, RateLimitException
from anitya.tests.base import DatabaseTestCase, create_distro

BACKEND = 'GitHub'


class GithubBackendtests(DatabaseTestCase):
    """ Github backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(GithubBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = models.Project(
            name='fedocal',
            homepage='https://github.com/fedora-infra/fedocal',
            version_url='fedora-infra/fedocal',
            backend=BACKEND,
        )
        self.session.add(project)

        project = models.Project(
            name='foobar',
            homepage='https://github.com/foo/bar',
            version_url='foobar/bar',
            backend=BACKEND,
        )
        self.session.add(project)

        project = models.Project(
            name='pkgdb2',
            homepage='https://github.com/fedora-infra/pkgdb2/',
            backend=BACKEND,
        )
        self.session.add(project)

        project = models.Project(
            name='foobar',
            homepage='https://github.com/foo',
            backend=BACKEND,
        )
        self.session.add(project)

        project = models.Project(
            name='foobar',
            homepage='http://github.com/foo/bar',
            backend=BACKEND,
        )
        self.session.add(project)

        project = models.Project(
            name='fpdc',
            homepage='https://github.com/fedora-infra/fpdc',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    @mock.patch.dict('anitya.config.config', {'GITHUB_ACCESS_TOKEN': "foobar"})
    def test_get_version(self):
        """ Test the get_version function of the github backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = '0.16'
        obs = backend.GithubBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_version,
            project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = '2.7.1'
        obs = backend.GithubBackend.get_version(project)
        self.assertEqual(obs, exp)

    @mock.patch.dict('anitya.config.config', {'GITHUB_ACCESS_TOKEN': "foobar"})
    def test_get_versions(self):
        """ Test the get_versions function of the github backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            u'0.1.0', u'0.1.1', u'0.1.2', u'0.2.0',
            u'0.3.0', u'0.3.1', u'0.4.0', u'0.4.1',
            u'0.4.2', u'0.4.3', u'0.4.5', u'.0.4.6',
            u'0.4.7', u'0.5.0', u'0.5.1', u'0.6.0',
            u'0.6.1', u'0.6.2', u'0.6.3', u'0.7',
            u'0.7.1', u'0.8', u'0.9', u'0.9.1',
            u'0.9.2', u'0.9.3', u'0.10', u'0.11',
            u'0.11.1', u'0.12', u'0.13', u'0.13.1',
            u'0.13.2', u'0.13.3', u'0.14', u'0.15',
            u'0.15.1', u'0.16'
        ]
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = [
            u'1.21', u'1.22', u'1.22.1', u'1.22.2',
            u'1.23', u'1.23.99', u'1.23.991', u'1.23.992',
            u'1.23.993', u'1.23.994', u'1.23.995', u'1.24',
            u'1.24.1', u'1.24.2', u'1.24.3', u'1.25',
            u'1.25.1', u'1.26', u'1.27', u'1.28',
            u'1.28.1', u'1.28.2', u'1.29', u'1.30',
            u'1.30.1', u'1.31', u'1.32', u'1.32.1',
            u'1.32.2', u'1.33.0', u'1.33.1', u'1.33.2',
            u'1.33.3', u'2.0', u'2.0.1', u'2.0.2', u'2.0.3',
            u'2.1', u'2.2', u'2.3', u'2.4', u'2.4.1', u'2.4.2',
            u'2.4.3', u'2.5', u'2.6', u'2.6.1',
            u'2.6.2', u'2.7', u'2.7.1'
        ]
        obs = backend.GithubBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 4
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

        pid = 5
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

    @mock.patch.dict('anitya.config.config', {'GITHUB_ACCESS_TOKEN': None})
    def test_get_versions_no_token(self):
        """ Test the get_versions function of the github backend
        without specified token.
        """
        pid = 1
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

    @mock.patch.dict('anitya.config.config', {'GITHUB_ACCESS_TOKEN': "Not_found"})
    def test_get_versions_unauthorized(self):
        """ Test the get_versions function of the github backend
        with invalid token.
        """
        pid = 1
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

    @mock.patch.dict('anitya.config.config', {'GITHUB_ACCESS_TOKEN': "Not_found"})
    @mock.patch('anitya.lib.backends.github.API_URL', "foobar")
    def test_get_versions_invalid_url(self):
        """ Test the get_versions function of the github backend
        with invalid URL.
        """
        pid = 1
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

    @mock.patch.dict('anitya.config.config', {'GITHUB_ACCESS_TOKEN': "foobar"})
    def test_get_versions_no_version_retrieved(self):
        """ Test the get_versions function of the github backend
        with project which doesn't have any tag.
        """
        pid = 6
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GithubBackend.get_versions,
            project
        )

    @mock.patch.dict('anitya.config.config', {'GITHUB_ACCESS_TOKEN': "foobar"})
    def test_plexus_utils(self):
        """ Regression test for issue #286 """
        project = models.Project(
            version_url='codehaus-plexus/plexus-archiver',
            version_prefix='plexus-archiver-',
        )
        version = backend.GithubBackend().get_version(project)
        self.assertEqual(u'3.6.0', version)


class JsonTests(unittest.TestCase):
    """
    Unit tests for json related functions
    """
    def __init__(self, *args, **kwargs):
        super(JsonTests, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_prepare_query_after(self):
        """ Assert query creation with cursor """
        exp = '''
{
    repository(owner: "foo", name: "bar") {
        refs (refPrefix: "refs/tags/", last:50,
                orderBy:{field:TAG_COMMIT_DATE, direction:ASC}, after: "abc") {
            totalCount
            edges {
                cursor
                node {
                    name
                    target {
                        commitUrl
                    }
                }
            }
        }
    }
    rateLimit {
        limit
        remaining
        resetAt
    }
}'''

        obs = backend.prepare_query("foo", "bar", "abc")
        self.assertMultiLineEqual(exp, obs)

    def test_prepare_query(self):
        """ Assert query creation """
        exp = '''
{
    repository(owner: "foo", name: "bar") {
        refs (refPrefix: "refs/tags/", last:50,
                orderBy:{field:TAG_COMMIT_DATE, direction:ASC}) {
            totalCount
            edges {
                cursor
                node {
                    name
                    target {
                        commitUrl
                    }
                }
            }
        }
    }
    rateLimit {
        limit
        remaining
        resetAt
    }
}'''

        obs = backend.prepare_query("foo", "bar")
        self.assertEqual(exp, obs)

    def test_parse_json(self):
        """ Assert parsing json"""
        project = models.Project(
            name='foobar',
            homepage='https://foobar.com',
            version_url='foo/bar',
            backend=BACKEND,
        )
        json = {
            "errors": [
                {
                    "type": "FOO",
                    "message": "BAR"
                }
            ]
        }

        self.assertRaises(
            AnityaPluginException,
            backend.parse_json,
            json,
            project
        )

        # Limit reached
        json = {
            "data": {
                "repository": {
                    "refs": {
                        "totalCount": 0
                    }
                },
                "rateLimit": {
                    "remaining": 0,
                    "resetAt": "dummy"
                }
            }
        }
        self.assertRaises(
            RateLimitException,
            backend.parse_json,
            json,
            project
        )

        json = {
            "data": {
                "repository": {
                    "refs": {
                        "totalCount": 1,
                        "edges": [
                            {
                                "node": {
                                    "name": "1.0"
                                }
                            }
                        ]
                    }
                },
                "rateLimit": {
                    "remaining": 5000,
                    "resetAt": "dummy"
                }
            }
        }
        exp = [u'1.0']
        obs = backend.parse_json(json, project)
        self.assertEqual(exp, obs)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GithubBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
