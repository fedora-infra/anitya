#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Migrate all the projects present on the wiki into Cnucnu Web """

## Requires:
## project name -- Fedora package name
# python-bugzilla -- python-bugzilla
# PyYAML -- PyYAML
# pycurl -- python-pycurl
# python-fedora -- python-fedora

import os

import cnucnu
from cnucnu.package_list import PackageList
import anitya.lib
from anitya.lib import model
from anitya.app import SESSION

CONVERT_URL = {
    'SF-DEFAULT': 'http://sourceforge.net/projects/%s',
    'FM-DEFAULT': 'http://freshmeat.net/projects/%s',
    'GNU-DEFAULT': 'http://www.gnu.org/software/%s/',
    'CPAN-DEFAULT': 'http://search.cpan.org/dist/%s/',
    'DRUPAL-DEFAULT': 'http://drupal.org/project/%s',
    'HACKAGE-DEFAULT': 'http://hackage.haskell.org/package/%s',
    'DEBIAN-DEFAULT': 'http://packages.debian.org/%s',
    'GOOGLE-DEFAULT': 'http://code.google.com/p/%s',
    'PYPI-DEFAULT': 'https://pypi.python.org/pypi/%s',
    'PEAR-DEFAULT': 'http://pear.php.net/package/%s',
    'PECL-DEFAULT': 'http://pecl.php.net/package/%s',
    'LP-DEFAULT': 'https://launchpad.net/%s',
    'GNOME-DEFAULT': 'http://download.gnome.org/sources/%s/*/',
    'NPM-DEFAULT': 'http://npmjs.org/package/%s',
    'RUBYGEMS-DEFAULT': 'http://rubygems.org/gems/%s'
}


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


def clean_url(url):
    ''' For a given url try to see if it can be clean to refer to the
    homepage of the project rather than the page where the releases are
    listed.
    '''
    if 'github.com' in url:
        if url.endswith('/tags'):
            url = url.rsplit('/', 1)[0]
        if url.endswith('/tags/'):
            url = url.rsplit('/', 2)[0]
        if url.endswith('/releases'):
            url = url.rsplit('/', 1)[0]
        if url.endswith('/releases/'):
            url = url.rsplit('/', 2)[0]
    elif 'gitorious.org' in url:
        if url.endswith('pages/Download') or url.endswith('pages/Download/'):
            url = url.rsplit('pages')[0]
    return url


def migrate_wiki(agent):
    ''' Retrieve the list of projects from the wiki and import them into
    the database.
    '''
    cnt = 0
    failed = 0
    k = []
    for pkg in get_package_list():

        name = None
        url = pkg.raw_url
        for key in CONVERT_URL:
            if url.startswith(key) and ':' in url:
                url, name = url.split(':')
        if url in CONVERT_URL:
            url = CONVERT_URL[url] % (name or pkg.name)
        else:
            url = clean_url(url)

        # @pypingou, what is going on here?  cnucnu.clear_name only exists in
        # your fork?  but, I can't find your fork.  What should be done here?
        #if name:
        #    name = cnucnu.clear_name(name, url)
        #    # Only keep the name if it is
        #    #if pkg.name.lower().startswith(name.lower()):
        #        #name = None

        project = anitya.lib.model.Project.get_or_create(
            SESSION,
            name=(name or pkg.name),
            homepage=url,
        )

        package = anitya.lib.map_project(
            SESSION, project, pkg.name, 'Fedora', agent)
        project.packages.append(package)

        SESSION.commit()
        cnt += 1
    print '{0} projects imported'.format(cnt)
    print '{0} projects failed to imported'.format(failed)


if __name__ == '__main__':
    agent = os.getlogin() + "@fedoraproject.org"
    migrate_wiki(agent)
