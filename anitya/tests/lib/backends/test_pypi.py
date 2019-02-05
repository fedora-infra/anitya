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
anitya tests for the pypi backend.
"""

import anitya.lib.backends.pypi as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = "PyPI"


class PypiBackendtests(DatabaseTestCase):
    """ pypi backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(PypiBackendtests, self).setUp()

        create_distro(self.session)

    def test_get_version_missing_project(self):
        """Assert an AnityaPluginException is raised for projects that result in 404."""
        project = models.Project(
            name="repo_manager_fake",
            homepage="https://pypi.org/project/repo_manager_fake/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        self.assertRaises(
            AnityaPluginException, backend.PypiBackend.get_version, project
        )

    def test_pypi_get_version(self):
        """ Test the get_version function of the pypi backend. """
        project = models.Project(
            name="chai", homepage="https://pypi.org/project/chai/", backend=BACKEND
        )
        self.session.add(project)
        self.session.commit()

        obs = backend.PypiBackend.get_version(project)
        self.assertEqual(obs, "1.1.2")

    def test_get_version_url(self):
        """
        Assert that correct url is returned.
        """
        project = models.Project(
            name="test", homepage="https://example.org", backend=BACKEND
        )
        exp = "https://pypi.org/pypi/test/json"

        obs = backend.PypiBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_pypi_get_versions(self):
        """ Test the get_versions function of the pypi backend. """
        project = models.Project(
            name="repo_manager",
            homepage="https://pypi.org/project/repo_manager/",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()
        exp = ["0.1.0"]

        obs = backend.PypiBackend.get_versions(project)
        self.assertEqual(obs, exp)

    def test_pypi_check_feed(self):
        """ Test the check_feed method of the pypi backend. """
        generator = backend.PypiBackend.check_feed()
        items = list(generator)

        self.assertEqual(
            items[0],
            ("simplemdx", "https://pypi.org/project/simplemdx/", "PyPI", "0.1.2"),
        )
        self.assertEqual(
            items[1],
            (
                "tapioca-trustwave-appscanner",
                "https://pypi.org/project/tapioca-trustwave-appscanner/",
                "PyPI",
                "0.3",
            ),
        )
