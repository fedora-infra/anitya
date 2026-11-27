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
"""sourcehut"""

from defusedxml import ElementTree

from anitya.lib import utilities
from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class SourceHutBackend(BaseBackend):
    """The custom class for projects hosted on SourceHut

    This backend allows to specify homepage or owner/name of the repository.
    """

    name = "SourceHut"
    default_version_scheme = "RPM"
    is_repo = True
    examples = ["https://git.sr.ht/~sircmpwn/scdoc", "https://git.sr.ht/~sircmpwn/hare"]

    @classmethod
    def _clean_repo(cls, raw: str) -> str:
        """Extract owner/repo from a raw repository path or URL."""
        if not raw:
            return ""
        clean = raw.split("?")[0].split("#")[0].strip("/")
        for prefix in (
            "https://git.sr.ht/~",
            "http://git.sr.ht/~",
            "https://www.git.sr.ht/~",
            "http://www.git.sr.ht/~",
            "git.sr.ht/~",
            "www.git.sr.ht/~",
            "~",
        ):
            if clean.startswith(prefix):
                clean = clean[len(prefix) :].strip("/")
                break
        else:
            if "://" in clean:
                return ""

        parts = [p for p in clean.split("/") if p]
        if len(parts) >= 2:
            owner = parts[0]
            repo = utilities.remove_suffix(parts[1], ".git")
            if owner and repo:
                return f"{owner}/{repo}"
        return ""

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
        raw = project.version_url or project.homepage or ""
        repo = cls._clean_repo(raw)

        if repo:
            url_template = "https://git.sr.ht/~%(repo)s/refs/rss.xml"
            return url_template % {"repo": repo}

        return ""

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

        last_change = project.get_time_last_created_version()
        res = cls.call_url(url, last_change)
        if res.status_code == 200:
            xml = ElementTree.fromstring(res.text)
        elif res.status_code == 304:
            return []
        else:
            raise AnityaPluginException(
                f"{project.name}: Server responded with status "
                f'"{res.status_code}": "{res.reason}"'
            )

        channel = xml.find("channel")
        if channel is None:
            raise AnityaPluginException(
                f"{project.name}: No channel found in RSS feed. '{url}'"
            )

        versions = []
        for item in channel.findall("item"):
            title = item.find("title")
            if title is not None and title.text and title.text.strip():
                versions.append(title.text.strip())

        if len(versions) == 0:
            raise AnityaPluginException(
                f"{project.name}: no upstream version found. '{url}'"
            )

        return cls.filter_versions(versions, project.version_filter)

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        return url.startswith(
            (
                "https://git.sr.ht/~",
                "http://git.sr.ht/~",
                "https://www.git.sr.ht/~",
                "http://www.git.sr.ht/~",
            )
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
        if not cls.is_url_valid(url):
            raise AnityaPluginException(f"Could not extract project name from {url}")

        repo_path = cls._clean_repo(url)
        if not repo_path:
            raise AnityaPluginException(f"Could not extract project name from {url}")

        owner, repo = repo_path.split("/")
        version_url = repo_path
        name = repo
        homepage = f"https://git.sr.ht/~{version_url}"
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
