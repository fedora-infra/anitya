# -*- coding: utf-8 -*-

"""
 (c) 2015 - Copyright Red Hat Inc
 Authors:
   Jens Petersen <petersen@redhat.com>
"""


from anitya.lib.backends import BaseBackend, get_versions_by_regex, REGEX


class StackageBackend(BaseBackend):
    ''' The custom class for Haskell projects hosted on Stackage.org.
    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'Stackage'
    examples = [
        'https://www.stackage.org/package/conduit',
        'https://www.stackage.org/package/cabal-install',
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
        url = 'https://www.stackage.org/package/%(name)s' % {
            'name': project.name}

        regex = '%(name)s <span class="latest-version">([\d.]*) *</span>' % {'name': project.name}

        return get_versions_by_regex(url, regex, project)
