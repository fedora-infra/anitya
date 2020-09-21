# -*- coding: utf-8 -*-

"""
 (c) 2015-2016 - Copyright Vivek Anand

 Authors:
   Vivek Anand <vivekanand1101@gmail.com>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


REGEX = 'class="name">([^<]*[^tip])</td'


class BitBucketBackend(BaseBackend):
    """The custom class for projects hosted on bitbucket.org

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "BitBucket"
    examples = [
        "https://bitbucket.org/zzzeek/sqlalchemy",
        "https://bitbucket.org/cherrypy/cherrypy",
    ]

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
        url_template = "https://bitbucket.org/%(version_url)s/" "downloads?tab=tags"
        url = ""
        if project.version_url:
            url = project.version_url.replace("https://bitbucket.org/", "")
        elif project.homepage.startswith("https://bitbucket.org"):
            url = project.homepage.replace("https://bitbucket.org/", "")

        if url.endswith("/"):
            url = url[:-1]

        if url:
            url = url_template % {"version_url": url}

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
                "Project %s was incorrectly set up." % project.name
            )

        return get_versions_by_regex(url, REGEX, project)
