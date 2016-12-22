# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import logging

from anitya.lib.backends import BaseBackend, get_versions_by_regex


REGEX = 'href="([0-9][0-9.]*)/"'


_log = logging.getLogger(__name__)


def use_gnome_cache_json(project):
    ''' Try retrieving the specified project's versions using the cache.json
    file if there is one.
    '''
    output = []
    url = 'https://download.gnome.org/sources/%(name)s/cache.json' % {
        'name': project.name}
    req = BaseBackend.call_url(url)
    data = req.json()
    for item in data:
        if isinstance(item, dict) and project.name in item \
                and isinstance(item[project.name], list):
            output = item[project.name]
    return output


def use_gnome_regex(project):
    ''' Try retrieving the specified project's versions a regular expression.
    '''
    output = []
    url = 'https://download.gnome.org/sources/%(name)s/' % {
        'name': project.name}
    output = get_versions_by_regex(url, REGEX, project)
    return output


class GnomeBackend(BaseBackend):
    ''' The custom class for project hosted by the GNOME project.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'GNOME'
    examples = [
        'https://download.gnome.org/sources/control-center/',
        'https://download.gnome.org/sources/evolution-caldav/',
    ]

    @classmethod
    def get_version(cls, project):
        ''' Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: the latest version found upstream
        :return type: str
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the version cannot be retrieved correctly

        '''
        return cls.get_ordered_versions(project)[-1]

    @classmethod
    def get_versions(cls, project):
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        '''

        output = []
        try:
            # First try to get the version by using the cache.json file
            output = use_gnome_cache_json(project)
        except Exception as err:
            _log.exception(err)
            output = use_gnome_regex(project)

        return output
