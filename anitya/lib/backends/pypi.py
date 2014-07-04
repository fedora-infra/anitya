# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import requests

from anitya.backends import BaseBackend


class PypiBackend(BaseBackend):
    ''' The PyPI class for project hosted on PyPI. '''

    name = 'pypi'

    @classmethod
    def get_version(self, project):
        ''' Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.

        '''
        url = 'https://pypi.python.org/pypi/%s/json' % project.name
        req = requests.get(url)
        try:
            data = req.json()
        except Exception:
            return

        return data['info']['version']

    @classmethod
    def get_versions(self, project):
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list

        '''
        url = 'https://pypi.python.org/pypi/%s/json' % project.name
        req = requests.get(url)
        try:
            data = req.json()
        except Exception:
            return

        return data['releases'].keys()
