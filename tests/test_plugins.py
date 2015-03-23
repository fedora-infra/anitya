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
anitya tests of the plugins.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import datetime
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya.lib.plugins as plugins
from tests import Modeltests


class Pluginstests(Modeltests):
    """ Plugins tests. """

    def test_load_plugins(self):
        """ Test the plugins.load_plugins function. """
        plgns = [plg.name for plg in plugins.load_plugins(self.session)]
        self.assertEqual(len(plgns), 21)
        exp = [
            'CPAN (perl)', 'Debian project', 'Drupal6', 'Drupal7', 'Freshmeat',
            'GNOME', 'GNU project', 'GitHub', 'Google code', 'Hackage',
            'Launchpad', 'Maven Central', 'PEAR', 'PECL', 'Packagist', 'PyPI',
            'Rubygems', 'Sourceforge', 'custom', 'folder', 'npmjs',
        ]

        self.assertEqual(sorted(plgns), exp)

    def test_plugins_get_plugin_names(self):
        """ Test the plugins.get_plugin_names function. """
        plgns = plugins.get_plugin_names()
        self.assertEqual(len(plgns), 21)
        exp = [
            'CPAN (perl)', 'Debian project', 'Drupal6', 'Drupal7', 'Freshmeat',
            'GNOME', 'GNU project', 'GitHub', 'Google code', 'Hackage',
            'Launchpad', 'Maven Central', 'PEAR', 'PECL', 'Packagist', 'PyPI',
            'Rubygems', 'Sourceforge', 'custom', 'folder', 'npmjs',
        ]

        self.assertEqual(sorted(plgns), exp)

    def test_plugins_get_plugin(self):
        """ Test the plugins.get_plugin function. """
        plgns = plugins.get_plugin('PyPI')
        self.assertEqual(
            str(plgns), "<class 'anitya.lib.backends.pypi.PypiBackend'>")


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Pluginstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
