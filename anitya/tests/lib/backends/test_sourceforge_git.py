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
anitya tests for the Sourceforge (git) backend.
"""

import unittest

import anitya.lib.backends.sourceforge_git as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = "Sourceforge (git)"


class SourceforgeGitBackendtests(DatabaseTestCase):
    """Sourceforge (git) backend tests."""

    def setUp(self):
        """Set up the environnment, ran before every tests."""
        super(SourceforgeGitBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        project = models.Project(
            name="flightgear",
            homepage="https://sourceforge.net/p/flightgear/flightgear/ci/master/tree/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="foobar",
            homepage="https://sourceforge.net/p/foobar/foobar/ci/master/tree/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="file-folder-ren",
            homepage="https://sourceforge.net/p/file-folder-ren/ci/master/tree/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the sourceforge backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "2.2.0-rc1"
        obs = backend.SourceforgeGitBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.SourceforgeGitBackend.get_version, project
        )

    def test_get_version_url(self):
        """
        Assert that correct url is returned.
        """
        project = models.Project(
            name="test",
            homepage="https://example.org",
            version_url="https://sourceforge.net/p/test_name/ref/master/tags",
            backend=BACKEND,
        )
        exp = "https://sourceforge.net/p/test_name/ref/master/tags"

        obs = backend.SourceforgeGitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_missing_version_url(self):
        """
        Assert that correct url is returned when project version url
        is missing.
        """
        project = models.Project(
            name="test",
            homepage="https://sourceforge.net/p/test/ci/master/tree",
            backend=BACKEND,
        )
        exp = "https://sourceforge.net/p/test/git/ref/master/tags/"

        obs = backend.SourceforgeGitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_version_url_plus(self):
        """
        Assert that correct url is returned when project version url
        contains '+'.
        """
        project = models.Project(
            name="test",
            homepage="https://sourceforge.net/p/test/ci/master/tree",
            version_url="test+name",
            backend=BACKEND,
        )
        exp = r"https://sourceforge.net/p/test\+name/git/ref/master/tags/"

        obs = backend.SourceforgeGitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_name_plus(self):
        """
        Assert that correct url is returned when project name
        contains '+'.
        """
        project = models.Project(
            name="test+", homepage="https://example.org", backend=BACKEND
        )
        exp = r"https://sourceforge.net/p/test\+/git/ref/master/tags/"

        obs = backend.SourceforgeGitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_version_url_name(self):
        """
        Assert that correct url is returned when project name
        contains '+'.
        """
        project = models.Project(
            name="test",
            homepage="https://example.org",
            version_url="test_version_url",
            backend=BACKEND,
        )
        exp = r"https://sourceforge.net/p/test_version_url/git/ref/master/tags/"

        obs = backend.SourceforgeGitBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """Test the get_versions function of the sourceforge backend."""
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            "2.2.0-rc1",
            "JSBSim/v1.1.1",
            "last-automake",
            "last-cvs",
            "master-20100117",
            "master-20100125",
            "release/2018.3.5",
            "remove-ATCDCL",
            "v2.0.0",
            "v2.0.0-bits",
            "v2.0.0-rc1",
            "v2.0.0-rc2",
            "v2.0.0-rc3",
            "v2.0.0-rc4",
            "version/2.10.0",
            "version/2.10.0-final",
            "version/2.11.0",
            "version/2.12.0",
            "version/2.4.0",
            "version/2.4.0-final",
            "version/2.5.0",
            "version/2.6.0",
            "version/2.6.0-final",
            "version/2.7.0",
            "version/2.8.0",
            "version/2.8.0-final",
            "version/2.9.0",
            "version/2016.1.0",
            "version/2016.1.1",
            "version/2016.1.2",
            "version/2016.2.0",
            "version/2016.2.1",
            "version/2016.3.0",
            "version/2016.3.1",
            "version/2016.4.0",
            "version/2016.4.1",
            "version/2016.4.3",
            "version/2016.4.4",
            "version/2017.1.0",
            "version/2017.1.1",
            "version/2017.1.2",
            "version/2017.1.3",
            "version/2017.2.0",
            "version/2017.2.1",
            "version/2017.3.0",
            "version/2017.3.1",
            "version/2017.4.0",
            "version/2018.1.1",
            "version/2018.2.0",
            "version/2018.2.1",
            "version/2018.3.0",
            "version/2018.3.3",
            "version/2018.3.4",
            "version/2018.3.5",
            "version/2018.3.6",
            "version/2019.1.2",
            "version/2020.1.2",
            "version/2020.1.3",
            "version/2020.3.1",
            "version/2020.3.2",
            "version/2020.3.3",
            "version/2020.3.4",
            "version/2020.3.5",
            "version/2020.3.6",
            "version/2020.3.7",
            "version/2020.3.8",
            "version/2020.3.9",
            "version/3.0.0",
            "version/3.0.0-final",
            "version/3.1.0",
            "version/3.2.0",
            "version/3.3.0",
            "version/3.4.0",
            "version/3.4.0-final",
            "version/3.5.0",
            "version/3.6.0",
            "version/3.7.0",
        ]
        obs = backend.SourceforgeGitBackend.get_ordered_versions(project)
        self.assertEqual(sorted(obs), exp)

    def test_get_versions_url_not_valid(self):
        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.SourceforgeGitBackend.get_versions, project
        )

    def test_get_namespace_repo_homepage(self):
        """
        Assert that correct namespace and repo is returned.
        """
        project = models.Project(
            name="flightgear",
            homepage="https://sourceforge.net/p/flightgear/flightgear/ci/next/tree/",
            backend=BACKEND,
        )
        exp = "flightgear", "flightgear"

        obs = backend.SourceforgeGitBackend.get_namespace_repo(project)

        self.assertEqual(obs, exp)

    def test_get_namespace_repo_version_url(self):
        """
        Assert that correct namespace and repo is returned.
        """
        project = models.Project(
            name="flightgear",
            homepage="https://sourceforge.net/p/flightgear/flightgear/ci/next/tree/",
            version_url="https://sourceforge.net/p/flightgear/flightgear/ref/next/tags/",
            backend=BACKEND,
        )
        exp = "flightgear", "flightgear"

        obs = backend.SourceforgeGitBackend.get_namespace_repo(project)

        self.assertEqual(obs, exp)

    def test_get_namespace_repo_project_name(self):
        """
        Assert that correct namespace and repo is returned.
        """
        project = models.Project(
            name="eclipse-cs", homepage="https://www.example.org", backend=BACKEND
        )
        exp = "eclipse-cs", "git"

        obs = backend.SourceforgeGitBackend.get_namespace_repo(project)

        self.assertEqual(obs, exp)

    def test_get_namespace_repo_project_name_plus(self):
        """
        Assert that correct namespace and repo is returned.
        """
        project = models.Project(
            name="eclipse+cs", homepage="https://www.example.org", backend=BACKEND
        )
        exp = r"eclipse\+cs", "git"

        obs = backend.SourceforgeGitBackend.get_namespace_repo(project)

        self.assertEqual(obs, exp)

    def test_get_namespace_repo_homepage_sourceforge(self):
        """
        Assert that correct namespace and repo is returned.
        """
        project = models.Project(
            name="flightgear",
            homepage="https://sourceforge.net/p/flightgear/flightgear/ci/next/tree/",
            backend=BACKEND,
        )
        exp = "flightgear", "flightgear"

        obs = backend.SourceforgeGitBackend.get_namespace_repo(project)

        self.assertEqual(obs, exp)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(SourceforgeGitBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
