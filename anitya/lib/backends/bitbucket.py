# -*- coding: utf-8 -*-

"""
 (c) 2015-2016 - Copyright Vivek Anand

 Authors:
   Vivek Anand <vivekanand1101@gmail.com>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


REGEX = 'class="name">([^<]*[^tip])</td'


class BitBucketBackend(BaseBackend):
    ''' The custom class for projects hosted on bitbucket.org

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'BitBucket'
    examples = [
        'https://bitbucket.org/zzzeek/sqlalchemy',
        'https://bitbucket.org/cherrypy/cherrypy',
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
            url_template = 'https://bitbucket.org/%(version_url)s/'\
                'downloads?tab=tags'
            version_url = project.version_url.replace(
                'https://bitbucket.org/', '')
            url = url_template % {'version_url': version_url}
        elif project.homepage.startswith('https://bitbucket.org'):
            url = project.homepage
            if url.endswith('/'):
                url = project.homepage[:1]
            url += '/downloads?tab=tags'
        else:
            raise AnityaPluginException(
                'Project %s was incorrectly set-up' % project.name)

        return get_versions_by_regex(url, REGEX, project)
