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

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class SourceHutBackend(BaseBackend):
    """The custom class for projects hosted on SourceHut

    This backend allows to specify homepage or owner/name of the repository.
    """

    name = "SourceHut"
    examples = ["https://git.sr.ht/~sircmpwn/scdoc", "https://git.sr.ht/~sircmpwn/hare"]

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
        url = ""
        if project.version_url:
            url = project.version_url
        elif project.homepage:
            url = project.homepage.replace("https://git.sr.ht/~", "")

        if url.endswith("/"):
            url = url[:-1]

        if url:
            url_template = "https://git.sr.ht/~%(repo)s/refs/rss.xml"
            url = url_template % {"repo": url}

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

        versions = [i.find("title").text for i in xml.find("channel").findall("item")]

        if len(versions) == 0:
            raise AnityaPluginException(
                f"{project.name}: no upstream version found. - {url} -  "
            )

        return cls.filter_versions(versions, project.version_filter)

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
