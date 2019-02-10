# -*- coding: utf-8 -*-
# This file is a part of the Anitya project.
#
# Copyright © 2014-2017 Pierre-Yves Chibon <pingou@pingoured.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""The Anitya backends API."""

import fnmatch
import logging
import re
import socket
from datetime import timedelta
# sre_constants contains re exceptions
import sre_constants
import urllib.request as urllib
from urllib.error import URLError

import pkg_resources
import requests

from anitya.config import config as anitya_config
from anitya.lib.exceptions import AnityaPluginException
from anitya.lib.versions import RpmVersion
import six

REGEX = anitya_config['DEFAULT_REGEX']

# Default headers for requests
REQUEST_HEADERS = {
    'User-Agent': 'Anitya %s at release-monitoring.org' %
    pkg_resources.get_distribution('anitya').version,
    'From': anitya_config.get('ADMIN_EMAIL'),
    }

_log = logging.getLogger(__name__)


# Use a common http session, so we don't have to go re-establishing https
# connections over and over and over again.
http_session = requests.session()


class BaseBackend(object):
    '''
    The base class that all the different backends should extend.

    Attributes:
        name (str): The backend name. This is displayed to the user and used in
            URLs.
        examples (list): A list of strings that are displayed to the user to
            indicate example project URLs.
        default_regex (str): A regular expression to use by default with the
            backend.
        more_info (str): A string that provides more detailed information to
            the user about the backend.
        default_version_scheme (str): The default version scheme for this
            backend. This is only used if both the project and the ecosystem
            the project is a part of do not define a default version scheme.
            If this is not defined, :data:`anitya.lib.versions.GLOBAL_DEFAULT`
            is used.
        check_interval (`datetime.timedelta`): Interval which is used for periodic
            checking for new versions. This could be overriden by backend plugin.
    '''

    name = None
    examples = None
    default_regex = None
    more_info = None
    default_version_scheme = None
    check_interval = timedelta(hours=1)

    @classmethod
    def expand_subdirs(self, url, glob_char="*"):
        ''' Expand dirs containing ``glob_char`` in the given URL with the latest
        Example URL: ``https://www.example.com/foo/*/``

        The globbing char can be bundled with other characters enclosed within
        the same slashes in the URL like ``/rel*/``.

        Code originally from Till Maas as part of
        `cnucnu <https://fedorapeople.org/cgit/till/public_git/cnucnu.git/>`_

        '''
        glob_pattern = "/([^/]*%s[^/]*)/" % re.escape(glob_char)
        glob_match = re.search(glob_pattern, url)
        if not glob_match:
            return url
        glob_str = glob_match.group(1)

        # url until first slash before glob_match
        url_prefix = url[0:glob_match.start() + 1]

        # everything after the slash after glob_match
        url_suffix = url[glob_match.end():]

        html_regex = re.compile(r'\bhref\s*=\s*["\']([^"\'/]+)/["\']', re.I)
        text_regex = re.compile(r'^d.+\s(\S+)\s*$', re.I | re.M)

        if url_prefix != "":
            resp = self.call_url(url_prefix)
            # When FTP server is called, Response object is not created
            # and we get binary string instead
            try:
                dir_listing = resp.text
            except AttributeError:
                dir_listing = resp
            if not dir_listing:
                return url
            subdirs = []
            regex = url.startswith("ftp://") and text_regex or html_regex
            for match in regex.finditer(dir_listing):
                subdir = match.group(1)
                if subdir not in (".", "..") \
                        and fnmatch.fnmatch(subdir, glob_str):
                    subdirs.append(subdir)
            if not subdirs:
                return url
            sorted_subdirs = sorted([RpmVersion(s) for s in subdirs])
            latest = sorted_subdirs[-1].version

            url = "%s%s/%s" % (url_prefix, latest, url_suffix)
            return self.expand_subdirs(url, glob_char)
        return url

    @classmethod
    def get_version(self, project):  # pragma: no cover
        ''' Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        Attributes:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            str: Latest version found upstream

        Raises:
            AnityaPluginException: A
                :obj:`anitya.lib.exceptions.AnityaPluginException` exception
                when the versions cannot be retrieved correctly

        '''
        pass

    @classmethod
    def get_version_url(cls, project):  # pragma: no cover
        ''' Method called to retrieve the url used to check for new version
        of the project provided, project that relies on the backend of this plugin.

        Attributes:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            str: url used for version checking
        '''
        pass

    @classmethod
    def get_versions(self, project):  # pragma: no cover
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        Attributes:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            :obj:`list`: A list of all the possible releases found

        Raises:
            AnityaPluginException: A
                :obj:`anitya.lib.exceptions.AnityaPluginException` exception
                when the versions cannot be retrieved correctly

        '''
        pass

    @classmethod
    def check_feed(self):
        ''' Method called to retrieve the latest uploads to a given backend,
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

        '''
        raise NotImplementedError()

    @classmethod
    def get_ordered_versions(self, project):
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, ordered from the oldest to the newest.

        Attributes:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            :obj:`list`: A sorted list of all the possible releases found

        Raises:
            AnityaPluginException: A
                :obj:`anitya.lib.exceptions.AnityaPluginException` exception
                when the versions cannot be retrieved correctly

        '''
        vlist = self.get_versions(project)
        sorted_versions = project.create_version_objects(vlist)
        return [v.version for v in sorted_versions]

    @classmethod
    def call_url(self, url, insecure=False):
        ''' Dedicated method to query a URL.

        It is important to use this method as it allows to query them with
        a defined user-agent header thus informing the projects we are
        querying what our intentions are.

        Attributes:
            url (str): The url to request (get).
            insecure (bool, optional): Flag for secure/insecure connection.
                Defaults to False.

        Returns:
            In case of FTP url it returns binary encoded string
            otherwise :obj:`requests.Response` object.

        '''
        headers = REQUEST_HEADERS.copy()
        if '*' in url:
            url = self.expand_subdirs(url)

        if url.startswith('ftp://') or url.startswith('ftps://'):
            socket.setdefaulttimeout(30)

            req = urllib.Request(url)
            req.add_header('User-Agent', headers['User-Agent'])
            req.add_header('From', headers['From'])
            try:
                # Ignore this bandit issue, the url is checked above
                resp = urllib.urlopen(req)  # nosec
                content = resp.read().decode()
            except URLError as e:
                raise AnityaPluginException(
                        'Could not call "%s" with error: %s' % (
                            url, e.reason))
            except UnicodeDecodeError:
                raise AnityaPluginException(
                        'FTP response cannot be decoded with UTF-8: %s' % url)

            return content

        else:
            # Works around https://github.com/kennethreitz/requests/issues/2863
            # Currently, requests does not start new TCP connections based on
            # TLS settings. This means that if a connection is ever started to
            # a host with `verify=False`, further requests to that
            # (scheme, host, port) combination will also be insecure, even if
            # `verify=True` is passed to requests.
            #
            # This starts a new session which is immediately discarded when the
            # request is insecure. We don't get to pool connections for these
            # requests, but it stops us from making insecure requests by
            # accident. This can be removed in requests-3.0.
            if insecure:
                with requests.Session() as r_session:
                    resp = r_session.get(
                        url, headers=headers, timeout=60, verify=False)
            else:
                resp = http_session.get(
                    url, headers=headers, timeout=60, verify=True)

            return resp


