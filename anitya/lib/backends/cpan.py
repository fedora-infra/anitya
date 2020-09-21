# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Ralph Bean <rbean@redhat.com>

"""

import logging

from defusedxml import ElementTree as ET

from anitya.lib.backends import BaseBackend, get_versions_by_regex, REGEX
from anitya.lib.exceptions import AnityaPluginException

_log = logging.getLogger(__name__)


class CpanBackend(BaseBackend):
    """The custom class for projects hosted on CPAN.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "CPAN (perl)"
    examples = [
        "https://metacpan.org/release/Net-Whois-Raw/",
        "https://metacpan.org/release/SOAP/",
    ]

    @classmethod
    def get_version(cls, project):
        """Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: the latest version found upstream
        :return type: str
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the version cannot be retrieved correctly

        """
        return cls.get_ordered_versions(project)[-1]

    @classmethod
    def get_version_url(cls, project):
        """Method called to retrieve the url used to check for new version
        of the project provided, project that relies on the backend of this plugin.

        Attributes:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            str: url used for version checking
        """
        url = "https://metacpan.org/release/%(name)s/" % {"name": project.name}

        return url

    @classmethod
    def get_versions(cls, project):
        """Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        """
        url = cls.get_version_url(project)

        regex = REGEX % {"name": project.name}

        return get_versions_by_regex(url, regex, project)

    @classmethod
    def check_feed(cls):
        """Return a generator over the latest uploads to CPAN

        by querying an RSS feed.
        """

        url = "https://metacpan.org/feed/recent"

        try:
            response = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException("Could not contact %s" % url)

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            raise AnityaPluginException("No XML returned by %s" % url)

        for item in root.iter(tag="{http://purl.org/rss/1.0/}item"):
            title = item.find("{http://purl.org/rss/1.0/}title")
            try:
                name, version = title.text.rsplit("-", 1)
            except ValueError:
                _log.info("Unable to parse CPAN package %s into a name and version")
            homepage = "https://metacpan.org/release/%s/" % name
            yield name, homepage, cls.name, version
