# -*- coding: utf-8 -*-

"""
 (c) 2014-2020 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Ralph Bean <rbean@redhat.com>
   Michal Konecny <mkonecny@redhat.com>

"""

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class RubygemsBackend(BaseBackend):
    """The custom class for projects hosted on rubygems.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information."""

    name = "Rubygems"
    examples = ["https://rubygems.org/gems/aa", "https://rubygems.org/gems/bio"]

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
        url = f"https://rubygems.org/api/v1/versions/{project.name}/latest.json"

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
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from exc

        # Not modified
        if req.status_code == 304:
            return []

        try:
            data = req.json()
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"No JSON returned by {url}") from exc

        if data["version"] == "unknown":
            raise AnityaPluginException(
                f"Project or version unknown at {url}"
            )  # pragma: no cover

        # Filter retrieved versions
        filtered_versions = cls.filter_versions(
            [data["version"]], project.version_filter
        )
        return filtered_versions

    @classmethod
    def check_feed(cls):
        """Return a generator over the latest 50 uploads to rubygems.org

        by querying the JSON API.
        """

        url = "https://rubygems.org/api/v1/activity/just_updated.json"

        try:
            response = cls.call_url(url)
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from exc

        try:
            data = response.json()
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"No XML returned by {url}") from exc

        for item in data:
            name, version = item["name"], item["version"]
            homepage = f"https://rubygems.org/gems/{name}"
            yield name, homepage, cls.name, version
