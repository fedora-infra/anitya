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
from __future__ import unicode_literals

'''
anitya tests for the bitbucket backend.
'''

import unittest

import anitya.lib.backends.bitbucket as backend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import Modeltests, create_distro, skip_jenkins


BACKEND = 'BitBucket'


class BitBucketBackendtests(Modeltests):
    """ BitBucket backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(BitBucketBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='sqlalchemy',
            homepage='https://bitbucket.org/zzzeek/sqlalchemy',
            version_url='zzzeek/sqlalchemy',
            backend=BACKEND,
            version_prefix='rel_',
            version_scheme=model.GENERIC_VERSION,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='foobar',
            homepage='http://bitbucket.org/foo/bar',
            version_url='foobar/bar',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='cherrypy',
            homepage='https://bitbucket.org/cherrypy/cherrypy',
            backend=BACKEND,
            version_scheme=model.PEP440_VERSION,
            version_prefix='cherrypy-',
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """ Test the get_version function of the BitBucket backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '1_1_3'
        obs = backend.BitBucketBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.BitBucketBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '5.2.0'
        obs = backend.BitBucketBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the BitBucket backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = sorted([
            '0_1_0', '0_1_1', '0_1_2', '0_1_3',
            '0_1_4', '0_1_5', '0_1_6', '0_1_7',
            '0_2_0', '0_2_1', '0_2_2', '0_2_3',
            '0_2_4', '0_2_5', '0_2_6', '0_2_7',
            '0_2_8', '0_3_0', '0_3_1', '0_3_2',
            '0_3_3', '0_3_4', '0_3_5', '0_3_6',
            '0_3_7', '0_3_8', '0_3_9', '0_3_10',
            '0_3_11', '0_4beta1', '0_4beta2', '0_4beta3',
            '0_4beta4', '0_4beta6', '0_4_0', '0_4_1',
            '0_4_2', '0_4_2a', '0_4_2b', '0_4_2p3',
            '0_4_3', '0_4_4', '0_4_5', '0_4_6',
            '0_4_7', '0_4_7p1', '0_4_8', '0_5beta1',
            '0_5beta2', '0_5beta3', '0_5rc1', '0_5rc2',
            '0_5rc3', '0_5rc4', '0_5_0', '0_5_1',
            '0_5_2', '0_5_3', '0_5_4', '0_5_4p1',
            '0_5_4p2', '0_5_5', '0_5_6', '0_5_7',
            '0_5_8', '0_6beta1', '0_6beta2', '0_6beta3',
            '0_6_0', '0_6_1', '0_6_2', '0_6_3',
            '0_6_4', '0_6_5', '0_6_6', '0_6_7', '0_6_8',
            '0_6_9', '0_7b1', '0_7b2', '0_7b3',
            '0_7b4', '0_7_0', '0_7_1', '0_7_2',
            '0_7_3', '0_7_4', '0_7_5', '0_7_6',
            '0_7_7', '0_7_8', '0_7_9', '0_7_10',
            '0_8_0', '0_8_0b1', '0_8_0b2', '0_8_1',
            '0_8_2', '0_8_3', '0_8_4', '0_8_5',
            '0_8_6', '0_8_7', '0_9_0', '0_9_0b1',
            '0_9_1', '0_9_2', '0_9_3', '0_9_4',
            '0_9_5', '0_9_6', '0_9_7', '0_9_8',
            '0_9_9', '0_9_10', '1_0_0', '1_0_0b1',
            '1_0_0b2', '1_0_0_b3', '1_0_0b4', '1_0_0b5',
            '1_0_1', '1_0_2', '1_0_3', '1_0_4',
            '1_0_5', '1_0_6', '1_0_7', '1_0_8',
            '1_0_9', '1_0_10', '1_0_11', '1_0_12',
            '1_0_13', '1_0_14', '1_0_15', '1_1_0',
            '1_1_0b1', '1_1_0b2', '1_1_0b3', '1_1_1',
            '1_1_2', '1_1_3'
        ])
        obs = backend.BitBucketBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.BitBucketBackend.get_versions,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = [
            'rdelon-experimental',
            'trunk',
            '2.0.0b0',
            '2.0.0',
            '2.1.0a0',
            '2.1.0rc1',
            '2.1.0rc2',
            '2.1.1',
            '2.2.0b0',
            '2.2.0rc1',
            '2.2.0',
            '2.2.1',
            '2.3.0',
            '3.0.0b0',
            '3.0.0b2',
            '3.0.0rc1',
            '3.0.0',
            '3.0.1',
            '3.0.2',
            '3.0.3',
            '3.0.4',
            '3.1.0b0',
            '3.1.0b2',
            '3.1.0b3',
            '3.1.0',
            '3.1.1',
            '3.1.2',
            '3.2.0b0',
            '3.2.0rc1',
            '3.2.0',
            '3.2.1',
            '3.2.2rc1',
            '3.2.2',
            '3.2.3',
            '3.2.4',
            '3.2.5',
            '3.2.6',
            '3.3.0',
            '3.4.0',
            '3.5.0',
            '3.6.0',
            '3.7.0',
            '3.8.0',
            '3.8.1',
            '3.8.2',
            '4.0.0',
            '5.0.0',
            '5.0.1',
            '5.1.0',
            '5.2.0',
        ]
        obs = backend.BitBucketBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(BitBucketBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
