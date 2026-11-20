# -*- coding: utf-8 -*-

"""
(c) 2014-2016 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>
  Ralph Bean <rbean@redhat.com>

"""

import logging

from defusedxml import ElementTree as ET

from anitya.lib.backends import REGEX, BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException

_log = logging.getLogger(__name__)


class CpanBackend(BaseBackend):
    """The backend class for projects hosted on CPAN."""

    name = "CPAN (perl)"
    default_version_scheme = "RPM"
    examples = [
        "https://metacpan.org/dist/Net-Whois-Raw/",
        "https://metacpan.org/dist/SOAP/",
    ]

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
        url = f"https://metacpan.org/dist/{project.name}/"  # noqa: E231

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
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        return "metacpan.org" in url

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.
        """
        clean_url = url.split("?")[0].split("#")[0].rstrip("/")
        for prefix in ("/dist/", "/pod/", "/release/"):
            if prefix in clean_url:
                name = clean_url.split(prefix)[-1].split("/")[0]
                break
        else:
            name = clean_url.split("/")[-1]

        homepage = f"https://metacpan.org/dist/{name}/"
        version_url = homepage
        version_scheme = cls.default_version_scheme
        backend = cls.name
        return {
            "name": name,
            "homepage": homepage,
            "backend": backend,
            "version_url": version_url,
            "version_scheme": version_scheme,
        }

    @classmethod
    def check_feed(cls):
        """Return a generator over the latest uploads to CPAN

        by querying an RSS feed.
        """

        url = "https://metacpan.org/feed/recent"

        try:
            response = cls.call_url(url)
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from exc

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as exc:
            raise AnityaPluginException(f"No XML returned by {url}") from exc

        for item in root.iter(tag="{http://purl.org/rss/1.0/}item"):
            title = item.find("{http://purl.org/rss/1.0/}title")
            if title is None or not title.text:
                continue
            try:
                name, version = title.text.rsplit("-", 1)
            except ValueError:
                _log.info(
                    "Unable to parse CPAN title %s into a package name and version",
                    title.text,
                )
                continue
            homepage = f"https://metacpan.org/dist/{name}/"  # noqa: E231
            yield name, homepage, cls.name, version
