# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

import github3

import anitya
from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


class GithubApiBackend(BaseBackend):
    ''' The custom class for projects hosted on github.com. It uses the github
    API instead of parsing the HTML returned by the web interface like github.py
    '''

    name = 'GitHub API'
    examples = [
        'https://github.com/fedora-infra/fedocal',
        'https://github.com/fedora-infra/pkgdb2',
    ]

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
        if project.version_url:
            url = project.version_url
        elif project.homepage.startswith('https://github.com'):
            url = project.homepage
        else:
            raise AnityaPluginException(
                'Project %s was incorrectly set-up' % project.name)

        url = url.replace('https://github.com/', '')

        try:
            owner, repo = url.split('/')
        except:
            raise AnityaPluginException(
                'Project %s was incorrectly set-up' % project.name)

        github_access_token = anitya.app.APP.config.get('GITHUB_ACCESS_TOKEN')

        if github_access_token:
            gh = github3.login(token=github_access_token)
        else:
            gh = github3

        repo = gh.repository(owner, repo)

        if not repo:
            raise AnityaPluginException(
                'Project %s does not exists on GitHub' % project.name)

        versions = []

        for tag in repo.tags():
            version = tag.name

            if project.version_prefix is not None and \
                    version.startswith(project.version_prefix):
                version = version[len(project.version_prefix):]
            elif version.startswith('v'):
                version = version[1:]

            versions.append(version)

        return versions
