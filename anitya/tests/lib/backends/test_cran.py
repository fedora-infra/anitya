# -*- coding: utf-8 -*-
#
# Copyright © 2018  Elliott Sales de Andrade
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

'''
anitya tests for the CRAN backend.
'''

import anitya.lib.backends.cran as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = 'CRAN (R)'


class CranBackendTests(DatabaseTestCase):
    """CRAN backend tests."""

    def setUp(self):
        """Set up the environment, ran before every tests."""
        super(CranBackendTests, self).setUp()

        create_distro(self.session)

    def test_get_version_missing_project(self):
        """Assert an AnityaPluginException is raised for projects that result in 404."""
        project = models.Project(
            name='non-existent-name-that-cannot-exist',
            homepage='https://cran.r-project.org/web/packages/non-existent-name-that-cannot-exist/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        self.assertRaises(
            AnityaPluginException,
            backend.CranBackend.get_version,
            project
        )

    def test_get_version(self):
        """Test the get_version function of the CRAN backend."""
        project = models.Project(
            name='whisker',
            homepage='https://github.com/edwindj/whisker',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        obs = backend.CranBackend.get_version(project)
        self.assertEqual(obs, '0.3-2')

    def test_get_versions_missing_project(self):
        """Assert an AnityaPluginException is raised for projects that result in 404."""
        project = models.Project(
            name='non-existent-name-that-cannot-exist',
            homepage='https://cran.r-project.org/web/packages/non-existent-name-that-cannot-exist/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        self.assertRaises(
            AnityaPluginException,
            backend.CranBackend.get_versions,
            project
        )

    def test_get_versions(self):
        """ Test the get_versions function of the CRAN backend. """
        project = models.Project(
            name='whisker',
            homepage='https://github.com/edwindj/whisker',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        obs = backend.CranBackend.get_ordered_versions(project)
        self.assertEqual(obs, ['0.1', '0.3-2'])

    def test_check_feed(self):
        """ Test the check_feed method of the CRAN backend. """
        generator = backend.CranBackend.check_feed()
        items = list(generator)

        self.assertEqual(items[0], (
            'xtractomatic',
            'https://github.com/rmendels/xtractomatic',
            'CRAN (R)', '3.4.2'))
        self.assertEqual(items[1], (
            'FedData',
            'https://github.com/ropensci/FedData',
            'CRAN (R)', '2.5.2'))
        # etc...
