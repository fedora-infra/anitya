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

"""
A backend for cgit
"""

from urllib.parse import urlparse

from sqlalchemy import func, or_

from anitya.lib import utilities
from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException

REGEX = r"<a href='.*'>(?:%(name)s-)?(.*)\.(?:tar|tar\.[bglx]z|tbz2|zip)</a>"


class CgitBackend(BaseBackend):
    """The custom class for projects hosted on Cgit

    This backend allows to specify a version_url that will
    be used to retrieve the version information.
    """

    name = "Cgit"
    default_version_scheme = "RPM"
    examples = [
        "https://git.savannah.gnu.org/cgit/gnuzilla.git",
        "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/",
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
        raw_url = project.version_url or project.homepage or ""
        clean_url = raw_url.split("?")[0].split("#")[0].rstrip("/")
        for subpath in (
            "/refs/tags",
            "/refs",
            "/tree",
            "/log",
            "/commit",
            "/summary",
            "/tag",
        ):
            if subpath in clean_url:
                clean_url = clean_url.split(subpath)[0].rstrip("/")

        if not clean_url:
            return ""

        return f"{clean_url}/refs/tags"

    @classmethod
    def check_duplicate(cls, session, project):
        """Check for duplicate Cgit projects by version_url or homepage."""
        target_url = project.version_url or project.homepage
        if not target_url:
            return None
        from anitya.db import models

        clean_url = target_url.strip().rstrip("/")
        return (
            cls._base_query(session, project)
            .filter(
                or_(
                    func.rtrim(models.Project.version_url, "/") == clean_url,
                    func.rtrim(models.Project.homepage, "/") == clean_url,
                ),
            )
            .first()
        )

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
        regex = REGEX % {"name": project.name.lower()}
        return get_versions_by_regex(url, regex, project, url.startswith("http://"))

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        # We need to exclude the SourceHut backend urls
        if "git.sr.ht/~" in url:
            return False
        return url.startswith(("https://git.", "http://git.")) or (
            not url.startswith(("http://", "https://")) and url.startswith("git.")
        )

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
        if not cls.is_url_valid(orig_url):
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        clean_url = url.split("?")[0].split("#")[0].rstrip("/")
        for subpath in (
            "/refs/tags",
            "/refs",
            "/tree",
            "/log",
            "/commit",
            "/summary",
            "/tag",
        ):
            if subpath in clean_url:
                clean_url = clean_url.split(subpath)[0].rstrip("/")

        parsed = urlparse(clean_url if "://" in clean_url else f"https://{clean_url}")
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if not path_parts:
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        name = utilities.remove_suffix(clean_url, ".git").split("/")[-1]
        if not name:
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        homepage = clean_url if clean_url != url.rstrip("/") else url
        version_url = clean_url if clean_url != url.rstrip("/") else url
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
