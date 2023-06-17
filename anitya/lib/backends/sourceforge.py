# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import REGEX, BaseBackend, get_versions_by_regex


class SourceforgeBackend(BaseBackend):
    """The custom class for projects hosted on sourceforge.net.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "Sourceforge"
    examples = [
        "https://sourceforge.net/projects/filezilla/",
        "https://sourceforge.net/projects/file-folder-ren/",
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
        url_template = "https://sourceforge.net/projects/%(name)s/rss?limit=200"

        url = url_template % {
            "name": (project.version_url or project.name).replace("+", r"\+")
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
        regex = REGEX % {"name": project.name.replace("+", r"\+")}

        return get_versions_by_regex(url, regex, project)

    @classmethod
    def check_feed(cls):  # pragma: no cover
        """Method called to retrieve the latest uploads to a given backend,
        via, for example, RSS or an API.

        Not all backends may support this.  It can be used to look for updates
        much more quickly than scanning all known projects.

        Returns:
            :obj:`list`: A list of 4-tuples, containing the project name, homepage, the
            backend, and the version.

        Raises:
            AnityaPluginException: A
                :obj:`anitya.lib.exceptions.AnityaPluginException` exception
                when the versions cannot be retrieved correctly
            NotImplementedError: If backend does not
                support batch updates.

        """
        raise NotImplementedError()
