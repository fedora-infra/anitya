# -*- coding: utf-8 -*-
#
# Copyright © 2018-2020  Red Hat, Inc.
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
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#
"""
 Authors:
   Michal Konecny <mkonecny@redhat.com>

"""

import logging

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException

_log = logging.getLogger(__name__)


class GitlabBackend(BaseBackend):
    """The custom class for projects hosted on gitlab.

    This backend allows to specify a version_url and owner, name of the repository.
    """

    name = "GitLab"
    examples = [
        "https://gitlab.gnome.org/GNOME/gnome-video-arcade",
        "https://gitlab.com/xonotic/xonotic",
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
        tokens = []
        url = ""
        url_template = (
            "%(hostname)s/api/v4/projects/%(owner)s%%2F%(repo)s/repository/tags"
        )
        if project.version_url:
            tokens = project.version_url.split("/")
        elif project.homepage:
            tokens = project.homepage.split("/")

        if len(tokens) >= 5:
            url = url_template % {
                "hostname": tokens[0] + "//" + tokens[2],
                "owner": tokens[3],
                "repo": "%2F".join(tokens[4:]),  # any subgroups & repo
            }

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

        last_change = project.get_time_last_created_version()
        resp = cls.call_url(url, last_change=last_change)

        if resp.status_code == 200:
            json = resp.json()
        else:
            # Not modified
            if resp.status_code == 304:
                return []
            raise AnityaPluginException(
                f"{project.name}: Server responded with status "
                f'"{resp.status_code}": "{resp.reason}"'
            )

        _log.debug("Received %s tags for %s", len(json), project.name)

        tags = []
        for tag in json:
            tags.append(tag["name"])

        if len(tags) == 0:
            raise AnityaPluginException(f"{project.name}: No upstream version found.")

        # Filter retrieved versions
        filtered_versions = cls.filter_versions(tags, project.version_filter)
        return filtered_versions

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
