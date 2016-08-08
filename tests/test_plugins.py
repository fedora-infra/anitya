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

from anitya.lib import plugins
from anitya.lib import model
from tests import Modeltests

EXPECTED_PLUGINS = [
    'BitBucket', 'CPAN (perl)', 'Debian project', 'Drupal6',
    'Drupal7', 'Freshmeat',
    'GNOME', 'GNU project', 'GitHub', 'Google code', 'Hackage',
    'Launchpad', 'Maven Central', 'PEAR', 'PECL', 'Packagist', 'PyPI',
    'Rubygems', 'Sourceforge', 'Stackage', 'custom', 'folder', 'npmjs',
    'pagure',
]

EXPECTED_ECOSYSTEMS = {
    "Rubygems": "rubygems",
    "PyPI": "pypi",
    "npmjs": "npm",
    "Maven Central": "maven",
}


class Pluginstests(Modeltests):
    """ Plugins tests. """

    def _check_db_contents(self, expected_plugins, expected_ecosystems):
        backends = list(model.Backend.all(self.session))
        backend_names_from_db = sorted(backend.name for backend in backends)
        self.assertEqual(backend_names_from_db, expected_plugins)
        ecosystems_from_db = dict((backend.name, backend.ecosystem.name)
                              for backend in backends
                                  if backend.ecosystem is not None)
        self.assertEqual(ecosystems_from_db, expected_ecosystems)


    def test_load_plugins(self):
        """ Test the plugins.load_plugins function. """
        plgns = plugins.load_plugins(self.session)
        self.assertEqual(len(plgns), len(EXPECTED_PLUGINS))
        plugin_names = sorted(plugin.name for plugin in plgns)
        self.assertEqual(plugin_names, EXPECTED_PLUGINS)

        ecosystems = dict((plugin.name, plugin.ecosystem_name)
                              for plugin in plgns
                                  if plugin.ecosystem_name is not None)
        self.assertEqual(ecosystems, EXPECTED_ECOSYSTEMS)

        self._check_db_contents(EXPECTED_PLUGINS, EXPECTED_ECOSYSTEMS)


    def test_reload_plugins_with_new_ecosystems(self):
        """ Test rerunning the plugins.load_plugins function. """
        plgns = plugins.load_plugins(self.session)
        self._check_db_contents(EXPECTED_PLUGINS, EXPECTED_ECOSYSTEMS)

        from anitya.lib.backends import custom
        custom.CustomBackend.ecosystem_name = "custom-ecosystem"
        modified_ecosystems = EXPECTED_ECOSYSTEMS.copy()
        modified_ecosystems["custom"] = "custom-ecosystem"
        plgns = plugins.load_plugins(self.session)
        self._check_db_contents(EXPECTED_PLUGINS, modified_ecosystems)


    def test_plugins_get_plugin_names(self):
        """ Test the plugins.get_plugin_names function. """
        plugin_names = plugins.get_plugin_names()
        self.assertEqual(len(plugin_names), len(EXPECTED_PLUGINS))
        self.assertEqual(sorted(plugin_names), EXPECTED_PLUGINS)

    def test_plugins_get_plugin(self):
        """ Test the plugins.get_plugin function. """
        plugin = plugins.get_plugin('PyPI')
        self.assertEqual(
            str(plugin), "<class 'anitya.lib.backends.pypi.PypiBackend'>")


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Pluginstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
