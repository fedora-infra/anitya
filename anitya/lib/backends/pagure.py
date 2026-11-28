# -*- coding: utf-8 -*-

"""
(c) 2015-2020 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>
  Michal Konecny <mkonecny@redhat.com>

"""

from __future__ import print_function

from urllib.parse import urlparse

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class PagureBackend(BaseBackend):
    """The pagure class for project hosted on pagure.io."""

    name = "pagure"
    default_version_scheme = "RPM"
    examples = ["https://pagure.io/pagure", "https://pagure.io/flask-multistatic"]

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
        versions = cls.get_ordered_versions(project)
        if versions:
            return versions[-1]

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
        raw_url = ""
        if project.version_url:
            raw_url = project.version_url
        elif project.homepage:
            raw_url = project.homepage

        if raw_url and cls.is_url_valid(raw_url):
            clean = cls._clean_url(raw_url)
            parsed = urlparse(clean)
            path = parsed.path.strip("/")
            if path.startswith("api/0/"):
                path = path[len("api/0/") :]
            if path.endswith("/git"):
                path = path[: -len("/git")]
            if path:
                return f"https://pagure.io/api/0/{path}/git/tags"

        return f"https://pagure.io/api/0/{project.name}/git/tags"

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
            raise AnityaPluginException(f"Could not contact {url}: {str(err)}") from err

        # Not modified
        if req.status_code == 304:
            return []

        try:
            data = req.json()
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"No JSON returned by {url}") from err

        # Filter retrieved versions
        filtered_versions = cls.filter_versions(
            data.get("tags", []), project.version_filter
        )

        return filtered_versions

    @classmethod
    def _clean_url(cls, url: str) -> str:
        """Strip query params, fragments, trailing slashes, .git, and subpaths."""
        clean = url.split("?")[0].split("#")[0].rstrip("/")
        if clean.endswith(".git"):
            clean = clean[:-4].rstrip("/")
        for subpath in ("/tree/", "/tags", "/releases", "/commits/", "/blob/"):
            if subpath in clean:
                clean = clean.split(subpath)[0].rstrip("/")
        return clean

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
                "https://pagure.io",
                "http://pagure.io",
                "https://www.pagure.io",
                "http://www.pagure.io",
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

        clean_url = cls._clean_url(url)
        parsed = urlparse(clean_url)
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]

        if not parts:
            raise AnityaPluginException(f"Could not extract project name from {url}")

        name = parts[-1]
        homepage = f"https://pagure.io/{path}"
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
