# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Michael Simacek <msimacek@redhat.com>

"""

import re
from subprocess import check_output, CalledProcessError
import json

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException
from anitya.lib.model import Project, NoResultFound
from anitya.lib import init
from anitya.app import APP

REGEX = r'\<a[^>]+\>(\d[^</]*)'


class MavenBackend(BaseBackend):
    ''' Backend for projects hosted on Maven Central '''

    name = 'Maven Central'
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
    def check_feed(cls):
        '''check_feed for Maven backend.

        Return a generator over the latest 40 packages to Maven central index by
        calling maven-index-checker application

        Returns:
            generator over new packages
        '''
        maven_url = 'http://repo2.maven.org/maven2'
        if APP.config['JAVA_PATH'] is None:
            raise AnityaPluginException('no java binary specified')
        if APP.config['JAR_NAME'] is None:
            raise AnityaPluginException('no maven-release-checker jar file specified')

        try:
            data = check_output([APP.config['JAVA_PATH'], "-jar",
                                 APP.config['JAR_NAME']], universal_newlines=True)
        except CalledProcessError:
            raise AnityaPluginException('maven-release-checker exited with non zero value')

        data = json.loads(data)
        session = init(APP.config['DB_URL'])
        for item in data[:40]:
            item = json.loads(item)
            # maven_coordinates are stored in db as version_url
            maven_coordinates = '{group_id}:{artifact_id}'.\
                format(group_id=item['groupId'], artifact_id=item['artifactId'])
            try:
                projects = session.query(Project).filter(
                    Project.version_url == maven_coordinates).all()
            except NoResultFound:
                projects = None

            if projects is not None:
                # If there is project created it can have
                # different name than maven_coordinates
                name = projects[0].name
                homepage = projects[0].homepage
            else:
                name = maven_coordinates
                homepage = '{maven_url}/{artifact}'.\
                    format(maven_url=maven_url, artifact=name.replace('.', '/').replace(':', '/'))
            version = item['version']
            yield name, homepage, cls.name, version
