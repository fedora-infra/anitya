# -*- coding: utf-8 -*-

"""
(c) 2014 - Copyright Red Hat Inc

Authors:
  Michael Simacek <msimacek@redhat.com>

"""

import re
from urllib.parse import unquote, urlparse

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException

VERSION_REGEX = re.compile(r"\<a[^>]+\>(\d[^</]*)")
MAVEN_HOMEPAGE_RE = re.compile(
    r"https?://(repo\d+\.maven\.org|repo\.maven\.apache\.org)/"
)
# Maven artifact coordinates in format groupId:artifactId
COORDINATES_RE = re.compile(r"([^:]+):([^:]+)")


class MavenBackend(BaseBackend):
    """Backend for projects hosted on Maven Central"""

    name = "Maven Central"
    default_version_scheme = "RPM"
    check_name_or_url = True
    examples = [
        "https://repo1.maven.org/maven2/plexus/plexus-compiler/",
        "https://repo1.maven.org/maven2/com/google/inject/guice/",
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
        if MAVEN_HOMEPAGE_RE.match(project.homepage):
            url = project.homepage
        else:
            coordinates = project.version_url or project.name
            match = COORDINATES_RE.match(coordinates)
            if not match:
                return ""
            group_id = match.group(1)
            artifact_id = match.group(2)
            url = (
                "https://repo1.maven.org/maven2/"
                f"{group_id.replace('.', '/')}/{artifact_id}/"
            )

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
        if not url:
            raise AnityaPluginException(
                "Artifact needs to be in format groupId:artifactId"
            )

        return get_versions_by_regex(url, VERSION_REGEX, project)

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        valid_domains = (
            "repo1.maven.org",
            "repo.maven.apache.org",
            "search.maven.org",
            "central.sonatype.com",
            "repo.maven.org",
        )
        return any(domain in url for domain in valid_domains)

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.

        Raises:
            AnityaPluginException: If URL cannot be parsed into valid Maven coordinates.
        """
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        group_id = None
        artifact_id = None

        if "artifact/" in path:
            sub = path.split("artifact/", 1)[1]
            parts = [p for p in sub.split("/") if p]
            if len(parts) >= 2:
                group_id = parts[0]
                artifact_id = parts[1]
        elif "maven2/" in path:
            sub = path.split("maven2/", 1)[1]
            parts = [p for p in sub.split("/") if p]
            file_exts = (
                ".xml",
                ".jar",
                ".pom",
                ".war",
                ".sha1",
                ".md5",
                ".asc",
            )
            if parts and any(parts[-1].endswith(ext) for ext in file_exts):
                parts = parts[:-1]
            if parts and re.match(r"^\d", parts[-1]):
                parts = parts[:-1]
            if len(parts) >= 2:
                group_id = ".".join(parts[:-1])
                artifact_id = parts[-1]
        elif parsed.query:
            query = unquote(parsed.query)
            g_match = re.search(r"g:[\"'\s]*([\w.\-]+)", query)
            a_match = re.search(r"a:[\"'\s]*([\w.\-]+)", query)
            if g_match and a_match:
                group_id = g_match.group(1).strip("\"'")
                artifact_id = a_match.group(1).strip("\"'")

        if not group_id or not artifact_id:
            raise AnityaPluginException(
                f"Could not extract Maven coordinates from {url}"
            )

        name = artifact_id
        version_url = f"{group_id}:{artifact_id}"
        group_path = group_id.replace(".", "/")
        homepage = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/"
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
