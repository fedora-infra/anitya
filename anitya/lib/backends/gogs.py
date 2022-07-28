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

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


REGEX = '<i class="tag icon"></i> (.*)</a>'


class GogsBackend(BaseBackend):
    """The custom class for projects hosted on gogs

    This backend allows to specify a version_url that will
    be used to retrieve the version information.
    """

    name = "Gogs"
    examples = [
        "https://notabug.org/libreboot/lbmk",
        "https://notabug.org/osboot/osbmk",
    ]

    @classmethod
    def get_version(cls, project):
        """Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        Args:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                    corresponds to the current plugin.

        Returns:
            str: latest version found on the upstream
        """
        return cls.get_ordered_versions(project)[-1]

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
                "Project %s was incorrectly set up" % project.name
            )

        return get_versions_by_regex(url, REGEX, project, url.startswith("http://"))
