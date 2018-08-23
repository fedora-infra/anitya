# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Michal Konecny <mkonecny@redhat.com>

"""

from anitya.lib.backends import BaseBackend, http_session, REQUEST_HEADERS
from anitya.lib.exceptions import AnityaPluginException, RateLimitException
from anitya.config import config
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

        if not (owner or repo):
            raise AnityaPluginException(
                'Project %s was incorrectly set-up. \
                Can\'t parse owner and repo' % project.name)

        query = prepare_query(owner, repo)

        try:
            headers = REQUEST_HEADERS.copy()
            token = config.get('GITHUB_ACCESS_TOKEN')
            if token:
                headers['Authorization'] = 'bearer %s' % token
            resp = http_session.post(
                API_URL, json={'query': query}, headers=headers, timeout=60, verify=True)
        except Exception as err:
            _log.debug('%s ERROR: %s' % (project.name, str(err)))
            raise AnityaPluginException(
                'Could not call : "%s" of "%s", with error: %s' % (
                    API_URL, project.name, str(err)))

        if resp.ok:
            json = resp.json()
        else:
            raise AnityaPluginException(
                '%s: Server responded with status "%s": "%s"' % (
                    project.name, resp.status_code, resp.reason))

        versions = parse_json(json, project)

        return versions


def parse_json(json, project):
    ''' Method for parsing json response

    :arg json: json response to parse
    :type owner: str
    :arg Project project: a :class:`anitya.db.models.Project` object whose backend
        corresponds to the current plugin.
    :return: versions
    :return type: list
    '''
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

    if remaining == 0:
        raise RateLimitException(reset_time)

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


def prepare_query(owner, repo, after=''):
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
}''' % (owner, repo, after_str)

    return query
