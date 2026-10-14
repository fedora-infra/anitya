# -*- coding: utf-8 -*-

"""
(c) 2014-2016 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException

REGEX = r"<version>7\.x-([^<]+)</version>"


class Drupal7Backend(BaseBackend):
    """The custom class for projects hosted on ftp.debian.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "Drupal7"
    examples = [
        "https://www.drupal.org/project/pathauto",
        "https://www.drupal.org/project/wysiwyg",
    ]
    more_info = (
        "If the project exists for Drupal 6 and 7 and is "
        "monitored for both, you can prefix the name with `Drupal7:`, "
        "for example: `Drupal7: cck`."
    )

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
        name = project.name
        if name.lower().strip().startswith("drupal7:"):
            name = name[len("drupal7:") :].strip()
        if "-" in project.name:
            name = project.name.replace("-", "_")

        return f"https://updates.drupal.org/release-history/{name}/7.x"  # noqa: E231

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
        name = project.name
        if "-" in project.name:
            name = project.name.replace("-", "_")
        regex = REGEX % {"name": name}
        versions = None

        try:
            versions = get_versions_by_regex(url, regex, project)
        except AnityaPluginException as err:
            raise err

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
        return url.startswith("https://www.drupal.org")

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.
        """
        homepage = url
        version_url = url
        name = "Drupal7: " + url.rstrip("/").split("/")[-1]
        version_scheme = "RPM"
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
