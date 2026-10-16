# -*- coding: utf-8 -*-
#
# Copyright © 2023 Erol Keskin <erolkeskin.dev@gmail.com>
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
"""gitea"""

from anitya.lib import utilities
from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class GiteaBackend(BaseBackend):
    """The custom class for projects hosted on gitea

    This backend can also be used for projects that are
    hosted on forgejo since forgejo is one-to-one compatible
    with gitea api.
    """

    name = "Gitea"
    examples = [
        "https://codeberg.org/freedroid/freedroid-src.git",
        "https://codeberg.org/forgejo/forgejo",
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
        url_template = "%(host)s/api/v1/repos/%(owner)s/%(repo)s/%(releases_or_tags)s"
        repo_url = ""

        if project.version_url:
            repo_url = project.version_url
        elif project.homepage:
            repo_url = project.homepage

        tokens = utilities.remove_suffix(repo_url.rstrip("/"), ".git").split("/")
        url = ""
        if len(tokens) == 5:
            url = url_template % {
                "host": tokens[0] + "//" + tokens[2],
                "owner": tokens[3],
                "repo": tokens[4],
                "releases_or_tags": "releases" if project.releases_only else "tags",
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

        resp = cls.call_url(url)

        if resp.status_code == 200:
            json = resp.json()
        else:
            raise AnityaPluginException(
                f"{project.name}: Server responded with status "
                f'"{resp.status_code}": "{resp.reason}"'
            )

        versions = [version["name"] for version in json]
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
        return url.startswith("https://codeberg.org")

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.
        """
        homepage = url
        version_url = url
        name = url.rstrip("/").rstrip(".git").split("/")[-1]
        version_scheme = "RPM"
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