def get_versions_by_regex(url, regex, project, insecure=False):
    ''' For the provided url, return all the version retrieved via the
    specified regular expression.

    '''

    try:
        req = BaseBackend.call_url(url, insecure=insecure)
    except Exception as err:
        _log.debug('%s ERROR: %s' % (project.name, str(err)))
        raise AnityaPluginException(
            'Could not call : "%s" of "%s", with error: %s' % (
                url, project.name, str(err)))

    if not isinstance(req, six.string_types):
        req = req.text

    return get_versions_by_regex_for_text(req, url, regex, project)


def get_versions_by_regex_for_text(text, url, regex, project):
    ''' For the provided text, return all the version retrieved via the
    specified regular expression.

    '''

    try:
        upstream_versions = list(set(re.findall(regex, text)))
    except sre_constants.error:  # pragma: no cover
        raise AnityaPluginException(
            "%s: invalid regular expression" % project.name)

    for index, version in enumerate(upstream_versions):

        # If the version retrieved is a tuple, re-constitute it
        if type(version) == tuple:
            version = ".".join([v for v in version if not v == ""])

        upstream_versions[index] = version

        if " " in version:
            raise AnityaPluginException(
                "%s: invalid upstream version:>%s< - %s - %s " % (
                    project.name, version, url, regex))
    if len(upstream_versions) == 0:
        raise AnityaPluginException(
            "%(name)s: no upstream version found. - %(url)s -  "
            "%(regex)s" % {
                'name': project.name, 'url': url, 'regex': regex})

    return upstream_versions
