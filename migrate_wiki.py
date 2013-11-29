#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Migrate all the projects present on the wiki into Cnucnu Web """

## Requires:
## project name -- Fedora package name
# python-bugzilla -- python-bugzilla
# PyYAML -- PyYAML
# pycurl -- python-pycurl
# python-fedora -- python-fedora

from cnucnu.package_list import PackageList
from cnucnuweb import model
from cnucnuweb.app import SESSION


def get_package_list():
    ''' Calling the cnucnu backend, retrieve the list of projects from the
    wiki.
    '''
    mediawiki = {
        'base url': 'https://fedoraproject.org/w/',
        'page': 'Upstream_release_monitoring',
    }
    pkglist = PackageList(mediawiki=mediawiki)
    return pkglist


def migrate_wiki():
    ''' Retrieve the list of projects from the wiki and import them into
    the database.
    '''
    cnt = 0
    failed = 0
    for pkg in get_package_list():

        project = model.Project(
            name=pkg.name,
            homepage=pkg.url,
            version_url=pkg.url,
            regex=pkg.raw_regex,
            fedora_name=pkg.name,
            debian_name=None
        )
        SESSION.add(project)
        try:
            SESSION.commit()
        except Exception as err:
            failed += 1
            print err
            SESSION.rollback()
        cnt += 1
    print '{0} projects imported'.format(cnt)
    print '{0} projects failed to imported'.format(failed)


if __name__ == '__main__':
    migrate_wiki()
