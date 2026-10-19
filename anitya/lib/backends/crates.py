# -*- coding: utf-8 -*-
# This file is a part of the Anitya project.
#
# Copyright © 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org>
# Copyright © 2020 Michal Konecny <mkonecny@redhat.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""
A backend for the Rust community’s crate host, `crates.io <https://crates.io/>`_.

This backend makes use of Cargo’s official sparse registry index
(`index.crates.io <https://index.crates.io/>`_) per RFC 2789 and the crates.io
Data Access Policy. The sparse index is hosted on a CDN without API rate limits.
Files contain newline-delimited JSON (NDJSON) metadata for all versions of a crate.

For example, ``https://index.crates.io/it/oa/itoa`` returns lines like::

    {"name":"itoa","vers":"0.2.1","deps":[],"cksum":"...","features":{},"yanked":false}
"""

import json

import arrow
import requests

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException, RateLimitException


class CratesBackend(BaseBackend):
    """The crates class for projects hosted on crates.io."""

    name = "crates.io"
    examples = ["https://crates.io/crates/clap", "https://crates.io/crates/serde"]

    @classmethod
    def _get_versions(cls, project):
        """
        Make a request for all versions of the project provided.

        Args:
            project (anitya.lib.anitya.db.models.Project): The Rust project to retrieve
                versions for.

        Returns:
            list: A list of version dictionaries ordered from newest to oldest.

        Raises:
            RateLimitException: If crates.io returns a 429 response.
            AnityaPluginException: If the URL was unreachable or the response
                was in an unexpected format.
        """
        url = cls.get_version_url(project)
        last_change = project.get_time_last_created_version()
        try:
            req = cls.call_url(url, last_change=last_change)
            if req.status_code == 429:
                retry_after = req.headers.get("Retry-After")
                if retry_after:
                    if retry_after.isdigit():
                        reset_time = arrow.now("UTC").shift(seconds=int(retry_after))
                    else:
                        try:
                            reset_time = arrow.get(retry_after)
                        except Exception:
                            reset_time = arrow.now("UTC").shift(hours=1)
                else:
                    reset_time = arrow.now("UTC").shift(hours=1)
                raise RateLimitException(reset_time.isoformat())
            req.raise_for_status()
            # Not modified
            if req.status_code == 304:
                return []
            versions = [
                json.loads(line) for line in req.text.splitlines() if line.strip()
            ]
        except RateLimitException:
            raise
        except requests.RequestException as e:
            raise AnityaPluginException(f"Could not contact {url}: {e!r}") from e
        except (ValueError, json.JSONDecodeError) as e:
            raise AnityaPluginException(f"Failed to decode JSON: {e!r}") from e

        return list(reversed(versions))

    @classmethod
    def get_version(cls, project):
        """
        Get the latest version of the project provided.

        Args:
            project (anitya.lib.anitya.db.models.Project): The Rust project to retrieve
                the latest version for.

        Returns:
            str: A version string.

        Raises:
            AnityaPluginException: If the URL was unreachable or the response
                was in an unexpected format.
        """
        versions = cls.get_versions(project)
        if not versions:
            raise AnityaPluginException(f"{project.name}: no versions found.")
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
        name = project.name.strip().lower()
        if len(name) == 1:
            prefix = "1"
        elif len(name) == 2:
            prefix = "2"
        elif len(name) == 3:
            prefix = f"3/{name[0]}"
        else:
            prefix = f"{name[:2]}/{name[2:4]}"

        return f"https://index.crates.io/{prefix}/{name}"

    @classmethod
    def get_versions(cls, project):
        """
        Get all versions of the project provided.

        Args:
            project (anitya.lib.anitya.db.models.Project): The Rust project to retrieve
                versions for.

        Returns:
            list: A list of version strings.

        Raises:
            AnityaPluginException: If the URL was unreachable or the response
                was in an unexpected format.
        """
        filtered_versions = cls.filter_versions(
            [
                v["vers"]
                for v in cls._get_versions(project)
                if not v.get("yanked", False)
            ],
            project.version_filter,
        )
        return filtered_versions

    @classmethod
    def get_ordered_versions(cls, project):
        """
        Get all versions of the project provided, ordered from newest to oldest.

        Args:
            project (anitya.lib.anitya.db.models.Project): The Rust project to retrieve
                versions for.

        Returns:
            list: A list of version strings.

        Raises:
            AnityaPluginException: If the URL was unreachable or the response
                was in an unexpected format.
        """
        # crates API returns already ordered versions
        return cls.get_versions(project)

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
