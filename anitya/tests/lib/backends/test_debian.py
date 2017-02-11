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
anitya tests for the debian backend.
'''

import unittest

import mock

from anitya.lib.exceptions import AnityaPluginException
from anitya.lib.backends import get_versions_by_regex_for_text
from anitya.tests.base import Modeltests, create_distro, skip_jenkins
import anitya.lib.backends.debian as backend
import anitya.lib.model as model


BACKEND = 'Debian project'


class DebianBackendtests(Modeltests):
    """ Debian backend tests. """

    @skip_jenkins
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(DebianBackendtests, self).setUp()

        create_distro(self.session)
        self.create_project()

    def create_project(self):
        """ Create some basic projects to work with. """
        project = model.Project(
            name='guake',
            homepage='http://ftp.debian.org/debian/pool/main/g/guake/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='foo',
            homepage='http://pecl.php.net/package/foo',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()

        project = model.Project(
            name='libgnupg-interface-perl',
            homepage='http://ftp.debian.org/debian/pool/main/'
            'libg/libgnupg-interface-perl/',
            backend=BACKEND,
        )
        self.session.add(project)
        self.session.commit()


    def test_get_version(self):
        """ Test the get_version function of the debian backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = '0.7.2'
        obs = backend.DebianBackend.get_version(project)
        self.assertEqual(obs, exp)

        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.DebianBackend.get_version,
            project
        )

        pid = 3
        project = model.Project.get(self.session, pid)
        exp = '0.52'
        obs = backend.DebianBackend.get_version(project)
        self.assertEqual(obs, exp)

    def test_get_versions(self):
        """ Test the get_versions function of the debian backend. """
        pid = 1
        project = model.Project.get(self.session, pid)
        exp = [
            u'0.4.2', u'0.4.3', u'0.4.4',
            u'0.5.0',
            u'0.7.0', u'0.7.2',
        ]
        obs = backend.DebianBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    def test_get_versions_http_404(self):
        """
        Assert an exception is raised if the request results in a HTTP 404.
        """
        pid = 2
        project = model.Project.get(self.session, pid)
        self.assertRaises(
            AnityaPluginException,
            backend.DebianBackend.get_version,
            project
        )

    def test_get_versions_no_z_release(self):
        """Assert the Debian backend handles versions in the format X.Y"""
        pid = 3
        project = model.Project.get(self.session, pid)
        exp = [u'0.45', u'0.50', u'0.52']
        obs = backend.DebianBackend.get_ordered_versions(project)
        self.assertEqual(obs, exp)

    def test_debian_regex_with_orig(self):
        """Assert Debian tarballs have the ".orig" string removed"""
        tarball_names = """
            Some Header
            libgnupg-interface-perl_0.45.orig.tar.gz
            libgnupg-interface-perl_0.46.orig.tar.gz

        """
        versions = get_versions_by_regex_for_text(
            tarball_names,
            'http://example.com',
            backend.DEBIAN_REGEX % {'name': 'libgnupg-interface-perl'},
            model.Project.get(self.session, 3)
        )
        self.assertEqual(sorted(['0.45', '0.46']), sorted(versions))

    def test_debian_regex_without_orig(self):
        """Assert Debian tarballs without the ".orig" string work"""
        tarball_names = """
            Some Header
            libgnupg-interface-perl_0.45.tar.gz
            libgnupg-interface-perl_0.46.tar.gz

        """
        versions = get_versions_by_regex_for_text(
            tarball_names,
            'http://example.com',
            backend.DEBIAN_REGEX % {'name': 'libgnupg-interface-perl'},
            model.Project.get(self.session, 3)
        )
        self.assertEqual(sorted(['0.45', '0.46']), sorted(versions))


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(DebianBackendtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
