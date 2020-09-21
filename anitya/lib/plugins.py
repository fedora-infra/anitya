# -*- coding: utf-8 -*-
# This file is a part of the Anitya project.
#
# Copyright © 2014-2017 Pierre-Yves Chibon <pingou@pingoured.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""Module handling the load/call of the plugins of anitya."""

import logging

from straight.plugin import load

from anitya.lib.backends import BaseBackend
from anitya.lib.ecosystems import BaseEcosystem
from anitya.lib.versions import Version

_log = logging.getLogger(__name__)


class _PluginManager(object):
    """Manage a particular set of Anitya plugins"""

    def __init__(self, namespace, base_class):
        self._namespace = namespace
        self._base_class = base_class

    def get_plugins(self):
        """ Return the list of plugins."""
        return load(self._namespace, subclasses=self._base_class)

    def get_plugin_names(self):
        """ Return the list of plugin names. """
        plugins = self.get_plugins()
        output = [plugin.name for plugin in plugins]
        return output

    def get_plugin(self, plugin_name):
        """ Return the plugin corresponding to the given plugin name. """
        plugins = self.get_plugins()
        for plugin in plugins:
            if plugin.name.lower() == plugin_name.lower():
                return plugin


BACKEND_PLUGINS = _PluginManager("anitya.lib.backends", BaseBackend)
ECOSYSTEM_PLUGINS = _PluginManager("anitya.lib.ecosystems", BaseEcosystem)
VERSION_PLUGINS = _PluginManager("anitya.lib.versions", Version)


def _load_backend_plugins(session):
    """Load any new backend plugins into the DB"""
    plugins = list(BACKEND_PLUGINS.get_plugins())
    return plugins


def _load_ecosystem_plugins(session):
    """Load any new ecosystem plugins into the DB"""
    plugins = list(ECOSYSTEM_PLUGINS.get_plugins())
    return plugins


def _load_version_plugins(session):
    """Load any new version plugins into the DB"""
    plugins = list(VERSION_PLUGINS.get_plugins())
    return plugins


def load_all_plugins(session):
    """Load all the plugins and insert them in the database if they are
    not already present."""
    plugins = {}
    plugins["backends"] = _load_backend_plugins(session)
    plugins["ecosystems"] = _load_ecosystem_plugins(session)
    plugins["versions"] = _load_version_plugins(session)
    return plugins


# Preserve module level API for accessing the backend plugin list
get_plugin_names = BACKEND_PLUGINS.get_plugin_names
get_plugins = BACKEND_PLUGINS.get_plugins
get_plugin = BACKEND_PLUGINS.get_plugin


def load_plugins(session, family="backends"):
    """Calls load_all_plugins, but only retuns plugins specified by family argument

    Args:
        family (str): family of the plugins, that should be returned
    """
    return load_all_plugins(session)[family]
