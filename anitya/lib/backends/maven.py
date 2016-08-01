# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Michael Simacek <msimacek@redhat.com>

"""

from __future__ import absolute_import
import re

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


REGEX = r'\<a[^>]+\>(\d[^</]*)'


class MavenBackend(BaseBackend):
    ''' Backend for projects hosted on Maven Central '''

    name = 'Maven Central'
    examples = [
        'http://repo1.maven.org/maven2/plexus/plexus-compiler/',
        'http://repo1.maven.org/maven2/com/google/inject/guice/',
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
        if re.match(r'https?://repo\d+.maven.org/', project.homepage):
            url = project.homepage
        else:
            coordinates = project.version_url or project.name
            if ':' not in coordinates:
                raise AnityaPluginException(
                    "Aritfact needs to be in format groupId:artifactId")
            url = 'http://repo1.maven.org/maven2/{path}'\
                  .format(path=coordinates.replace('.', '/')
                          .replace(':', '/'))

        return get_versions_by_regex(url, REGEX, project)
