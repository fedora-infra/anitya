# -*- coding: utf-8 -*-

"""
 (c) 2014-2020 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Michal Konecny <mkonecny@redhat.com>

"""


from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class PackagistBackend(BaseBackend):
    """The custom class for projects hosted on packagist.org.

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
    def get_version_url(cls, project):
        """Method called to retrieve the url used to check for new version
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
                f"Project {project.name} is not correctly set up."
            )

        last_change = project.get_time_last_created_version()
        try:
            req = cls.call_url(url, last_change=last_change)
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"Could not contact {url}") from exc

        # Not modified
        if req.status_code == 304:
            return []

        try:
            data = req.json()
        except Exception as exc:  # pragma: no cover
            raise AnityaPluginException(f"No JSON returned by {url}") from exc

        if "package" in data and "versions" in data["package"]:
            # Filter retrieved versions
            filtered_versions = cls.filter_versions(
                sorted(data["package"]["versions"].keys()), project.version_filter
            )

            return filtered_versions
        elif "status" in data and data["status"] == "error" and "message" in data:
            raise AnityaPluginException(data["message"])
        else:
            raise AnityaPluginException(f"Invalid JSON returned by {url}")

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
