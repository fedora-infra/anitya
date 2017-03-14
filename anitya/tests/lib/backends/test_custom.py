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

import anitya.lib.backends.custom as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import Modeltests, create_distro, skip_jenkins

BACKEND = 'custom'


class CustomBackendtests(Modeltests):
    """ custom backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(CustomBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='geany',
            homepage='http://www.geany.org/',
            version_url='http://www.geany.org/Download/Releases',
            regex='DEFAULT',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='fake',
            homepage='https://pypi.python.org/pypi/repo_manager_fake',
            regex='DEFAULT',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='subsurface',
            homepage='http://subsurface.hohndel.org/',
            version_url='http://subsurface.hohndel.org/downloads/',
            regex='DEFAULT',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
        )
        self.session.add(project)
        self.session.commit()

    def test_custom_get_version(self):
        """ Test the get_version function of the custom backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '1.24.1'
        obs = backend.CustomBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.CustomBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '4.4.2'
        obs = backend.CustomBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_custom_get_versions(self):
        """ Test the get_versions function of the custom backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = ['1.24.1']
        obs = backend.CustomBackend.get_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.CustomBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = [u'3.1.1', u'4.0', u'4.0.1', u'4.0.2', u'4.0.3',
               u'4.1', u'4.2', u'4.3', u'4.4.0', u'4.4.1', u'4.4.2']
        obs = backend.CustomBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(CustomBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
