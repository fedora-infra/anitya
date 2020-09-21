# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Michael Simacek <msimacek@redhat.com>

"""

import re

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


VERSION_REGEX = re.compile(r"\<a[^>]+\>(\d[^</]*)")
MAVEN_HOMEPAGE_RE = re.compile(r"https?://repo\d+.maven.org/")
# Maven artifact coordinates in format artifactId:groupId
COORDINATES_RE = re.compile(r"([^:]+):([^:]+)")


class MavenBackend(BaseBackend):
    """ Backend for projects hosted on Maven Central """

    name = "Maven Central"
    examples = [
        "https://repo1.maven.org/maven2/plexus/plexus-compiler/",
        "https://repo1.maven.org/maven2/com/google/inject/guice/",
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

        return cls.get_ordered_versions(project)[-1]

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
            url = "https://repo1.maven.org/maven2/{group_id}/{artifact_id}/".format(
                group_id=group_id.replace(".", "/"), artifact_id=artifact_id
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
                "Aritfact needs to be in format groupId:artifactId"
            )

        return get_versions_by_regex(url, VERSION_REGEX, project)
