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

API_URL = "https://api.github.com/graphql"

"""
Rate limit threshold (percent)
10 percent of limit is left for users
"""
RATE_LIMIT_THRESHOLD = 0.1

_log = logging.getLogger(__name__)

"""
Reset time that is currently set for GitHub backend.
Used when GitHub starts returning HTTP status code 403,
which doesn't contains this information anymore.
"""
reset_time = "1970-01-01T00:00:00Z"


class GithubBackend(BaseBackend):
    """ The custom class for projects hosted on github.com.

    This backend is using GitHub API v4 to query releases
    for projects hosted on github.com
    See: https://developer.github.com/v4/
    """

    name = "GitHub"
    examples = [
        "https://github.com/fedora-infra/fedocal",
        "https://github.com/fedora-infra/pkgdb2",
    ]

    @classmethod
    def get_version(cls, project):
        """ Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        Args:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            str: Latest version found upstream

        Raises:
            AnityaPluginException: A
                :obj:`anitya.lib.exceptions.AnityaPluginException` exception
                when the versions cannot be retrieved correctly

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
        if project.version_url:
            url = project.version_url
        elif project.homepage.startswith("https://github.com"):
            url = project.homepage.replace("https://github.com/", "")

        if url.endswith("/"):
            url = url[:-1]

        if url:
            url = "https://github.com/{}/tags".format(url)

        return url

    @classmethod
    def get_versions(cls, project):
        """ Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        Args:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            :obj:`list`: A list of all the possible releases found

        Raises:
            AnityaPluginException: A
                :obj:`anitya.lib.exceptions.AnityaPluginException` exception
                when the versions cannot be retrieved correctly

        """
        owner = None
        repo = None
        url = cls.get_version_url(project)
        if url:
            url = url.replace("https://github.com/", "")
            url = url.replace("/tags", "")
        else:
            raise AnityaPluginException(
                "Project %s was incorrectly set-up" % project.name
            )

        try:
            (owner, repo) = url.split("/")
        except ValueError:
            raise AnityaPluginException(
                """Project {} was incorrectly set-up.
                Can\'t parse owner and repo.""".format(
                    project.name
                )
            )

        query = prepare_query(owner, repo, project.releases_only)

        try:
            headers = REQUEST_HEADERS.copy()
            token = config["GITHUB_ACCESS_TOKEN"]
            if token:
                headers["Authorization"] = "bearer %s" % token
            resp = http_session.post(
                API_URL, json={"query": query}, headers=headers, timeout=60, verify=True
            )
        except Exception as err:
            _log.debug("%s ERROR: %s" % (project.name, str(err)))
            raise AnityaPluginException(
                'Could not call : "%s" of "%s", with error: %s'
                % (API_URL, project.name, str(err))
            )

        if resp.ok:
            json = resp.json()
        elif resp.status_code == 403:
            _log.info("Github API ratelimit reached.")
            raise RateLimitException(reset_time)
        else:
            raise AnityaPluginException(
                '%s: Server responded with status "%s": "%s"'
                % (project.name, resp.status_code, resp.reason)
            )

        versions = parse_json(json, project)

        if len(versions) == 0:
            raise AnityaPluginException(
                "%s: No upstream version found." % (project.name)
            )

        return versions


def parse_json(json, project):
    """ Function for parsing json response

    Args:
        json (dict): Json dictionary to parse.
        project (:obj:`anitya.db.models.Project`): Project object whose backend
            corresponds to the current plugin.

    Returns:
        :obj:`list`: A list of all the possible releases found.

    Raises:
        AnityaPluginException: A
            :obj:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly.
        RateLimitException: A
            :obj:`anitya.lib.exceptions.RateLimitException` exception
            when rate limit threshold is reached.

    """
    global reset_time
    # We need to check limit first,
    # because exceeding the limit will also return error
    try:
        limit = json["data"]["rateLimit"]["limit"]
        remaining = json["data"]["rateLimit"]["remaining"]
        reset_time = json["data"]["rateLimit"]["resetAt"]
        _log.debug(
            "Github API ratelimit remains %s, will reset at %s UTC"
            % (remaining, reset_time)
        )

        if (remaining / limit) <= RATE_LIMIT_THRESHOLD:
            raise RateLimitException(reset_time)
    except KeyError:
        _log.info("Github API ratelimit key is missing. Checking for errors.")

    if "errors" in json:
        error_str = ""
        for error in json["errors"]:
            error_str += '"%s": "%s"\n' % (error["type"], error["message"])
        raise AnityaPluginException(
            "%s: Server responded with following errors\n%s" % (project.name, error_str)
        )
    if project.releases_only:
        json_data = json["data"]["repository"]["releases"]
    else:
        json_data = json["data"]["repository"]["refs"]

    total_count = json_data["totalCount"]

    if project.releases_only:
        _log.debug("Received %s releases for %s" % (total_count, project.name))
    else:
        _log.debug("Received %s tags for %s" % (total_count, project.name))

    versions = []

    for edge in json_data["edges"]:
        version = edge["node"]["name"]
        versions.append(version)

    return versions


def prepare_query(owner, repo, releases_only, cursor=""):
    """ Function for preparing GraphQL query for specified repository

    Args:
        owner (str): Owner of the repository.
        repo (str): Repository name.
        releases_only (bool): Fetch releases instead of tags.
        cursor (str, optional): Cursor id of the latest received commit.
            Defaults to empty string.

    Returns:
        str: GraphQL query.

    """

    cursor_str = ""
    commitUrl = "target { commitUrl }"

    # Fill cursor if we have the id
    if cursor:
        cursor_str = ', after: "%s"' % cursor

    if releases_only:
        fetch_string = "releases (orderBy: {field: CREATED_AT"
        commitUrl = "tag { " + commitUrl + " }"
    else:
        fetch_string = 'refs (refPrefix: "refs/tags/", orderBy: {field: TAG_COMMIT_DATE'

    query = """
{{
    repository(owner: "{owner}", name: "{name}") {{
        {fetch_string}, direction: ASC}}, last: 50{cursor}) {{
            totalCount
            edges {{
                cursor
                node {{
                    name
                    {commitUrl}
                }}
            }}
        }}
    }}
    rateLimit {{
        limit
        remaining
        resetAt
    }}
}}""".format(
        owner=owner,
        name=repo,
        fetch_string=fetch_string,
        cursor=cursor_str,
        commitUrl=commitUrl,
    )

    return query
