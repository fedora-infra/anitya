# -*- coding: utf-8 -*-

"""
(c) 2014-2020 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>
  Ralph Bean <rbean@redhat.com>

"""

import logging
import re

from anitya.lib import xml2dict
from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException

_log = logging.getLogger(__name__)


def _get_versions(url):
    """Retrieve the versions for the provided url."""
    try:
        req = PeclBackend.call_url(url)
    except Exception as exc:  # pragma: no cover
        raise AnityaPluginException(f"Could not contact {url}") from exc

    data = req.text
    versions = []
    for line in data.split("\n"):
        if "<v>" in line and "</v>" in line:
            version = line.split("v>", 2)[1].split("</")[0]
            versions.append(version)
    return versions


class PeclBackend(BaseBackend):
    """The backend class for projects hosted on pecl.php.net."""

    name = "PECL"
    default_version_scheme = "RPM"
    examples = [
        "https://pecl.php.net/package/inotify",
        "https://pecl.php.net/package/gnupg",
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
        versions = cls.get_versions(project)
        if not versions:
            raise AnityaPluginException(
                f"Could not retrieve latest version for {project.name}"
            )
        return versions[0]

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
        name = project.name.lower()
        url_template = "https://pecl.php.net/rest/r/%(name)s/allreleases.xml"

        if "-" in name:
            name = name.replace("-", "_")

        url = url_template % {"name": name}

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
        versions = []
        versions = _get_versions(url)

        if not versions:
            raise AnityaPluginException(f"No versions found for {project.name.lower()}")

        # Filter retrieved versions
        filtered_versions = BaseBackend.filter_versions(
            versions, project.version_filter
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
        return "pecl.php.net" in url

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
        if "package-info.php" in url and "package=" in url:
            raw_name = url.split("package=")[-1].split("&")[0].split("#")[0]
        elif "/package/" in clean_url:
            path = clean_url.split("/package/")[-1].strip("/")
            raw_name = path.split("/")[0]
        else:
            raw_name = clean_url.split("/")[-1]

        match = re.match(r"^(.+)-(\d[\d.]*)$", raw_name)
        if match:
            name = match.group(1)
        else:
            name = raw_name

        homepage = f"https://pecl.php.net/package/{name}"
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
        """Return a generator over the latest 10 uploads to PECL

        by querying an RSS feed.
        """

        url = "https://pecl.php.net/feeds/latest.rss"

        try:
            response = cls.call_url(url)
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from exc

        try:
            parser = xml2dict.XML2Dict()
            data = parser.fromstring(response.text)
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"No XML returned by {url}") from exc

        items = data.get("RDF", {}).get("item", [])
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
                    "Unable to parse PECL title %s into a package name and version",
                    title,
                )
                continue
            homepage = f"https://pecl.php.net/package/{name}"  # noqa: E231
            yield name, homepage, cls.name, version
