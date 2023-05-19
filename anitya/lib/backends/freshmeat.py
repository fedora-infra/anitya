# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex

REGEX = '<a href="/projects/[^/]*/releases/[0-9]*">([^<]*)</a>'


class FreshmeatBackend(BaseBackend):
    """The custom class for projects hosted on freshmeat.net.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "Freshmeat"
    examples = [
        "http://freecode.com/projects/atmail",
        "http://freecode.com/projects/awstats",
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
        url_template = "http://freshmeat.net/projects/%(name)s"

        url = url_template % {"name": project.name}

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

        return get_versions_by_regex(url, REGEX, project)
