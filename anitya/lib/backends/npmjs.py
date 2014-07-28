# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""


from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class NpmjsBackend(BaseBackend):
    ''' The custom class for projects hosted on npmjs.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'npmjs'
    examples = [
        'https://www.npmjs.org/package/request',
        'https://www.npmjs.org/package/colors',
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
        url_template = 'http://registry.npmjs.org/%(name)s'

        url = url_template % {'name': project.name}

        try:
            req = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException('Could not contact %s' % url)

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException('No JSON returned by %s' % url)

        if 'dist-tags' in data and 'latest' in data['dist-tags']:
            return data['dist-tags']['latest']
        else:
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
        url_template = 'http://registry.npmjs.org/%(name)s'

        url = url_template % {'name': project.name}

        try:
            req = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException('Could not contact %s' % url)

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException('No JSON returned by %s' % url)

        if 'error' in data or 'versions' not in data:
            raise AnityaPluginException('No versions found at %s' % url)

        return data['versions'].keys()
