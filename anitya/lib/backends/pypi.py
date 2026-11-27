# -*- coding: utf-8 -*-

"""
(c) 2014-2020 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>
  Ralph Bean <rbean@redhat.com>
  Michal Konecny <mkonecny@redhat.com>

"""

import logging
from urllib.parse import urlparse

from anitya.lib import xml2dict
from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException

_log = logging.getLogger(__name__)


class PypiBackend(BaseBackend):
    """The PyPI class for project hosted on PyPI."""

    name = "PyPI"
    default_version_scheme = "Python (PEP 440)"
    examples = [
        "https://pypi.org/project/fedmsg/",
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
        url = cls.get_version_url(project)
        last_change = project.get_time_last_created_version()
        try:
            req = cls.call_url(url, last_change=last_change)
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from err

        # Handle missing packages explicitly
        if req.status_code == 404:
            raise AnityaPluginException(f"Package not found on PyPI: {url}")

        # Not modified
        if req.status_code == 304:
            return None

        try:
            data = req.json()
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"No JSON returned by {url}") from err

        return data["info"]["version"]

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
        url = f"https://pypi.org/pypi/{project.name}/json"  # noqa: E231

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
        last_change = project.get_time_last_created_version()
        try:
            req = cls.call_url(url, last_change=last_change)
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from err

        # Handle missing packages explicitly
        if req.status_code == 404:
            raise AnityaPluginException(f"Package not found on PyPI: {url}")

        # Not modified
        if req.status_code == 304:
            return []

        try:
            data = req.json()
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"No JSON returned by {url}") from err

        # Filter yanked versions
        unyanked_versions = []

        # Just return empty list if "releases" key is missing in json
        if "releases" not in data:
            return []

        for version in data["releases"].keys():
            if not data["releases"][version] == []:
                if "yanked" in data["releases"][version][0]:
                    if data["releases"][version][0]["yanked"]:
                        continue
            # Old releases doesn't contain metadata
            unyanked_versions.append(version)

        # Filter retrieved versions
        filtered_versions = cls.filter_versions(
            unyanked_versions,
            project.version_filter,
        )
        return filtered_versions

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        return url.startswith(
            (
                "https://pypi.org",
                "http://pypi.org",
                "https://www.pypi.org",
                "http://www.pypi.org",
                "https://pypi.python.org",
                "http://pypi.python.org",
            )
        )

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.

        Raises:
            AnityaPluginException: If URL cannot be parsed into a valid project.
        """
        if not cls.is_url_valid(url):
            raise AnityaPluginException(f"Could not extract project name from {url}")

        parsed = urlparse(url)
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]

        name = None
        if "project" in parts:
            idx = parts.index("project")
            if len(parts) > idx + 1:
                name = parts[idx + 1]
        elif "pypi" in parts:
            idx = parts.index("pypi")
            if len(parts) > idx + 1:
                name = parts[idx + 1]
        elif len(parts) == 1:
            name = parts[0]

        if not name or name in ("project", "pypi"):
            raise AnityaPluginException(f"Could not extract project name from {url}")

        homepage = f"https://pypi.org/project/{name}/"
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
        """Return a generator over the latest 40 uploads to PyPI

        by querying an RSS feed.
        """

        url = "https://pypi.org/rss/updates.xml"

        try:
            response = cls.call_url(url)
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from err

        try:
            parser = xml2dict.XML2Dict()
            data = parser.fromstring(response.text)
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"No XML returned by {url}") from err

        items = data.get("rss", {}).get("channel", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        for entry in items:
            if "title" not in entry or "value" not in entry["title"]:
                continue
            title = entry["title"]["value"]
            try:
                name, version = title.rsplit(None, 1)
            except ValueError:
                _log.info(
                    "Unable to parse PyPI title %s into a package name and version",
                    title,
                )
                continue
            homepage = f"https://pypi.org/project/{name}/"  # noqa: E231
            yield name, homepage, cls.name, version
