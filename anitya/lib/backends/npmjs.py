# -*- coding: utf-8 -*-

"""
(c) 2014-2020 - Copyright Red Hat Inc

Authors:
  Pierre-Yves Chibon <pingou@pingoured.fr>
  Ralph Bean <rbean@redhat.com>

"""

import logging
from urllib.parse import quote

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException

_log = logging.getLogger(__name__)


class NpmjsBackend(BaseBackend):
    """The backend class for projects hosted on npmjs.com."""

    name = "npmjs"
    default_version_scheme = "Semantic"
    examples = [
        "https://www.npmjs.com/package/request",
        "https://www.npmjs.com/package/colors",
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

        if "dist-tags" in data and "latest" in data["dist-tags"]:
            return data["dist-tags"]["latest"]
        else:
            versions = cls.get_ordered_versions(project)
            if not versions:
                return None
            return versions[-1]

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
        encoded_name = quote(project.name, safe="@")
        return f"https://registry.npmjs.org/{encoded_name}"

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

        if "error" in data or "versions" not in data:
            raise AnityaPluginException(f"No versions found at {url}")

        # Filter retrieved versions
        filtered_versions = BaseBackend.filter_versions(
            list(data["versions"].keys()), project.version_filter
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
        return "npmjs.com" in url or "npmjs.org" in url

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
        path = clean_url.split("/package/")[-1]
        parts = path.split("/")
        if parts[0].startswith("@") and len(parts) >= 2:
            name = f"{parts[0]}/{parts[1]}"
        else:
            name = parts[0]
        homepage = f"https://www.npmjs.com/package/{name}"
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
        """Return a generator over the latest 40 uploads to npmjs.com

        by querying an weird JSON endpoint.
        """

        url = (
            "https://skimdb.npmjs.com/registry/_changes?"
            "feed=normal"
            "&descending=true"
            "&limit=40"
            "&include_docs=true"
            "&attachments=false"
        )

        try:
            response = cls.call_url(url)
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from err

        if response.status_code != 200:
            raise AnityaPluginException(
                f"Failed to download from {url}: {response.status_code} "
                f"{response.reason}"
            )

        try:
            data = response.json()
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException(f"No JSON returned by {url}") from err

        if not isinstance(data, dict):
            _log.warning("Unexpected response format from %s: expected dict", url)
            return

        results = data.get("results")
        if not isinstance(results, list):
            _log.warning(
                "Unexpected response format from %s: missing results list", url
            )
            return

        for item in results:
            if not isinstance(item, dict) or item.get("deleted"):
                continue
            doc = item.get("doc")
            if not isinstance(doc, dict):
                continue
            name = doc.get("name")
            if not name:
                continue
            homepage = doc.get("homepage") or f"https://npmjs.org/package/{name}"
            versions = doc.get("versions") or []
            for version in versions:
                yield name, homepage, cls.name, version
