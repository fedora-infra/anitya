# -*- coding: utf-8 -*-

"""
(c) 2015-2016 - Copyright Vivek Anand

Authors:
  Vivek Anand <vivekanand1101@gmail.com>

"""

import requests

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class BitBucketBackend(BaseBackend):
    """The custom class for projects hosted on bitbucket.org

    This backend retrieves version information using the Bitbucket API.
    """

    name = "BitBucket"
    examples = [
        "https://bitbucket.org/zzzeek/sqlalchemy",
        "https://bitbucket.org/cherrypy/cherrypy",
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
        url = ""
        if project.version_url:
            url = project.version_url.replace("https://bitbucket.org/", "")
        elif project.homepage and project.homepage.startswith("https://bitbucket.org/"):
            url = project.homepage.replace("https://bitbucket.org/", "")

        # Clean up trailing slashes
        if url.endswith("/"):
            url = url[:-1]

        # Ensure we only keep the 'owner/repo' part by stripping extra paths
        # in case a user pasted a link like bitbucket.org/owner/repo/downloads
        if "/downloads" in url:
            url = url.split("/downloads")[0]
        if "/src" in url:
            url = url.split("/src")[0]

        if url:
            # Use the official Bitbucket REST API v2.0 endpoint for tags
            url = f"https://api.bitbucket.org/2.0/repositories/{url}/refs/tags?sort=-target.date"

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
                f"Project {project.name} was incorrectly set up."
            )

        try:
            # Fetch data from the Bitbucket API
            req = requests.get(url, timeout=15)
            req.raise_for_status()
            data = req.json()

            versions = []
            # Bitbucket API returns a paginated list inside the "values" key
            if "values" in data:
                for tag in data["values"]:
                    if "name" in tag:
                        versions.append(tag["name"])

            return versions

        except Exception as e:
            raise AnityaPluginException(
                f"Could not retrieve versions from Bitbucket API: {e}"
            )

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
