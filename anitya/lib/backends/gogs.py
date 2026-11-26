# -*- coding: utf-8 -*-
#
# Copyright © 2022 Erol Keskin <erolkeskin.dev@gmail.com>
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
"""Backend for projects hosted on Gogs instances."""

from urllib.parse import urlparse

from anitya.lib import utilities
from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException

REGEX = '<i class="tag icon"></i> (.*)</a>'


class GogsBackend(BaseBackend):
    """Backend for projects hosted on Gogs instances (e.g. notabug.org)."""

    name = "Gogs"
    default_version_scheme = "RPM"
    is_repo = True
    multi_host = True
    examples = [
        "https://notabug.org/libreboot/lbmk",
        "https://notabug.org/osboot/osbmk",
    ]

    @classmethod
    def get_version_url(cls, project):
        """Method called to retrieve the url used to check for new version
        of the project provided, project that relies on the backend of this plugin.

        Args:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            str: url used for version checking
        """
        url_template = "%(host)s/%(owner)s/%(repo)s/releases"
        tokens = []
        url = ""

        if project.version_url:
            tokens = project.version_url.rstrip("/").split("/")
        elif project.homepage:
            tokens = project.homepage.rstrip("/").split("/")

        if len(tokens) >= 5:
            url = url_template % {
                "host": tokens[0] + "//" + tokens[2],
                "owner": tokens[3],
                "repo": "/".join(tokens[4:]),
            }

        return url

    @classmethod
    def get_versions(cls, project):
        """Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        Args:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                    corresponds to the current plugin.

        Returns:
            str: a list of all the possible releases found
        """
        url = cls.get_version_url(project)
        if not url:
            raise AnityaPluginException(
                f"Project {project.name} was incorrectly set up"
            )

        return get_versions_by_regex(url, REGEX, project, url.startswith("http://"))

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        return "notabug.org" in url

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.

        Raises:
            AnityaPluginException: If URL cannot be parsed into a valid project.
        """
        orig_url = url
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        host = parsed.netloc or "notabug.org"

        for subpath in (
            "/releases",
            "/src",
            "/commits",
            "/branches",
            "/issues",
            "/pulls",
            "/archive",
            "/raw",
            "/wiki",
            "/activity",
            "/forks",
            "/stars",
            "/watchers",
        ):
            if subpath in path:
                path = path.split(subpath)[0].rstrip("/")

        path = utilities.remove_suffix(path.rstrip("/"), ".git")
        parts = [p for p in path.split("/") if p]
        if len(parts) < 2:
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        owner = parts[0]
        repo = parts[1]
        name = repo
        homepage = f"https://{host}/{owner}/{repo}"
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
