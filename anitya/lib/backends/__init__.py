# -*- coding: utf-8 -*-

"""
 (c) 2014-2015 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import fnmatch
import logging
import re
import socket
# sre_constants contains re exceptions
import sre_constants
import six.moves.urllib.request as urllib2

import requests
import six

from anitya.lib import model
from anitya.lib.exceptions import AnityaPluginException
import anitya
import anitya.app


REGEX = '%(name)s(?:[-_]?(?:minsrc|src|source))?[-_]([^-/_\s]+?)(?i)(?:[-_]'\
        '(?:minsrc|src|source|asc))?\.(?:tar|t[bglx]z|tbz2|zip)'

_log = logging.getLogger(__name__)


# Use a common http session, so we don't have to go re-establishing https
# connections over and over and over again.
http_session = requests.session()


class BaseBackend(object):
    ''' The base class that all the different backend should extend. '''

    name = None
    examples = None
    default_regex = None
    more_info = None

    @classmethod
    def expand_subdirs(self, url, glob_char="*"):
        ''' Expand dirs containing glob_char in the given URL with the latest
        Example URL: http://www.example.com/foo/*/

        The globbing char can be bundled with other characters enclosed within
        the same slashes in the URL like "/rel*/".

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
            dir_listing = self.call_url(url_prefix).text
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

            # Make use of the PEP-440 version parser and sorting to select the latest
            # directory. When we track all versions instead of just the latest, we can
            # iterate over all subdirs and look for new versions.
            versions = []
            for subdir in subdirs:
                versions.append(model.Pep440Version(version=subdir))
            latest = max(versions).version

            url = "%s%s/%s" % (url_prefix, latest, url_suffix)
            return self.expand_subdirs(url, glob_char)
        return url

    @classmethod
    def get_version(self, project):  # pragma: no cover
        ''' Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: the latest version found upstream
        :return type: str
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the version cannot be retrieved correctly

        '''
        pass

    @classmethod
    def get_versions(self, project):  # pragma: no cover
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        '''
        pass

    @classmethod
    def check_feed(self):
        ''' Method called to retrieve the latest uploads to a given backend,
        via, for example, RSS or an API.

        Not all backends may support this.  It can be used to look for updates
        much more quickly than scanning all known projects.

        :return: a list of 4-tuples, containing the project name, homepage, the
            backend, and the version.
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the version cannot be retrieved correctly
        :raise NotImplementedError:
            :class:`NotImplementedError` exception when the backend does not
            support batch updates.
        '''
        raise NotImplementedError()

    @classmethod
    def get_ordered_versions(self, project):
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, ordered from the oldest to the newest.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        '''
        vlist = sorted([project.version_class(version=v) for v in self.get_versions(project)])
        return [six.text_type(v) for v in vlist]

    @classmethod
    def call_url(self, url, insecure=False):
        ''' Dedicated method to query a URL.

        It is important to use this method as it allows to query them with
        a defined user-agent header thus informing the projects we are
        querying what our intentions are.

        :arg url: the url to request (get).
        :type url: str
        :return: the request object corresponding to the request made
        :return type: Request
        '''
        user_agent = 'Anitya %s at upstream-monitoring.org' % \
            anitya.app.__version__
        from_email = anitya.app.APP.config.get('ADMIN_EMAIL')

        if '*' in url:
            url = self.expand_subdirs(url)

        if url.startswith('ftp://') or url.startswith('ftps://'):
            socket.setdefaulttimeout(30)

            req = urllib2.Request(url)
            req.add_header('User-Agent', user_agent)
            req.add_header('From', from_email)
            resp = urllib2.urlopen(req)
            content = resp.read()

            return content

        else:
            headers = {
                'User-Agent': user_agent,
                'From': from_email,
            }

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

        # Strip the version_prefix early
        if project.version_prefix is not None and \
                version.startswith(project.version_prefix):
            version = version[len(project.version_prefix):]
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
