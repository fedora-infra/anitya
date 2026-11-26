# -*- coding: utf-8 -*-

"""
(c) 2014 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from urllib.parse import urlparse

from anitya.lib.backends import REGEX, BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


class SourceforgeBackend(BaseBackend):
    """The custom class for projects hosted on sourceforge.net.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "Sourceforge"
    default_version_scheme = "RPM"
    check_name_or_url = True
    examples = [
        "https://sourceforge.net/projects/filezilla/",
        "https://sourceforge.net/projects/file-folder-ren/",
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
        url_template = "https://sourceforge.net/projects/%(name)s/rss"
        raw_name = project.version_url or project.name or ""
        for prefix in (
            "https://sourceforge.net/projects/",
            "http://sourceforge.net/projects/",
            "https://www.sourceforge.net/projects/",
            "http://www.sourceforge.net/projects/",
        ):
            if raw_name.startswith(prefix):
                raw_name = raw_name[len(prefix) :]
                break

        name = raw_name.strip("/")
        if "/" in name:
            name = name.split("/")[0]

        url = url_template % {"name": name.replace("+", r"\+")}

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
        regex = REGEX % {"name": project.name.replace("+", r"\+")}

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
        return "sourceforge.net/projects" in url

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
        orig_url = url
        if not cls.is_url_valid(orig_url):
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if path.startswith("projects"):
            path = path[len("projects") :].strip("/")

        for subpath in (
            "/files",
            "/reviews",
            "/support",
            "/directory",
            "/develop",
            "/news",
        ):
            if subpath in path:
                path = path.split(subpath)[0].rstrip("/")

        parts = [p for p in path.split("/") if p]
        if not parts:
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        name = parts[0]
        homepage = f"https://sourceforge.net/projects/{name}/"
        version_url = name
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

        Not all backends may support this.  It can be used to look for updates
        much more quickly than scanning all known projects.

        Returns:
            :obj:`list`: A list of 4-tuples, containing the project name, homepage, the
            backend, and the version.

        Raises:
            AnityaPluginException: A
                :obj:`anitya.lib.exceptions.AnityaPluginException` exception
                when the versions cannot be retrieved correctly
            NotImplementedError: If backend does not
                support batch updates.

        """
        raise NotImplementedError()
