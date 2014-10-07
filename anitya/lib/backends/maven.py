# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Michael Simacek <msimacek@redhat.com>

"""


from anitya.lib.backends import BaseBackend, get_versions_by_regex


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
        url = 'http://repo1.maven.org/maven2/{path}'\
              .format(path=project.name.replace('.', '/').replace(':', '/'))

        regex = r'\<a[^>]+\>(\d[^</]*)'

        return get_versions_by_regex(url, regex, project)
