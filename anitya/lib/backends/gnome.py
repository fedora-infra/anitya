# -*- coding: utf-8 -*-

"""
(c) 2014-2020 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>
  Michal Konecny <mkonecny@redhat.com>

"""

import logging
import re
from urllib.parse import urlparse

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException

REGEX = 'href="([0-9][0-9.]*)/"'


_log = logging.getLogger(__name__)


def use_gnome_cache_json(project):
    """Try retrieving the specified project's versions using the cache.json
    file if there is one.
    """
    output = []
    url = GnomeBackend.get_version_url(project) + "cache.json"
    req = BaseBackend.call_url(url)
    data = req.json()
    for item in data:
        if (
            isinstance(item, dict)
            and project.name in item
            and isinstance(item[project.name], list)
        ):
            output = item[project.name]

    # Filter retrieved versions
    filtered_versions = BaseBackend.filter_versions(output, project.version_filter)
    return filtered_versions


def use_gnome_regex(project):
    """Try retrieving the specified project's versions a regular expression."""
    output = []
    url = GnomeBackend.get_version_url(project)
    output = get_versions_by_regex(url, REGEX, project)
    return output


class GnomeBackend(BaseBackend):
    """Backend for projects hosted by the GNOME project on download.gnome.org."""

    name = "GNOME"
    default_version_scheme = "RPM"
    examples = [
        "https://download.gnome.org/sources/control-center/",
        "https://download.gnome.org/sources/evolution-caldav/",
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
        url = f"https://download.gnome.org/sources/{project.name}/"  # noqa: E231

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

        output = []
        try:
            # First try to get the version by using the cache.json file
            output = use_gnome_cache_json(project)
        except Exception as err:
            _log.exception(err)
            output = use_gnome_regex(project)

        return output

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        return "download.gnome.org" in url

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.

        Raises:
            AnityaPluginException: If URL cannot be parsed.
        """
        parsed = urlparse(url)
        path = parsed.path
        if "/sources/" in path:
            path = path.split("/sources/", 1)[1]
        elif path.startswith("sources/"):
            path = path.split("sources/", 1)[1]
        else:
            raise AnityaPluginException(f"Could not extract project name from {url}")

        parts = [p for p in path.split("/") if p]
        if not parts:
            raise AnityaPluginException(f"Could not extract project name from {url}")

        name = parts[0]
        for ext in (".tar.xz", ".tar.gz", ".tar.bz2", ".tar", ".tgz", ".zip"):
            if name.endswith(ext):
                name = name[: -len(ext)]
                name = re.sub(r"-\d.*$", "", name)
                break

        if not name:
            raise AnityaPluginException(f"Could not extract project name from {url}")

        homepage = f"https://download.gnome.org/sources/{name}/"
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
    def check_feed(cls):  # pragma: no cover
        """Method called to retrieve the latest uploads to a given backend,
        via, for example, RSS or an API.

        Not Supported

        Returns:
            :obj:`list`: A list of 4-tuples, containing the project name, homepage, the
            backend, and the version.

        Raises:
             NotImplementedError: If backend does not
                support batch updates.

        """
        raise NotImplementedError()
