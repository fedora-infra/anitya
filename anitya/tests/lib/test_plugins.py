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

from anitya.lib import plugins
from anitya.lib import model
from anitya.tests.base import Modeltests

EXPECTED_BACKENDS = [
    'BitBucket', 'CPAN (perl)', 'crates.io', 'Debian project', 'Drupal6',
    'Drupal7', 'Freshmeat',
    'GNOME', 'GNU project', 'GitHub', 'Google code', 'Hackage',
    'Launchpad', 'Maven Central', 'PEAR', 'PECL', 'Packagist', 'PyPI',
    'Rubygems', 'Sourceforge', 'Stackage', 'custom', 'folder', 'npmjs',
    'pagure',
]

EXPECTED_ECOSYSTEMS = {
    "rubygems": "Rubygems",
    "pypi": "PyPI",
    "npm": "npmjs",
    "maven": "Maven Central",
    "crates.io": "crates.io",
}


class Pluginstests(Modeltests):
    """ Plugins tests. """

    def _check_db_contents(self, expected_backends, expected_ecosystems):
        backends = model.Backend.all(self.session)
        backend_names_from_db = sorted(backend.name for backend in backends)
        self.assertEqual(sorted(backend_names_from_db), sorted(expected_backends))
        ecosystems = model.Ecosystem.all(self.session)
        ecosystems_from_db = dict((eco.name, eco.default_backend.name)
                                  for eco in ecosystems)
        self.assertEqual(ecosystems_from_db, expected_ecosystems)


    def test_load_all_plugins(self):
        """ Test the plugins.load_all_plugins function. """
        all_plugins = plugins.load_all_plugins(self.session)
        backend_plugins = all_plugins["backends"]
        self.assertEqual(len(backend_plugins), len(EXPECTED_BACKENDS))
        backend_names = sorted(plugin.name for plugin in backend_plugins)
        self.assertEqual(sorted(backend_names), sorted(EXPECTED_BACKENDS))

        ecosystem_plugins = all_plugins["ecosystems"]
        ecosystems = dict((plugin.name, plugin.default_backend)
                              for plugin in ecosystem_plugins)
        self.assertEqual(ecosystems, EXPECTED_ECOSYSTEMS)

        self._check_db_contents(EXPECTED_BACKENDS, EXPECTED_ECOSYSTEMS)

    def test_load_plugins(self):
        """ Test the plugins.load_plugins function. """
        backend_plugins = plugins.load_plugins(self.session)
        self.assertEqual(len(backend_plugins), len(EXPECTED_BACKENDS))
        backend_names = sorted(plugin.name for plugin in backend_plugins)
        self.assertEqual(sorted(backend_names), sorted(EXPECTED_BACKENDS))

        self._check_db_contents(EXPECTED_BACKENDS, EXPECTED_ECOSYSTEMS)

    def test_plugins_get_plugin_names(self):
        """ Test the plugins.get_plugin_names function. """
        plugin_names = plugins.get_plugin_names()
        self.assertEqual(len(plugin_names), len(EXPECTED_BACKENDS))
        self.assertEqual(sorted(plugin_names), sorted(EXPECTED_BACKENDS))

    def test_plugins_get_plugin(self):
        """ Test the plugins.get_plugin function. """
        plugin = plugins.get_plugin('PyPI')
        self.assertEqual(
            str(plugin), "<class 'anitya.lib.backends.pypi.PypiBackend'>")


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Pluginstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
