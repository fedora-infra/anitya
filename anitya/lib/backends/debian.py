# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from anitya.lib.backends import BaseBackend, get_versions_by_regex


# Debian packagers upload the original source tarball in the format
# <name>_<version>.orig.<compression format>. So, for example,
# reprepro_4.13.1.orig.tar.gz.
DEBIAN_REGEX = (
    '%(name)s(?:[-_]?(?:minsrc|src|source))?[-_]([^-/_\s]+?)(?i)(?:[-_]'
    '(?:minsrc|src|source|asc))?\.(?:orig\.)?(?:tar|t[bglx]z|tbz2|zip)'
)


class DebianBackend(BaseBackend):
    ''' The custom class for projects hosted on ftp.debian.org.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'Debian project'
    examples = [
        'http://ftp.debian.org/debian/pool/main/q/qpdf/',
        'http://ftp.debian.org/debian/pool/main/g/guake/',
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
        url_template = 'http://ftp.debian.org/debian/pool/main/'\
            '%(short)s/%(name)s/'

        if project.name.startswith('lib'):
            short = project.name[:4]
        else:
            short = project.name[0]

        url = url_template % {'short': short, 'name': project.name}
        regex = DEBIAN_REGEX % {'name': project.name}

        return get_versions_by_regex(url, regex, project)
