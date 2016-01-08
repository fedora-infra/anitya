# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException


REGEX = b'class="tag-name">([^<]*)</span'


class GithubBackend(BaseBackend):
    ''' The custom class for projects hosted on github.com.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'GitHub'
    examples = [
        'https://github.com/fedora-infra/fedocal',
        'https://github.com/fedora-infra/pkgdb2',
    ]

    def get_url_from_regex_match(cls, regex_match):
        url_template = 'https://github.com/{}/tags'

        repo_owner = regex_match.group(1)
        repo_name = regex_match.group(2)

        url = url_template.format(
            "{}/{}".format(
                repo_owner, repo_name
            )
        )

        return url

    @classmethod
    def get_version(cls, project):
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
        return cls.get_ordered_versions(project)[-1]

    @classmethod
    def get_versions(cls, project):
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
        github_repo_regex = 'http[s]?:\/\/github\.com\/([^\/]+)\/([^\/]+)[\/]?'

        homepage_gh_regex_match = re.match(github_repo_regex, project.homepage)

        if project.version_url:
            matched_url_regex = re.match(github_repo_regex, project.version_url)
            if matched_url_regex:
                # matches github repo url
                # e.g https://github.com/fedora-infra/anitya
                url = cls.get_url_from_regex_match(matched_url_regex)
            else:
                # does not match github repo url,
                # assume repoowner/reponame format
                # e.g fedora-infra/anitya
                url = url_template.format(project.version_url)

        elif homepage_gh_regex_match:
            # homepage matches github repo regex
            url = cls.get_url_from_regex_match(homepage_gh_regex_match)

        else:
            raise AnityaPluginException(
                'Project %s was incorrectly set-up' % project.name)

        return get_versions_by_regex(url, REGEX, project)
