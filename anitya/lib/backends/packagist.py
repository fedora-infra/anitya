# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""


from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class PackagistBackend(BaseBackend):
    """ The custom class for projects hosted on packagist.org.

    This backend allows to specify a version_url that will be used to
    retrieve the version information.
    """

    name = "Packagist"
    examples = [
        "https://packagist.org/packages/phpunit/php-code-coverage",
        "https://packagist.org/packages/phpunit/php-timer",
        "https://packagist.org/packages/<owner or group>/<project-name>",
    ]

    @classmethod
    def get_version(cls, project):
        """ Method called to retrieve the latest version of the projects
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
        """ Method called to retrieve the url used to check for new version
        of the project provided, project that relies on the backend of this plugin.

        Attributes:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            str: url used for version checking
        """
        url = ""
        url_template = "https://packagist.org/packages/%(user)s/%(name)s.json"

        if project.version_url:
            url = url_template % {"name": project.name, "user": project.version_url}

        return url

    @classmethod
    def get_versions(cls, project):
        """ Method called to retrieve all the versions (that can be found)
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
                "Project {} is not correctly set-up.".format(project.name)
            )

        try:
            req = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException("Could not contact %s" % url)

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException("No JSON returned by %s" % url)

        if "package" in data and "versions" in data["package"]:
            return sorted(data["package"]["versions"].keys())
        elif "status" in data and data["status"] == "error" and "message" in data:
            raise AnityaPluginException(data["message"])
        else:
            raise AnityaPluginException("Invalid JSON returned by %s" % url)
