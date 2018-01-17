# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


REGEX = '<version>6\.x-([^<]+)</version>'


class Drupal6Backend(BaseBackend):
    ''' The custom class for projects hosted on ftp.debian.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'Drupal6'
    examples = [
        'https://www.drupal.org/project/pathauto',
        'https://www.drupal.org/project/wysiwyg',
    ]
    more_info = 'If the project exists for Drupal 6 and 7 and is '\
        'monitored for both, you can prefix the name with `Drupal6:`, '\
        'for example: `Drupal6: cck`.'

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
        name = project.name
        if name.lower().strip().startswith('drupal6:'):
            name = name[len('drupal6:'):].strip()

        url_template = 'https://updates.drupal.org/release-history/'\
            '%(name)s/6.x'

        url = url_template % {'name': name}
        regex = REGEX % {'name': name}
        versions = None

        try:
            versions = get_versions_by_regex(url, regex, project)
        except AnityaPluginException as err:
            if '-' not in project.name:
                raise err
            name = project.name.replace("-", "_")
            url = url_template % {'name': name}
            regex = REGEX % {'name': name}
            versions = get_versions_by_regex(url, regex, project)

        return versions
