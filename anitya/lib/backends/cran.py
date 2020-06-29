# -*- coding: utf-8 -*-
# This file is part of the Anitya project.
# Copyright (C) 2018 Elliott Sales de Andrade <quantum.analyst@gmail.com>
# Copyright (C) 2020 Michal Konecny <mkonecny@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""
A backend for the R package host, `CRAN <https://cran.r-project.org/>`_.

CRAN does not provide a specific API, so this uses the `MetaCRAN <https://www.r-pkg.org/>`_
JSON API instead:

  * An HTTP GET request to ``https://crandb.r-pkg.org/{name}`` returns information about the `latest
    version of the package <https://github.com/metacran/crandb#pkg-latest-version-of-a-package>`_.
    We read the ``Version`` key from this response.
  * An HTTP GET request to ``https://crandb.r-pkg.org/{name}/all`` returns information about `all
    versions <https://github.com/metacran/crandb#pkgall-all-versions-of-a-package>`_. The
    ``versions`` key in the response contains a dictionary keyed by version and with values
    corresponding to the previous request above.
  * An HTTP GET request to ``https://crandb.r-pkg.org/-/pkgreleases?descending=true&limit=50``
    returns information on `all package releases
    <https://github.com/metacran/crandb#-pkgreleases-package-releases>`_, in order of release.
    The response is a list of dictionaries with the ``package`` key containing the same results as
    the first request above.
"""

import json

import requests

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class CranBackend(BaseBackend):
    """The custom class for projects hosted on CRAN."""

    name = "CRAN (R)"
    examples = [
        "https://cran.r-project.org/web/packages/tidyverse/",
        "https://cran.r-project.org/web/packages/devtools/",
    ]

    @classmethod
    def get_version(cls, project):
        """
        Retrieve the latest version of the provided project from this backend.

        Args:
            project (anitya.db.models.Project): The CRAN project to retrieve the version for.

        Returns:
            str: The latest version found upstream.

        Raises:
            AnityaPluginException: If the URL was unreachable or the response was in an unexpected
                format.

        """
        url = "https://crandb.r-pkg.org/{name}".format(name=project.name)

        last_change = project.get_time_last_created_version()
        try:
            response = cls.call_url(url, last_change=last_change)
        except requests.RequestException as e:  # pragma: no cover
            raise AnityaPluginException("Could not contact {}: {}".format(url, str(e)))

        if response.status_code != 200:
            # Not modified
            if response.status_code == 304:
                return None
            raise AnityaPluginException(
                "Failed to download from {}: {} {}".format(
                    url, response.status_code, response.reason
                )
            )

        try:
            data = response.json()
        except json.JSONDecodeError:  # pragma: no cover
            raise AnityaPluginException("No JSON returned by {}".format(url))

        if "error" in data or "Version" not in data:  # pragma: no cover
            raise AnityaPluginException("No versions found at {}".format(url))

        return data["Version"]

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
        url = "https://crandb.r-pkg.org/{name}/all".format(name=project.name)

        return url

    @classmethod
    def get_versions(cls, project):
        """
        Retrieve all the versions (that can be found) of the provided project from this backend.

        Args:
            project (anitya.db.models.Project): The project to retrieve the versions for.

        Returns:
            List[str]: All the possible versions found.

        Raises:
            AnityaPluginException: If the URL was unreachable or the response was in an unexpected
                format.

        """
        url = cls.get_version_url(project)
        last_change = project.get_time_last_created_version()

        try:
            response = cls.call_url(url, last_change=last_change)
        except requests.RequestException as e:  # pragma: no cover
            raise AnityaPluginException("Could not contact {}: {}".format(url, str(e)))

        if response.status_code != 200:
            # Not modified
            if response.status_code == 304:
                return []
            raise AnityaPluginException(
                "Failed to download from {}: {} {}".format(
                    url, response.status_code, response.reason
                )
            )

        try:
            data = response.json()
        except json.JSONDecodeError:  # pragma: no cover
            raise AnityaPluginException("No JSON returned by {}".format(url))

        if "error" in data or "versions" not in data:  # pragma: no cover
            raise AnityaPluginException("No versions found at {}".format(url))

        filtered_versions = cls.filter_versions(
            list(data["versions"].keys()), project.version_filter
        )
        return filtered_versions

    @classmethod
    def check_feed(cls):
        """
        Query the MetaCRAN JSON API for the latest 50 uploads to CRAN.

        Yields:
            Tuple[str, str, str, str]: Tuple of:

                * The name of the project.
                * The homepage of the project.
                * This backend's name.
                * The version of the project.

        Raises:
            AnityaPluginException: If the URL was unreachable or the response was in an unexpected
                format.
        """

        url = "https://crandb.r-pkg.org/-/pkgreleases?descending=true&limit=50"

        try:
            response = cls.call_url(url)
        except requests.RequestException as e:  # pragma: no cover
            raise AnityaPluginException("Could not contact {}: {}".format(url, str(e)))

        if response.status_code != 200:  # pragma: no cover
            raise AnityaPluginException(
                "Failed to download from {}: {} {}".format(
                    url, response.status_code, response.reason
                )
            )

        try:
            data = response.json()
        except json.JSONDecodeError:  # pragma: no cover
            raise AnityaPluginException("No JSON returned by {}".format(url))

        for item in data:
            name = item["name"]
            package = item["package"]
            homepage = package.get(
                "URL", "https://cran.r-project.org/web/packages/" + name
            )
            version = package["Version"]
            yield name, homepage, cls.name, version
