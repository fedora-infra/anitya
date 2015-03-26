# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import fnmatch
import re
import socket
# sre_constants contains re exceptions
import sre_constants
import urllib2

import requests
import anitya
import anitya.app
from anitya.lib.exceptions import AnityaPluginException


REGEX = b'%(name)s(?:[-_]?(?:minsrc|src|source))?[-_]([^-/_\s]+?)(?i)(?:[-_]'\
    '(?:minsrc|src|source))?\.(?:tar|t[bglx]z|tbz2|zip)'


def upstream_cmp(v1, v2):
    """ Compare two upstream versions

    Code from Till Maas as part of
    `cnucnu <https://fedorapeople.org/cgit/till/public_git/cnucnu.git/>`_

    :Parameters:
        v1 : str
            Upstream version string 1
        v2 : str
            Upstream version string 2

    :return:
        - -1 - second version newer
        - 0  - both are the same
        - 1  - first version newer

    :rtype: int

    """

    # Strip leading 'v' characters; turn v1.0 into 1.0.
    # https://github.com/fedora-infra/anitya/issues/110
    v1 = v1.lstrip('v')
    v2 = v2.lstrip('v')

    v1, rc1, rcn1 = split_rc(v1)
    v2, rc2, rcn2 = split_rc(v2)

    diff = rpm_cmp(v1, v2)
    if diff != 0:
        # base versions are different, ignore rc-status
        return diff

    if rc1 and rc2:
        # both are rc, higher rc is newer
        diff = cmp(rc1.lower(), rc2.lower())
        if diff != 0:
            # rc > pre > beta > alpha
            return diff
        if rcn1 and rcn2:
            # both have rc number
            return cmp(int(rcn1), int(rcn2))
        if rcn1:
            # only first has rc number, then it is newer
            return 1
        if rcn2:
            # only second has rc number, then it is newer
            return -1
        # both rc numbers are missing or same
        return 0

    if rc1:
        # only first is rc, then second is newer
        return -1
    if rc2:
        # only second is rc, then first is newer
        return 1

    # neither is a rc
    return 0


def split_rc(version):
    """ Split (upstream) version into version and release candidate string +
    release candidate number if possible

    Code from Till Maas as part of
    `cnucnu <https://fedorapeople.org/cgit/till/public_git/cnucnu.git/>`_

    """
    rc_upstream_regex = re.compile(
        "(.*?)\.?(-?(rc|pre|beta|alpha|dev)([0-9]*))", re.I)
    match = rc_upstream_regex.match(version)
    if not match:
        return (version, "", "")

    rc_str = match.group(3)
    if rc_str:
        v = match.group(1)
        rc_num = match.group(4)
        return (v, rc_str, rc_num)
    else:
        # if version contains a dash, but no release candidate string is found,
        # v != version, therefore use version here
        # Example version: 1.8.23-20100128-r1100
        # Then: v=1.8.23, but rc_str=""
        return (version, "", "")


def rpm_cmp(v1, v2):
    import rpm
    diff = rpm.labelCompare((None, v1, None), (None, v2, None))
    return diff


class BaseBackend(object):
    ''' The base class that all the different backend should extend. '''

    name = None
    examples = None

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
            list.sort(subdirs, cmp=upstream_cmp)
            latest = subdirs[-1]

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
        vlist = self.get_versions(project)
        return anitya.order_versions(vlist)

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

            return requests.get(url, headers=headers, verify=not insecure)


def get_versions_by_regex(url, regex, project, insecure=False):
    ''' For the provided url, return all the version retrieved via the
    specified regular expression.

    '''

    try:
        req = BaseBackend.call_url(url, insecure=insecure)
    except Exception, err:
        anitya.LOG.debug('%s ERROR: %s' % (project.name, err.message))
        raise AnityaPluginException(
            'Could not call : "%s" of "%s"' % (url, project.name))

    if not isinstance(req, basestring):
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
