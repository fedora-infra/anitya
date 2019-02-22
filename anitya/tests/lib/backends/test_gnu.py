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

import anitya.lib.backends.gnu as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = "GNU project"


class GnuBackendtests(DatabaseTestCase):
    """ custom backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(GnuBackendtests, self).setUp()

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

    def test_custom_get_version(self):
        """ Test the get_version function of the custom backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "0.8.10"
        obs = backend.GnuBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.GnuBackend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.GnuBackend.get_version, project
        )

    def test_get_version_url(self):
        """ Assert that correct url is returned. """
        project = models.Project(
            name="test", homepage="http://example.org", backend=BACKEND
        )
        exp = "https://ftp.gnu.org/gnu/test/"

        obs = backend.GnuBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_custom_get_versions(self):
        """ Test the get_versions function of the custom backend. """
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
        obs = backend.GnuBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.GnuBackend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.GnuBackend.get_version, project
        )


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GnuBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
