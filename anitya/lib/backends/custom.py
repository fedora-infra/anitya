# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex, REGEX


REGEX_ALIASES = {
    'DEFAULT': REGEX,
}


class CustomBackend(BaseBackend):
    ''' The custom class for project having a special hosting.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'custom'
    examples = [
        'https://subsurface-divelog.org/downloads/',
        'https://www.geany.org/Download/Releases',
    ]
    more_info = 'More information in the '\
        '<a href=\'/about#test-your-regex\'>about#test-your-regex</a>'
    default_regex = REGEX % {'name': '{project name}'}

    @classmethod
    def get_version(cls, project):
        ''' Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
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

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        '''
        url = project.version_url

        regex = REGEX_ALIASES['DEFAULT']
        if project.regex:
            regex = REGEX_ALIASES.get(project.regex, project.regex)

        if '%(name)' in regex:
            regex = regex % {'name': project.name.replace('+', '\+')}

        return get_versions_by_regex(
            url, regex, project, insecure=project.insecure)
