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

import anitya.lib.backends.npmjs as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import Modeltests, create_distro, skip_jenkins


BACKEND = 'npmjs'


class NpmjsBackendtests(Modeltests):
    """ Drupal backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(NpmjsBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='request',
            homepage='https://www.npmjs.org/package/request',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='foobarasd',
            homepage='https://www.npmjs.org/package/foobarasd',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='colors',
            homepage='https://www.npmjs.org/package/colors',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """ Test the get_version function of the npmjs backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '2.56.0'
        obs = backend.NpmjsBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.NpmjsBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '1.1.0'
        obs = backend.NpmjsBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the npmjs backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            u'0.8.3', u'0.9.0', u'0.9.1', u'0.9.5', u'0.10.0',
            u'1.0.0', u'1.1.0', u'1.1.1', u'1.2.0',
            u'1.9.0', u'1.9.1', u'1.9.2', u'1.9.3', u'1.9.5', u'1.9.7',
            u'1.9.8', u'1.9.9',
            u'2.0.0', u'2.0.1', u'2.0.2', u'2.0.3', u'2.0.4', u'2.0.5',
            u'2.1.0', u'2.1.1',
            u'2.2.0', u'2.2.5', u'2.2.6', u'2.2.9',
            u'2.9.0', u'2.9.1', u'2.9.2', u'2.9.3',
            u'2.9.100', u'2.9.150', u'2.9.151', u'2.9.152', u'2.9.153',
            u'2.9.200', u'2.9.201', u'2.9.202', u'2.9.203',
            u'2.10.0',
            u'2.11.0', u'2.11.1', u'2.11.2', u'2.11.3', u'2.11.4',
            u'2.12.0',
            u'2.14.0',
            u'2.16.0', u'2.16.2', u'2.16.4', u'2.16.6',
            u'2.18.0', u'2.19.0', u'2.20.0', u'2.21.0', u'2.22.0', u'2.23.0',
            u'2.24.0', u'2.25.0', u'2.26.0', u'2.27.0', u'2.28.0', u'2.29.0',
            u'2.30.0', u'2.31.0', u'2.32.0', u'2.33.0', u'2.34.0', u'2.35.0',
            u'2.36.0', u'2.37.0', u'2.38.0', u'2.39.0', u'2.40.0', u'2.41.0',
            u'2.42.0', u'2.43.0', u'2.44.0', u'2.45.0', u'2.46.0', u'2.47.0',
            u'2.48.0', u'2.49.0', u'2.50.0', u'2.51.0', u'2.52.0', u'2.53.0',
            u'2.54.0', u'2.55.0', u'2.56.0',
        ]
        obs = backend.NpmjsBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.NpmjsBackend.get_versions,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = [
            u'0.3.0', u'0.5.0', u'0.5.1',
            u'0.6.0', u'0.6.0.post1', u'0.6.1', u'0.6.2',
            u'1.0.0', u'1.0.1', u'1.0.2', u'1.0.3',
            u'1.1.0',
        ]
        obs = backend.NpmjsBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    def test_npmjs_check_feed(self):
        """ Test the check_feed method of the npmjs backend. """
        generator = backend.NpmjsBackend.check_feed()
        items = list(generator)

        self.assertEqual(items[0], (
            '0-_-0', 'http://npmjs.org/package/0-_-0', 'npmjs', '1.0.0'))
        self.assertEqual(items[1], (
            '111-react-simpleform',
            'http://npmjs.org/package/111-react-simpleform',
            'npmjs', '1.2.0'))
        # etc...


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(NpmjsBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
