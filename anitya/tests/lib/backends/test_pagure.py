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

'''
anitya tests for the pagure backend.
'''

import unittest

import anitya.lib.backends.pagure as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = 'pagure'


class PagureBackendtests(DatabaseTestCase):
    """ pagure backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(PagureBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = models.Project(
            name='pagure',
            homepage='https://pagure.io/pagure',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name='fake',
            homepage='https://pagure.io/fake',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_pagure_get_version(self):
        """ Test the get_version function of the pagure backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = '0.1.16'
        obs = backend.PagureBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.PagureBackend.get_version,
            project
        )

    def test_pagure_get_versions(self):
        """ Test the get_versions function of the pagure backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            '0.1', '0.1.1', '0.1.10', '0.1.11', '0.1.12', '0.1.13', '0.1.14',
            '0.1.15', '0.1.16', '0.1.2', '0.1.3', '0.1.4', '0.1.5', '0.1.6',
            '0.1.7', '0.1.8', '0.1.9']
        obs = backend.PagureBackend.get_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.PagureBackend.get_versions,
            project
        )


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PagureBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
