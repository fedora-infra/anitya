# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

Module handling the load/call of the plugins of anitya
"""

import logging

from sqlalchemy.exc import SQLAlchemyError

from straight.plugin import load

import anitya.lib.model as model
from anitya.lib.backends import BaseBackend

log = logging.getLogger(__name__)

def load_plugins(session):
    ''' Load all the plugins and insert them in the database if they are
    not already present. '''
    backends = [bcke.name for bcke in model.Backend.all(session)]

    plugins = list(get_plugins())
    # Add any new Backend definitions (including new Ecosystems)
    plugin_names = [plugin.name for plugin in plugins]
    plugins_by_name = dict(zip(plugin_names, plugins))
    for backend in set(backends).symmetric_difference(set(plugin_names)):
        log.info("Registering backend %r", backend)
        bcke = model.Backend(name=backend)
        session.add(bcke)
        eco_name = plugins_by_name[backend].ecosystem_name
        if eco_name is not None:
            log.info("Registering ecosystem %r for backend %r",
                     eco_name, backend)
            ecosystem = model.Ecosystem(name=eco_name, backend=bcke)
            session.add(ecosystem)
        try:
            session.commit()
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot test this as it would come from a defective DB
            print(err)
            session.rollback()
    # Add any new Ecosystem definitions for existing plugins
    #    Note: not unit tested since it requires a changing plugin definition
    ecosystems = [ecosystem.name for ecosystem in model.Ecosystem.all(session)]
    backends_by_ecosystem = dict((plugin.ecosystem_name, plugin.name)
                                    for plugin in plugins
                                        if plugin.ecosystem_name is not None)
    for eco_name in set(ecosystems).symmetric_difference(set(backends_by_ecosystem)):
        backend = backends_by_ecosystem[eco_name]
        bcke = model.Backend.by_name(session, backend)
        log.info("Registering ecosystem %r for backend %r", eco_name, backend)
        ecosystem = model.Ecosystem(name=eco_name, backend=bcke)
        session.add(ecosystem)
        try:
            session.commit()
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot test this as it would come from a defective DB
            print(err)
            session.rollback()

    return plugins


def get_plugin_names():
    ''' Return the list of plugins names. '''
    plugins = load('anitya.lib.backends', subclasses=BaseBackend)
    output = [plugin.name for plugin in plugins]
    return output


def get_plugins():
    ''' Return the list of plugins. '''
    return load('anitya.lib.backends', subclasses=BaseBackend)


def get_plugin(plugin_name):
    ''' Return the plugin corresponding to the given plugin name. '''
    plugins = load('anitya.lib.backends', subclasses=BaseBackend)
    for plugin in plugins:
        if plugin.name.lower() == plugin_name.lower():
            return plugin
