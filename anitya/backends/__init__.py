#-*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

class BaseBackend(object):
    ''' The base class that all the different backend should extend. '''

    name = None

    @classmethod
    def get_version(self, project):
        ''' Method called to retrieve the versions of the projects provided,
        project that relies on the backend of this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.

        '''
        pass
