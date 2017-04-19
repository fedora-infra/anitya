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
anitya tests for the Maven backend.
'''

import unittest
import os

from anitya.lib.backends.maven import MavenBackend
import anitya.lib.model as model
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import Modeltests, create_distro, skip_jenkins
from anitya.config import config

BACKEND = 'Maven Central'


class MavenBackendTest(Modeltests):
    """ custom backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(MavenBackendTest, self).setUp()

        path = os.path.dirname(os.path.realpath(__file__))
        config.config['JAVA_PATH'] = os.path.join(path, '../../test-data/maven_mock.py')
        config.config['JAR_NAME'] = 'not-empty'
        create_distro(self.session)

    def assert_plexus_version(self, **kwargs):
        project = model.Project(backend=BACKEND, **kwargs)
        exp = '1.3.8'
        obs = MavenBackend.get_version(project)
        self.assertEqual(obs, exp)

    def assert_invalid(self, **kwargs):
        project = model.Project(backend=BACKEND, **kwargs)
        self.assertRaises(
            AnityaPluginException,
            MavenBackend.get_version,
            project
        )

    def test_maven_nonexistent(self):
        self.assert_invalid(
            name='foo',
            homepage='http://example.com',
        )

    def test_maven_coordinates_in_version_url(self):
        self.assert_plexus_version(
            name='plexus-maven-plugin',
            version_url='org.codehaus.plexus:plexus-maven-plugin',
            homepage='http://plexus.codehaus.org/',
        )

    def test_maven_coordinates_in_name(self):
        self.assert_plexus_version(
            name='org.codehaus.plexus:plexus-maven-plugin',
            homepage='http://plexus.codehaus.org/',
        )

    def test_maven_bad_coordinates(self):
        self.assert_invalid(
            name='plexus-maven-plugin',
            homepage='http://plexus.codehaus.org/',
            version_url='plexus-maven-plugin',
        )

    def test_maven_get_version_by_url(self):
        self.assert_plexus_version(
            name='plexus-maven-plugin',
            homepage='http://repo1.maven.org/maven2/'\
                     'org/codehaus/plexus/plexus-maven-plugin/',
        )

    def test_maven_get_versions(self):
        project = model.Project(
            backend=BACKEND,
            name='plexus-maven-plugin',
            version_url='org.codehaus.plexus:plexus-maven-plugin',
            homepage='http://plexus.codehaus.org/',
        )
        exp = ['1.1-alpha-7', '1.1', '1.1.1', '1.1.2', '1.1.3', '1.2', '1.3',
               '1.3.1', '1.3.2', '1.3.3', '1.3.4', '1.3.5', '1.3.6', '1.3.7',
               '1.3.8']
        obs = MavenBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    def test_maven_create_correct_url_with_version(self):
        # tries to create url where is version inside
        homepage = 'http://repo2.maven.org/maven2/com/zenecture/neuroflow-application_2.12/'
        group_id = 'com.zenecture'
        artifact_id = 'neuroflow-application_2.12'
        obs = MavenBackend.create_correct_url(group_id, artifact_id)
        self.assertEqual(obs, homepage)

    def test_maven_create_correct_url_with_dots(self):
        # tries to create url where are dots inside
        homepage = 'http://repo2.maven.org/maven2/com/liferay/com.liferay.amazon.rankings.web/'
        group_id = 'com.liferay'
        artifact_id = 'com.liferay.amazon.rankings.web'
        obs = MavenBackend.create_correct_url(group_id, artifact_id)
        self.assertEqual(obs, homepage)

    def test_maven_create_correct(self):
        # tests just normal package
        homepage = 'http://http://repo2.maven.org/maven2/com/github/liyiorg/weixin-popular/'
        group_id = 'com.github.liyiorg'
        artifact_id = 'weixin-popular'
        obs = MavenBackend.create_correct_url(group_id, artifact_id)
        self.assertEqual(obs, homepage)

    def test_maven_check_feed(self):
        """ Test the check_feed method of the maven backend. """
        generator = MavenBackend.check_feed()
        items = list(generator)

        self.assertEqual(items[0], (
            'ai.h2o:deepwater-backend-api', 'http://repo2.maven.org/maven2/ai/h2o/deepwater-backend-api/',
            'Maven Central', '1.0.3'))
        self.assertEqual(items[1], (
            'ai.h2o:sparkling-water-core_2.11', 'http://repo2.maven.org/maven2/ai/h2o/sparkling-water-core_2.11/',
            'Maven Central', '2.0.6'))
        # etc...


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MavenBackendTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
