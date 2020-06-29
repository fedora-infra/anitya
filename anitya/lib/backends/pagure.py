# -*- coding: utf-8 -*-

"""
 (c) 2015-2020 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Michal Konecny <mkonecny@redhat.com>

"""


from __future__ import print_function
from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class PagureBackend(BaseBackend):
    """ The pagure class for project hosted on pagure.io. """

    name = "pagure"
    examples = ["https://pagure.io/pagure", "https://pagure.io/flask-multistatic"]

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
        versions = cls.get_ordered_versions(project)
        if versions:
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
        url = "https://pagure.io/api/0/%s/git/tags" % project.name

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
        except Exception as err:  # pragma: no cover
            raise AnityaPluginException("Could not contact %s: %s" % (url, str(err)))

        # Not modified
        if req.status_code == 304:
            return []

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException("No JSON returned by %s" % url)

        # Filter retrieved versions
        filtered_versions = cls.filter_versions(
            data.get("tags", []), project.version_filter
        )

        return filtered_versions
