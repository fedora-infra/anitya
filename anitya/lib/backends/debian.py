# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex

# Debian packagers upload the original source tarball in the format
# <name>_<version>.orig.<compression format>. So, for example,
# reprepro_4.13.1.orig.tar.gz.
DEBIAN_REGEX = (
    r"(?i)%(name)s(?:[-_]?(?:minsrc|src|source))?[-_]([^-/_\s]+?)(?:[-_]"
    r"(?:minsrc|src|source|asc))?\.(?:orig\.)?(?:tar|t[bglx]z|tbz2|zip)"
)


class DebianBackend(BaseBackend):
    """The custom class for projects hosted on ftp.debian.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "Debian project"
    examples = [
        "http://ftp.debian.org/debian/pool/main/q/qpdf/",
        "http://ftp.debian.org/debian/pool/main/g/guake/",
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

        if project.name.startswith("lib"):
            short = project.name[:4]
        else:
            short = project.name[0]

        return f"http://ftp.debian.org/debian/pool/main/{short}/{project.name}/"

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
        regex = DEBIAN_REGEX % {"name": project.name}

        return get_versions_by_regex(url, regex, project)

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
