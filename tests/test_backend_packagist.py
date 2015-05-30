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
anitya tests for the packagist backend.
'''

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya.lib.backends.packagist as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from tests import Modeltests, create_distro, skip_jenkins


BACKEND = 'Packagist'


class PackagistBackendtests(Modeltests):
    """ Packagist backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(PackagistBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='php-code-coverage',
            homepage='https://packagist.org/packages/phpunit/php-code-coverage',
            version_url='phpunit',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='fake',
            homepage='https://packagist.org/packages/fake/php-fake',
            version_url='fake',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='php-timer',
            homepage='https://packagist.org/packages/phpunit/php-timer',
            version_url='phpunit',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_packagist_get_version(self):
        """ Test the get_version function of the packagist backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '2.0.17'
        obs = backend.PackagistBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.PackagistBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '1.0.5'
        obs = backend.PackagistBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_packagist_get_versions(self):
        """ Test the get_versions function of the packagist backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            u'1.2.0', u'1.2.1', u'1.2.10', u'1.2.11', u'1.2.12', u'1.2.13',
            u'1.2.14', u'1.2.15', u'1.2.16', u'1.2.17', u'1.2.18', u'1.2.2',
            u'1.2.3', u'1.2.6', u'1.2.7', u'1.2.8', u'1.2.9', u'1.2.x-dev',
            u'2.0.0', u'2.0.1', u'2.0.10', u'2.0.11', u'2.0.12', u'2.0.13',
            u'2.0.14', u'2.0.15', u'2.0.16', u'2.0.17',
            u'2.0.2', u'2.0.3', u'2.0.4', u'2.0.5',
            u'2.0.6', u'2.0.7', u'2.0.8', u'2.0.9',
            u'2.0.x-dev',
            u'dev-feature/path-coverage',
            u'dev-master',
        ]
        obs = backend.PackagistBackend.get_versions(project)
        self.assertListEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.PackagistBackend.get_versions,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = ['dev-master', '1.0.3', '1.0.4', '1.0.5']
        obs = backend.PackagistBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PackagistBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
