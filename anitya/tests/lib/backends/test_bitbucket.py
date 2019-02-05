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

"""
anitya tests for the bitbucket backend.
"""

import unittest

import anitya.lib.backends.bitbucket as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = "BitBucket"


class BitBucketBackendtests(DatabaseTestCase):
    """ BitBucket backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(BitBucketBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = models.Project(
            name="sqlalchemy",
            homepage="https://bitbucket.org/zzzeek/sqlalchemy",
            version_url="zzzeek/sqlalchemy",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="foobar",
            homepage="https://bitbucket.org/foo/bar",
            version_url="foobar/bar",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name="cherrypy",
            homepage="https://bitbucket.org/cherrypy/cherrypy",
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """ Test the get_version function of the BitBucket backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = "rel_1_1_3"
        obs = backend.BitBucketBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.BitBucketBackend.get_version, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = "v5.2.0"
        obs = backend.BitBucketBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_version_url_only_homepage(self):
        """
        Assert that correct url is returned when only
        homepage is specified.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://bitbucket.org/cherrypy/cherrypy",
            backend=BACKEND,
        )
        exp = "https://bitbucket.org/cherrypy/cherrypy/downloads?tab=tags"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_project_version_url(self):
        """
        Assert that correct url is returned when
        version_url is specified.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://example.org",
            version_url="https://bitbucket.org/cherrypy/cherrypy",
            backend=BACKEND,
        )
        exp = "https://bitbucket.org/cherrypy/cherrypy/downloads?tab=tags"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_slash_homepage(self):
        """
        Assert that correct url is returned when
        homepage ends with /.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://bitbucket.org/cherrypy/cherrypy/",
            backend=BACKEND,
        )
        exp = "https://bitbucket.org/cherrypy/cherrypy/downloads?tab=tags"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_url_slash_version_url(self):
        """
        Assert that correct url is returned when
        version_url ends with /.
        """
        project = models.Project(
            name="cherrypy",
            homepage="https://example.org",
            version_url="https://bitbucket.org/cherrypy/cherrypy/",
            backend=BACKEND,
        )
        exp = "https://bitbucket.org/cherrypy/cherrypy/downloads?tab=tags"

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_version_wrong_homepage(self):
        """
        Assert that correct url is returned when wrong
        homepage is provided.
        """
        project = models.Project(
            name="cherrypy", homepage="https://wrong.org", backend=BACKEND
        )
        exp = ""

        obs = backend.BitBucketBackend.get_version_url(project)

        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the BitBucket backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            "rel_0_1_0",
            "rel_0_1_1",
            "rel_0_1_2",
            "rel_0_1_3",
            "rel_0_1_4",
            "rel_0_1_5",
            "rel_0_1_6",
            "rel_0_1_7",
            "rel_0_2_0",
            "rel_0_2_1",
            "rel_0_2_2",
            "rel_0_2_3",
            "rel_0_2_4",
            "rel_0_2_5",
            "rel_0_2_6",
            "rel_0_2_7",
            "rel_0_2_8",
            "rel_0_3_0",
            "rel_0_3_1",
            "rel_0_3_2",
            "rel_0_3_3",
            "rel_0_3_4",
            "rel_0_3_5",
            "rel_0_3_6",
            "rel_0_3_7",
            "rel_0_3_8",
            "rel_0_3_9",
            "rel_0_3_10",
            "rel_0_3_11",
            "rel_0_4beta1",
            "rel_0_4beta2",
            "rel_0_4beta3",
            "rel_0_4beta4",
            "rel_0_4beta6",
            "rel_0_4_0",
            "rel_0_4_1",
            "rel_0_4_2",
            "rel_0_4_2a",
            "rel_0_4_2b",
            "rel_0_4_2p3",
            "rel_0_4_3",
            "rel_0_4_4",
            "rel_0_4_5",
            "rel_0_4_6",
            "rel_0_4_7",
            "rel_0_4_7p1",
            "rel_0_4_8",
            "rel_0_5beta1",
            "rel_0_5beta2",
            "rel_0_5beta3",
            "rel_0_5rc1",
            "rel_0_5rc2",
            "rel_0_5rc3",
            "rel_0_5rc4",
            "rel_0_5_0",
            "rel_0_5_1",
            "rel_0_5_2",
            "rel_0_5_3",
            "rel_0_5_4",
            "rel_0_5_4p1",
            "rel_0_5_4p2",
            "rel_0_5_5",
            "rel_0_5_6",
            "rel_0_5_7",
            "rel_0_5_8",
            "rel_0_6beta1",
            "rel_0_6beta2",
            "rel_0_6beta3",
            "rel_0_6_0",
            "rel_0_6_1",
            "rel_0_6_2",
            "rel_0_6_3",
            "rel_0_6_4",
            "rel_0_6_5",
            "rel_0_6_6",
            "rel_0_6_7",
            "rel_0_6_8",
            "rel_0_6_9",
            "rel_0_7b1",
            "rel_0_7b2",
            "rel_0_7b3",
            "rel_0_7b4",
            "rel_0_7_0",
            "rel_0_7_1",
            "rel_0_7_2",
            "rel_0_7_3",
            "rel_0_7_4",
            "rel_0_7_5",
            "rel_0_7_6",
            "rel_0_7_7",
            "rel_0_7_8",
            "rel_0_7_9",
            "rel_0_7_10",
            "rel_0_8_0",
            "rel_0_8_0b1",
            "rel_0_8_0b2",
            "rel_0_8_1",
            "rel_0_8_2",
            "rel_0_8_3",
            "rel_0_8_4",
            "rel_0_8_5",
            "rel_0_8_6",
            "rel_0_8_7",
            "rel_0_9_0",
            "rel_0_9_0b1",
            "rel_0_9_1",
            "rel_0_9_2",
            "rel_0_9_3",
            "rel_0_9_4",
            "rel_0_9_5",
            "rel_0_9_6",
            "rel_0_9_7",
            "rel_0_9_8",
            "rel_0_9_9",
            "rel_0_9_10",
            "rel_1_0_0",
            "rel_1_0_0b1",
            "rel_1_0_0b2",
            "rel_1_0_0_b3",
            "rel_1_0_0b4",
            "rel_1_0_0b5",
            "rel_1_0_1",
            "rel_1_0_2",
            "rel_1_0_3",
            "rel_1_0_4",
            "rel_1_0_5",
            "rel_1_0_6",
            "rel_1_0_7",
            "rel_1_0_8",
            "rel_1_0_9",
            "rel_1_0_10",
            "rel_1_0_11",
            "rel_1_0_12",
            "rel_1_0_13",
            "rel_1_0_14",
            "rel_1_0_15",
            "rel_1_1_0",
            "rel_1_1_0b1",
            "rel_1_1_0b2",
            "rel_1_1_0b3",
            "rel_1_1_1",
            "rel_1_1_2",
            "rel_1_1_3",
        ]
        obs = backend.BitBucketBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException, backend.BitBucketBackend.get_versions, project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = [
            "cherrypy-2.0.0-beta",
            "cherrypy-2.0.0",
            "cherrypy-2.1.0-alpha",
            "cherrypy-2.1.0-rc1",
            "cherrypy-2.1.0-rc2",
            "cherrypy-2.1.1",
            "cherrypy-2.2.0beta",
            "cherrypy-2.2.0rc1",
            "cherrypy-2.2.0",
            "cherrypy-2.2.1",
            "cherrypy-2.3.0",
            "cherrypy-3.0.0beta",
            "cherrypy-3.0.0beta2",
            "cherrypy-3.0.0RC1",
            "cherrypy-3.0.0",
            "cherrypy-3.0.1",
            "cherrypy-3.0.2",
            "cherrypy-3.0.3",
            "cherrypy-3.0.4",
            "cherrypy-3.1.0beta",
            "cherrypy-3.1.0beta2",
            "cherrypy-3.1.0beta3",
            "cherrypy-3.1.0",
            "cherrypy-3.1.1",
            "cherrypy-3.1.2",
            "cherrypy-3.2.0beta",
            "cherrypy-3.2.0rc1",
            "cherrypy-3.2.0",
            "cherrypy-3.2.1",
            "cherrypy-3.2.2rc1",
            "cherrypy-3.2.2",
            "rdelon-experimental",
            "trunk",
            "3.2.3",
            "3.2.4",
            "3.2.5",
            "3.2.6",
            "3.3.0",
            "3.4.0",
            "3.5.0",
            "3.6.0",
            "3.7.0",
            "3.8.0",
            "3.8.1",
            "3.8.2",
            "4.0.0",
            "5.0.0",
            "5.0.1",
            "5.1.0",
            "v5.2.0",
        ]
        obs = backend.BitBucketBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(BitBucketBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
