# -*- coding: utf-8 -*-
#
# Copyright © 2018  Red Hat, Inc.
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
Anitya tests for the GitLab backend.
'''

import unittest

import anitya.lib.backends.gitlab as backend
from anitya.db import models
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import DatabaseTestCase, create_distro


BACKEND = 'GitLab'


class GitlabBackendtests(DatabaseTestCase):
    """ Gitlab backend tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(GitlabBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = models.Project(
            name='gnome-video-arcade',
            homepage='https://gitlab.gnome.org/GNOME/gnome-video-arcade',
            version_url='https://gitlab.gnome.org/GNOME/gnome-video-arcade',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name='foobar',
            homepage='https://gitlab.com/foo/bar',
            version_url='https://gitlab.com/foo/bar',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = models.Project(
            name='xonotic',
            homepage='https://gitlab.com/xonotic/xonotic',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

    def test_get_version(self):
        """ Test the get_version function of the gitlab backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = '0.8.8'
        obs = backend.GitlabBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GitlabBackend.get_version,
            project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = 'xonotic-v0.8.2'
        obs = backend.GitlabBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the gitlab backend. """
        pid = 1
        project = models.Project.get(self.session, pid)
        exp = [
            u'0.6.1', u'0.6.1.1', u'0.6.2', u'0.6.3',
            u'0.6.4', u'0.6.5', u'0.6.6', u'0.6.7',
            u'0.6.8', u'0.7.0', u'0.7.1', u'0.8.0',
            u'0.8.1', u'0.8.2', u'0.8.3', u'0.8.4',
            u'0.8.5', u'0.8.6', u'0.8.7', u'0.8.8'
        ]
        obs = backend.GitlabBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = models.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.GitlabBackend.get_versions,
            project
        )

        pid = 3
        project = models.Project.get(self.session, pid)
        exp = [
            u'xonotic-v0.1.0preview', u'xonotic-v0.5.0',
            u'xonotic-v0.6.0', u'xonotic-v0.7.0',
            u'xonotic-v0.8.0', u'xonotic-v0.8.1',
            u'xonotic-v0.8.2'
        ]
        obs = backend.GitlabBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

        project = models.Project(
            name='foobar',
            homepage='',
            backend=BACKEND,
        )
        self.assertRaises(
            AnityaPluginException,
            backend.GitlabBackend.get_versions,
            project
        )


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(GitlabBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
