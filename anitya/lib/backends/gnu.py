# -*- coding: utf-8 -*-

"""
(c) 2014 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import re

import six

from anitya.lib.backends import REGEX, BaseBackend, get_versions_by_regex_for_text
from anitya.lib.exceptions import AnityaPluginException

DEFAULT_REGEX = 'href="([0-9][0-9.]*)/"'


class GnuBackend(BaseBackend):
    """The custom class for project hosted on gnu.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "GNU project"
    default_version_scheme = "RPM"
    examples = [
        "https://ftpmirror.gnu.org/gnash/",
        "https://ftp.gnu.org/gnu/sed/",
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
        url = f"https://ftpmirror.gnu.org/{project.name}/"  # noqa: E231

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
            raise AnityaPluginException(
                f'Could not call : "{url}" of "{project.name}"'
            ) from err

        versions = []
        if not isinstance(req, six.string_types):
            # Not modified
            if req.status_code == 304:
                return versions

            if req.status_code != 200:
                raise AnityaPluginException(
                    f"{project.name}: Server responded with status "
                    f'"{req.status_code}": "{req.reason}"'
                )

        try:
            regex = REGEX % {"name": project.name}
            versions = get_versions_by_regex_for_text(req.text, url, regex, project)
        except AnityaPluginException:
            versions = get_versions_by_regex_for_text(
                req.text, url, DEFAULT_REGEX, project
            )

        return versions

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        valid_prefixes = (
            "https://ftpmirror.gnu.org",
            "http://ftpmirror.gnu.org",
            "https://ftp.gnu.org",
            "http://ftp.gnu.org",
            "https://www.gnu.org/software/",
            "http://www.gnu.org/software/",
        )
        return url.startswith(valid_prefixes)

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
        clean_url = re.sub(
            r"/[^/]+\.(?:tar|t[bglx]z|tbz2|zip|gz|xz|bz2|sig)$", "", clean_url
        )
        clean_url = clean_url.rstrip("/")

        if "/software/" in clean_url:
            path = clean_url.split("/software/")[-1].strip("/")
            name = path.split("/")[0]
        elif "/gnu/" in clean_url:
            path = clean_url.split("/gnu/")[-1].strip("/")
            name = path.split("/")[0]
        else:
            name = clean_url.split("/")[-1]

        homepage = f"https://ftpmirror.gnu.org/{name}/"
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
