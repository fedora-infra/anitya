# -*- coding: utf-8 -*-

"""
 (c) 2014-2020 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Ralph Bean <rbean@redhat.com>
   Michal Konecny <mkonecny@redhat.com>

"""

from anitya.lib import xml2dict
from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class PypiBackend(BaseBackend):
    """The PyPI class for project hosted on PyPI."""

    name = "PyPI"
    examples = [
        "https://pypi.python.org/pypi/arrow",
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
        url = f"https://pypi.org/pypi/{project.name}/json"

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

        items = data["rss"]["channel"]["item"]
        for entry in items:
            title = entry["title"]["value"]
            name, version = title.rsplit(None, 1)
            homepage = f"https://pypi.org/project/{name}/"
            yield name, homepage, cls.name, version
