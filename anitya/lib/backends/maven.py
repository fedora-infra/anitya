# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Michael Simacek <msimacek@redhat.com>

"""

import re
import subprocess
import json

from anitya.lib.backends import BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException
from anitya.lib.model import Project
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
        ''' Return a generator over the latest 40 packages to Maven central index

        by calling maven-index-checker application
        '''
        maven_url = 'http://repo2.maven.org/maven2'
        jar_path = '/src/maven-release-checker-1.0-SNAPSHOT-jar-with-dependencies.jar'
        # session for checking whether there is already created package
        session = init(APP.config['DB_URL'], create=True, debug=False)

        try:
            data = subprocess.check_output(["java", "-jar", jar_path], universal_newlines=True)
        except Exception:
            raise AnityaPluginException('Could not start %s' % maven_url)

        data = json.loads(data)
        for item in data[:40]:
            item = json.loads(item)
            maven_coordinates = '{group_id}:{artifact_id}'.\
                format(group_id=item['groupId'], artifact_id=item['artifactId'])
            # maven_coordinates are stored in db as version_url
            retrieved_projects = Project.by_version_url(session, maven_coordinates)
            if len(retrieved_projects) != 0:
                # If there is project created it can have different name than maven_coordinates
                name = retrieved_projects[0].name
                homepage = retrieved_projects[0].homepage
            else:
                name = maven_coordinates
                homepage = '{maven_url}/{artifact}'.\
                    format(maven_url=maven_url, artifact=name.replace('.', '/').replace(':', '/'))
            version = item['version']
            yield name, homepage, cls.name, version
