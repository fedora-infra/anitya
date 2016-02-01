# -*- coding: utf-8 -*-

"""
 (c) 2015 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""


from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class PagureBackend(BaseBackend):
    ''' The pagure class for project hosted on pagure.io. '''

    name = 'pagure'
    examples = [
        'https://pagure.io/pagure',
        'https://pagure.io/flask-multistatic',
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
        versions = cls.get_ordered_versions(project)
        if versions:
            return versions[-1]

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
        url = 'https://pagure.io/api/0/%s/git/tags' % project.name
        try:
            req = cls.call_url(url)
        except Exception as err:  # pragma: no cover
            print err
            raise AnityaPluginException('Could not contact %s' % url)

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException('No JSON returned by %s' % url)

        return data.get('tags', [])
