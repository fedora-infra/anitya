# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

Module handling the load/call of the plugins of anitya
"""

import logging

from sqlalchemy.exc import SQLAlchemyError

from straight.plugin import load

import anitya.lib.model as model
from anitya.lib.backends import BaseBackend
from anitya.lib.ecosystems import BaseEcosystem

log = logging.getLogger(__name__)


class _PluginManager(object):
    """Manage a particular set of Anitya plugins"""
    def __init__(self, namespace, base_class):
        self._namespace = namespace
        self._base_class = base_class

    def get_plugins(self):
        ''' Return the list of plugins.'''
        return load(self._namespace, subclasses=self._base_class)

    def get_plugin_names(self):
        ''' Return the list of plugin names. '''
        plugins = self.get_plugins()
        output = [plugin.name for plugin in plugins]
        return output

    def get_plugin(self, plugin_name):
        ''' Return the plugin corresponding to the given plugin name. '''
        plugins = self.get_plugins()
        for plugin in plugins:
            if plugin.name.lower() == plugin_name.lower():
                return plugin


BACKEND_PLUGINS = _PluginManager('anitya.lib.backends', BaseBackend)
ECOSYSTEM_PLUGINS = _PluginManager('anitya.lib.ecosystems', BaseEcosystem)


def _load_backend_plugins(session):
    """Load any new backend plugins into the DB"""
    backends = [bcke.name for bcke in model.Backend.all(session)]
    plugins = list(BACKEND_PLUGINS.get_plugins())
    # Add any new Backend definitions
    plugin_names = [plugin.name for plugin in plugins]
    for backend in set(backends).symmetric_difference(set(plugin_names)):
        log.info("Registering backend %r", backend)
        bcke = model.Backend(name=backend)
        session.add(bcke)
        try:
            session.commit()
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot test this as it would come from a defective DB
            print(err)
            session.rollback()
    return plugins


def _load_ecosystem_plugins(session):
    """Load any new ecosystem plugins into the DB"""
    ecosystems = [ecosystem.name for ecosystem in model.Ecosystem.all(session)]
    plugins = list(ECOSYSTEM_PLUGINS.get_plugins())
    # Add any new Ecosystem definitions
    backends_by_ecosystem = dict((plugin.name, plugin.default_backend)
                                 for plugin in plugins)
    eco_names = set(ecosystems).symmetric_difference(
        set(backends_by_ecosystem))
    for eco_name in eco_names:
        backend = backends_by_ecosystem[eco_name]
        bcke = model.Backend.by_name(session, backend)
        log.info("Registering ecosystem %r with default backend %r",
                 eco_name, backend)
        ecosystem = model.Ecosystem(name=eco_name, default_backend=bcke)
        session.add(ecosystem)
        try:
            session.commit()
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot test this as it would come from a defective DB
            print(err)
            session.rollback()
    return plugins


def load_all_plugins(session):
    ''' Load all the plugins and insert them in the database if they are
    not already present. '''
    plugins = {}
    plugins["backends"] = _load_backend_plugins(session)
    plugins["ecosystems"] = _load_ecosystem_plugins(session)
    return plugins


# Preserve module level API for accessing the backend plugin list
get_plugin_names = BACKEND_PLUGINS.get_plugin_names
get_plugins = BACKEND_PLUGINS.get_plugins
get_plugin = BACKEND_PLUGINS.get_plugin


def load_plugins(session):
    ''' Calls load_all_plugins, but only returns the backends plugin list '''
    return load_all_plugins(session)["backends"]
