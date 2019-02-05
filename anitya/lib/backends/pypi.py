# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Ralph Bean <rbean@redhat.com>

"""

import anitya.lib.xml2dict as xml2dict

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class PypiBackend(BaseBackend):
    """ The PyPI class for project hosted on PyPI. """

    name = "PyPI"
    examples = [
        "https://pypi.python.org/pypi/arrow",
        "https://pypi.org/project/fedmsg/",
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
        url = cls.get_version_url(project)
        try:
            req = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException("Could not contact %s" % url)

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException("No JSON returned by %s" % url)

        return data["info"]["version"]

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
        url = "https://pypi.org/pypi/%s/json" % project.name

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
        try:
            req = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException("Could not contact %s" % url)

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException("No JSON returned by %s" % url)

        return list(data["releases"].keys())

    @classmethod
    def check_feed(cls):
        """ Return a generator over the latest 40 uploads to PyPI

        by querying an RSS feed.
        """

        url = "https://pypi.org/rss/updates.xml"

        try:
            response = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException("Could not contact %s" % url)

        try:
            parser = xml2dict.XML2Dict()
            data = parser.fromstring(response.text)
        except Exception:  # pragma: no cover
            raise AnityaPluginException("No XML returned by %s" % url)

        items = data["rss"]["channel"]["item"]
        for entry in items:
            title = entry["title"]["value"]
            name, version = title.rsplit(None, 1)
            homepage = "https://pypi.org/project/%s/" % name
            yield name, homepage, cls.name, version
