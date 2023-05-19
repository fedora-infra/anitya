# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""


from anitya.lib.backends import REGEX, BaseBackend, get_versions_by_regex


class HackageBackend(BaseBackend):
    """The custom class for projects hosted on hackage.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "Hackage"
    examples = [
        "https://hackage.haskell.org/package/Hs2lib",
        "https://hackage.haskell.org/package/Biobase",
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
        url = "https://hackage.haskell.org/package/%(name)s" % {"name": project.name}

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

        regex = REGEX % {"name": project.name}

        return get_versions_by_regex(url, regex, project)

    @classmethod
    def check_feed(cls):
        # See https://hackage.haskell.org/api#recentPackages
        # It should be possible to query this, but I can't figure out how to
        # get it to give me non-html.
        # url = 'https://hackage.haskell.org/packages/recent/revisions'
        raise NotImplementedError()
