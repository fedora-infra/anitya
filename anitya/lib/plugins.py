# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

Module handling the load/call of the plugins of anitya
"""

from sqlalchemy.exc import SQLAlchemyError

from straight.plugin import load

import anitya.lib.model as model
from anitya.lib.backends import BaseBackend


def load_plugins(session):
    ''' Load all the plugins and insert them in the database if they are
    not already present. '''
    backends = [bcke.name for bcke in model.Backend.all(session)]

    plugins = get_plugins()
    plg_names = [plugin.name for plugin in plugins]
    for backend in set(backends).symmetric_difference(set(plg_names)):
        bcke = model.Backend(name=backend)
        session.add(bcke)
        try:
            session.commit()
        except SQLAlchemyError, err:  # pragma: no cover
            # We cannot test this as it would come from a defective DB
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
        if plugin.name == plugin_name:
            return plugin
