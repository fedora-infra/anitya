# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import (
    BaseBackend, get_versions_by_regex_for_text, REGEX)
from anitya.lib.exceptions import AnityaPluginException

DEFAULT_REGEX = b'href="([0-9][0-9.]*)/"'


class FolderBackend(BaseBackend):
    ''' The custom class for project having a special hosting.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'folder'
    examples = [
        'http://ftp.gnu.org/pub/gnu/gnash/',
        'http://subsurface.hohndel.org/downloads/',
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
        url = project.version_url

        try:
            req = cls.call_url(url)
        except Exception:
            raise AnityaPluginException(
                'Could not call : "%s" of "%s"' % (url, project.name))

        versions = None
        try:
            regex = REGEX % {'name': project.name}
            versions = get_versions_by_regex_for_text(
                req.text, url, regex, project)
        except AnityaPluginException:
            versions = get_versions_by_regex_for_text(
                req.text, url, DEFAULT_REGEX, project)

        return versions
