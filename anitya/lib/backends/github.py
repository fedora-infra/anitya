# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Michal Konecny <mkonecny@redhat.com>

"""

from anitya.lib.backends import BaseBackend, http_session
from anitya.lib.exceptions import AnityaPluginException
from anitya.config import config
import requests
import logging

API_URL = 'https://api.github.com/graphql'

_log = logging.getLogger(__name__)


class GithubBackend(BaseBackend):
    ''' The custom class for projects hosted on github.com.

    This backend is using GitHub API v4 to query releases
    for projects hosted on github.com
    See: https://developer.github.com/v4/
    '''

    name = 'GitHub'
    examples = [
        'https://github.com/fedora-infra/fedocal',
        'https://github.com/fedora-infra/pkgdb2',
    ]

    @classmethod
    def get_version(cls, project):
        ''' Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: the latest version found upstream
        :return type: str
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the version cannot be retrieved correctly

        '''
        return cls.get_ordered_versions(project)[-1]

    @classmethod
    def get_versions(cls, project):
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        '''
        owner = None
        repo = None
        if project.version_url:
            url = project.version_url
        elif project.homepage.startswith('https://github.com'):
            url = project.homepage.replace('https://github.com/', '')
            if url.endswith('/'):
                url = url[:-1]
        else:
            raise AnityaPluginException(
                'Project %s was incorrectly set-up' % project.name)

        if url:
            (owner, repo) = url.split('/')

        if (not owner) or (not repo):
            raise AnityaPluginException(
                'Project %s was incorrectly set-up. \
                Can\'t parse owner and repo' % project.name)

        query = cls.prepare_query(owner, repo)

        try:
            resp = cls.call_url_post(API_URL, query, use_token=True)
        except Exception as err:
            _log.debug('%s ERROR: %s' % (project.name, str(err)))
            raise AnityaPluginException(
                'Could not call : "%s" of "%s", with error: %s' % (
                    url, project.name, str(err)))

        if resp.ok:
            json = resp.json()
        else:
            raise AnityaPluginException(
                '%s: Server responded with status "%s": "%s"' % (
                    project.name, resp.status_code, resp.reason))

        if 'errors' in json:
            error_str = ''
            for error in json['errors']:
                error_str += '"%s": "%s"\n' % (
                    error['type'], error['message'])
            raise AnityaPluginException(
                '%s: Server responded with following errors\n%s' % (
                    project.name, error_str))

        total_count = json['data']['repository']['refs']['totalCount']

        _log.debug('Received %s tags for %s' % (total_count, project.name))

        # TODO: Save cursor to project and use it to fetch only newer versions
        # cursor = json['data']['repository']['refs']['edges']['cursor']

        remaining = json['data']['rateLimit']['remaining']
        reset_time = json['data']['rateLimit']['resetAt']
        _log.debug('Github API ratelimit remains %s, will reset at %s UTC' % (
                remaining, reset_time))

        versions = []

        for edge in json['data']['repository']['refs']['edges']:
            version = edge['node']['name']
            if project.version_prefix is not None and \
                    version.startswith(project.version_prefix):
                version = version[len(project.version_prefix):]
            elif version.startswith('v'):
                version = version[1:]
            # TODO: Save commit url to DB and make versions clickable on frontend
            # commit_url = edge['node']['target']['commitUrl']
            versions.append(version)

        return versions

    @classmethod
    def prepare_query(cls, owner, repo, after=''):
        ''' Method for preparing GraphQL query for specified repository

        :arg owner: owner of the repository
        :type owner: str
        :arg repo: repository name
        :type repo: str
        :arg after: cursor id of the latest received commit
        :type after: str
        :return: GraphQL query
        :return type: str
        '''

        after_str = ''

        # Fill cursor if we have the id
        if after:
            after_str = ', after: "%s"' % after

        query = '''
        {
            repository(owner: "%s", name: "%s") {
                refs (refPrefix: "refs/tags/", last:50,
                        orderBy:{field:TAG_COMMIT_DATE, direction:ASC}%s) {
                    totalCount
                    edges {
                        cursor
                        node {
                            name
                            target {
                                commitUrl
                            }
                        }
                    }
                }
            }
            rateLimit {
                limit
                remaining
                resetAt
            }
        }
        ''' % (owner, repo, after_str)

        return query

    @classmethod
    def call_url_post(cls, url, json, insecure=False, use_token=False):
        ''' Dedicated method to send post request to specific URL.

        It is important to use this method as it allows to query them with
        a defined user-agent header thus informing the projects we are
        querying what our intentions are.

        :arg url: the url to request (post).
        :type url: str
        :arg json: json query to sent
        :type data: str
        :arg insecure: flag for secure/insecure connection (default False)
        :type insecure: bool
        :arg use_token: if this flag is set than use authorization token.
            Currently used only for :class:`anitya.lib.backends.GithubBackend`
        :type use_token: bool
        :return: the request object corresponding to the request made
        :return type: Request
        '''
        headers = cls.get_header()
        token = config.get('GITHUB_ACCESS_TOKEN')
        if use_token and token:
            headers['Authorization'] = 'bearer %s' % token

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
                resp = r_session.post(
                    url, json={'query': json}, headers=headers, timeout=60, verify=False)
        else:
            resp = http_session.post(
                url, json={'query': json}, headers=headers, timeout=60, verify=True)

        return resp
