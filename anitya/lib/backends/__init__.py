# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import re
# sre_constants contains re exceptions
import sre_constants

import requests
import anitya
from anitya.lib.exceptions import AnityaPluginException


class BaseBackend(object):
    ''' The base class that all the different backend should extend. '''

    name = None

    @classmethod
    def get_version(self, project):  # pragma: no cover
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
        pass

    @classmethod
    def get_versions(self, project):  # pragma: no cover
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
        pass

    @classmethod
    def get_ordered_versions(self, project):
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, ordered from the oldest to the newest.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        '''
        vlist = self.get_versions(project)
        return anitya.order_versions(vlist)


def get_versions_by_regex(url, regex, project):
    ''' For the provided url, return all the version retrieved via the
    specified regular expression.

    '''

    try:
        req = requests.get(url)
    except Exception:
        raise AnityaPluginException(
            'Could not call : "%s" of "%s"' % (url, project.name))

    try:
        upstream_versions = list(set(re.findall(regex, req.text)))
    except sre_constants.error:
        raise AnityaPluginException(
            "%s: invalid regular expression" % project.name)

    for index, version in enumerate(upstream_versions):
        if type(version) == tuple:
            version = ".".join([v for v in version if not v == ""])
            upstream_versions[index] = version
        if " " in version:
            raise AnityaPluginException(
                "%s: invalid upstream version:>%s< - %s - %s " % (
                    project.name, version, project.version_url, regex))
    if len(upstream_versions) == 0:
        raise AnityaPluginException(
            "%(name)s: no upstream version found. - %(version_url)s -  "
            "%(regex)s" % {
                'name': project.name, 'version_url': project.version_url,
                'regex': regex})

    return upstream_versions
