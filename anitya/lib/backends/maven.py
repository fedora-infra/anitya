# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Michael Simacek <msimacek@redhat.com>

"""

import re
from subprocess import check_output, CalledProcessError
import json
import requests
import itertools

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException
from anitya.lib.model import Project, NoResultFound
from anitya.config import config
from anitya.lib.backends import http_session

REGEX = r'\<a[^>]+\>(\d[^</]*)'


class MavenBackend(BaseBackend):
    ''' Backend for projects hosted on Maven Central '''

    name = 'Maven Central'
    maven_url = 'http://repo2.maven.org/maven2'
    examples = [
        'http://repo1.maven.org/maven2/plexus/plexus-compiler/',
        'http://repo1.maven.org/maven2/com/google/inject/guice/',
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
        if re.match(r'https?://repo\d+.maven.org/', project.homepage):
            url = project.homepage
        else:
            coordinates = project.version_url or project.name
            if ':' not in coordinates:
                raise AnityaPluginException(
                    "Aritfact needs to be in format groupId:artifactId")
            url = 'http://repo1.maven.org/maven2/{path}'\
                  .format(path=coordinates.replace('.', '/')
                          .replace(':', '/'))

        return get_versions_by_regex(url, REGEX, project)

    @classmethod
    def create_correct_url(cls, group_id, artifact_id):
        '''Method tries to create url from given groupId and artifactId             
        
        :param group_id: groupId of project
        :param artifact_id: artifactId of project
        :return: URL to Maven Central for group_id and artifact_id
        '''
        temp_artifact = artifact_id
        temp_group = group_id
        for pattern1, pattern2 in itertools.product(['(?=\d)', r'(?=\D)'], repeat=2):
            temp_artifact = re.sub(r'{}\.{}'.format(pattern1, pattern2), r'/', temp_artifact)
            temp_group = re.sub(r'{}\.{}'.format(pattern1, pattern2), r'/', temp_group)

        for group, artifact in [(temp_group, temp_artifact), (temp_group, artifact_id),
                                (group_id, temp_artifact), (group_id, artifact_id)]:
            homepage = '{maven_url}/{group}/{artifact}/'.format(
                maven_url=MavenBackend.maven_url, group=group, artifact=artifact)
            try:
                request = http_session.get(homepage)
                if request.status_code == 200:
                    return homepage
            except requests.RequestException:
                pass

    @classmethod
    def check_feed(cls):
        '''check_feed for Maven backend.

        Return a generator over the latest 40 packages to Maven central index by
        calling maven-index-checker application

        Returns:
            generator over new packages
        '''

        if config['JAVA_PATH'] is None:
            raise AnityaPluginException('no java binary specified')
        if config['JAR_NAME'] is None:
            raise AnityaPluginException('no maven-release-checker jar file specified')

        try:
            data = check_output([config['JAVA_PATH'], "-jar",
                                 config['JAR_NAME'], "-it"], universal_newlines=True)
        except CalledProcessError:
            raise AnityaPluginException(
                'maven-release-checker exited with non zero value')
        for item in json.loads(data):
            maven_coordinates = '{group_id}:{artifact_id}'. \
                format(group_id=item['groupId'], artifact_id=item['artifactId'])
            try:
                projects = Project.query.filter(Project.version_url
                                                == maven_coordinates).all()
            except NoResultFound:
                projects = []

            if len(projects) != 0:
                # If there is project created it can have
                # different name than maven_coordinates
                name = projects[0].name
                homepage = projects[0].homepage
            else:
                name = maven_coordinates
                homepage = cls.create_correct_url(item['groupId'], item['artifactId'])
                if homepage is None:
                    continue
            version = item['version']
            yield name, homepage, cls.name, version
