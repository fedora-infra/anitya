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
anitya tests for the custom backend.
'''

import unittest

import anitya.lib.backends.sourceforge as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = 'Sourceforge'


class SourceforgeBackendtests(DatabaseTestCase):
    """ Sourceforge backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(SourceforgeBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = models.Project(
            name='filezilla',
            homepage='https://sourceforge.net/projects/filezilla/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name='foobar',
            homepage='https://sourceforge.net/projects/foobar',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name='file-folder-ren',
            homepage='https://sourceforge.net/projects/file-folder-ren/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """ Test the get_version function of the sourceforge backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = '3.31.0'
        obs = backend.SourceforgeBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.SourceforgeBackend.get_version,
            project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.SourceforgeBackend.get_version,
            project
        )

    def test_get_versions(self):
        """ Test the get_versions function of the sourceforge backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            u'3.25.0', u'3.25.1', u'3.25.2',
            u'3.26.0', u'3.26.1', u'3.26.2',
            u'3.27.0', u'3.27.0.1', u'3.27.1',
            u'3.28.0', u'3.29.0', u'3.30.0', u'3.31.0',
        ]
        obs = backend.SourceforgeBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.SourceforgeBackend.get_versions,
            project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.SourceforgeBackend.get_versions,
            project
        )


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        SourceforgeBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
