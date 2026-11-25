# -*- coding: utf-8 -*-

"""
(c) 2015 - Copyright Red Hat Inc
Authors:
  Jens Petersen <petersen@redhat.com>
"""

import re

from anitya.lib.backends import BaseBackend, get_versions_by_regex


class StackageBackend(BaseBackend):
    """The backend class for Haskell projects hosted on Stackage.org."""

    name = "Stackage"
    default_version_scheme = "RPM"
    examples = [
        "https://www.stackage.org/package/conduit",
        "https://www.stackage.org/package/cabal-install",
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
        url = f"https://www.stackage.org/package/{project.name}"  # noqa: E231

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

        regex = (
            rf"<a href=\"https://hackage.haskell.org/package/{project.name}\">"  # noqa: E231
            r"<span class=\"version\">([\d.]*).*</span></a>"
        )

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
        return "stackage.org" in url

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
        if "/package/" in clean_url:
            path = clean_url.split("/package/")[-1].strip("/")
            raw_name = path.split("/")[0]
        else:
            raw_name = clean_url.split("/")[-1]

        match = re.match(r"^(.+)-(\d[\d.]*)$", raw_name)
        if match:
            name = match.group(1)
        else:
            name = raw_name

        homepage = f"https://www.stackage.org/package/{name}"
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
