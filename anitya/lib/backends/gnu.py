# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, REGEX, get_versions_by_regex_for_text
from anitya.lib.exceptions import AnityaPluginException

import six


DEFAULT_REGEX = 'href="([0-9][0-9.]*)/"'


class GnuBackend(BaseBackend):
    """The custom class for project hosted on gnu.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "GNU project"
    examples = ["https://ftp.gnu.org/pub/gnu/gnash/"]

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
        return cls.get_ordered_versions(project)[-1]

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
        url = "https://ftp.gnu.org/gnu/%(name)s/" % {"name": project.name}

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
        last_change = project.get_time_last_created_version()

        try:
            req = cls.call_url(url, last_change=last_change)
        except Exception:  # pragma: no cover
            raise AnityaPluginException(
                'Could not call : "%s" of "%s"' % (url, project.name)
            )

        versions = []
        if not isinstance(req, six.string_types):
            # Not modified
            if req.status_code == 304:
                return versions

        try:
            regex = REGEX % {"name": project.name}
            versions = get_versions_by_regex_for_text(req.text, url, regex, project)
        except AnityaPluginException:
            versions = get_versions_by_regex_for_text(
                req.text, url, DEFAULT_REGEX, project
            )

        return versions
