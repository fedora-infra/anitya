# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import re
# sre_constants contains re exceptions
import sre_constants

import requests

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException

REGEX = b'href="([0-9][0-9.]*)/"'


class FolderBackend(BaseBackend):
    ''' The custom class for project having a special hosting.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'folder'
    examples = [
        'http://ftp.gnu.org/pub/gnu/gnash/',
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
            req = requests.get(url)
        except Exception:
            raise AnityaPluginException(
                'Could not call : "%s" of "%s"' % (url, project.name))

        try:
            upstream_versions = list(set(re.findall(REGEX, req.text)))
        except sre_constants.error:
            raise AnityaPluginException(
                "%s: invalid regular expression" % project.name)

        for index, version in enumerate(upstream_versions):
            if type(version) == tuple:
                version = ".".join([v for v in version if not v == ""])
                upstream_versions[index] = version
            if " " in version:
                raise AnityaPluginException(
                    "%s: invalid upstream version:>%s< - %s - %s " % (
                        project.name, version, project.version_url,
                        REGEX))
        if len(upstream_versions) == 0:
            raise AnityaPluginException(
                "%(name)s: no upstream version found. - %(version_url)s -  "
                "%(regex)s" % {
                    'name': project.name, 'version_url': project.version_url,
                    'regex': REGEX})

        return upstream_versions
