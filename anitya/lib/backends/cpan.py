# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Ralph Bean <rbean@redhat.com>

"""

import anitya.lib.xml2dict as xml2dict

from anitya.lib.backends import BaseBackend, get_versions_by_regex, REGEX
from anitya.lib.exceptions import AnityaPluginException


class CpanBackend(BaseBackend):
    ''' The custom class for projects hosted on CPAN.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'CPAN (perl)'
    examples = [
        'http://search.cpan.org/dist/Net-Whois-Raw/',
        'http://search.cpan.org/dist/SOAP/',
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
        url = 'http://search.cpan.org/dist/%(name)s/' % {
            'name': project.name}

        regex = REGEX % {'name': project.name}

        return get_versions_by_regex(url, regex, project)

    @classmethod
    def check_feed(cls):
        ''' Return a generator over the latest uploads to CPAN

        by querying an RSS feed.
        '''

        url = 'http://search.cpan.org/uploads.rdf'

        try:
            response = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException('Could not contact %s' % url)

        try:
            parser = xml2dict.XML2Dict()
            data = parser.fromstring(response.text)
        except Exception:  # pragma: no cover
            raise AnityaPluginException('No XML returned by %s' % url)

        items = data['RDF']['item']
        for entry in items:
            title = entry['title']['value']
            name, version = title.rsplit('-', 1)
            homepage = 'http://search.cpan.org/dist/%s/' % name
            yield name, homepage, cls.name, version
