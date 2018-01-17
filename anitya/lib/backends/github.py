# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


REGEX = 'class="tag-name">([^<]*)</span'


class GithubBackend(BaseBackend):
    ''' The custom class for projects hosted on github.com.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'GitHub'
    examples = [
        'https://github.com/fedora-infra/fedocal',
        'https://github.com/fedora-infra/pkgdb2',
    ]

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
        if project.version_url:
            url_template = 'https://github.com/%(version_url)s/tags'
            version_url = project.version_url.replace(
                'https://github.com/', '')
            url = url_template % {'version_url': version_url}
        elif project.homepage.startswith('https://github.com'):
            url = project.homepage
            if url.endswith('/'):
                url = project.homepage[:-1]
            url += '/tags'
        else:
            raise AnityaPluginException(
                'Project %s was incorrectly set-up' % project.name)

        return get_versions_by_regex(url, REGEX, project)
