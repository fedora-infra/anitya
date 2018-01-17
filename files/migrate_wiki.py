#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Migrate all the projects present on the wiki into Cnucnu Web """

# Requires:
# project name -- Fedora package name
#
# python-bugzilla -- python-bugzilla
# PyYAML -- PyYAML
# pycurl -- python-pycurl
# python-fedora -- python-fedora

import os
import pprint

from cnucnu.package_list import PackageList
from anitya.config import config
import anitya.app
import anitya.lib
import anitya.lib.plugins

import anitya.lib.backends.sourceforge
import anitya.lib.backends.gnu
import anitya.lib.backends.freshmeat
import anitya.lib.backends.cpan
# TODO what about drupal6?
import anitya.lib.backends.drupal7
import anitya.lib.backends.hackage
import anitya.lib.backends.debian
import anitya.lib.backends.google
import anitya.lib.backends.github
import anitya.lib.backends.pypi
import anitya.lib.backends.pear
import anitya.lib.backends.pecl
import anitya.lib.backends.launchpad
import anitya.lib.backends.gnome
import anitya.lib.backends.npmjs
import anitya.lib.backends.rubygems
from anitya import db


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
    'RUBYGEMS-DEFAULT': 'http://rubygems.org/gems/%s',
    'GITHUB-TAGS': 'https://github.com/%s',
}


# Map old wiki names to new anitya names for our one-time conversion.
name_mapping = {
    'SF-DEFAULT': anitya.lib.backends.sourceforge.SourceforgeBackend.name,
    'GNU-DEFAULT': anitya.lib.backends.gnu.GnuBackend.name,
    'FM-DEFAULT': anitya.lib.backends.freshmeat.FreshmeatBackend.name,
    'CPAN-DEFAULT': anitya.lib.backends.cpan.CpanBackend.name,
    'DRUPAL-DEFAULT': anitya.lib.backends.drupal7.Drupal7Backend.name,
    'HACKAGE-DEFAULT': anitya.lib.backends.hackage.HackageBackend.name,
    'DEBIAN-DEFAULT': anitya.lib.backends.debian.DebianBackend.name,
    'GOOGLE-DEFAULT': anitya.lib.backends.google.GoogleBackend.name,
    'PYPI-DEFAULT': anitya.lib.backends.pypi.PypiBackend.name,
    'PEAR-DEFAULT': anitya.lib.backends.pear.PearBackend.name,
    'PECL-DEFAULT': anitya.lib.backends.pecl.PeclBackend.name,
    'LP-DEFAULT': anitya.lib.backends.launchpad.LaunchpadBackend.name,
    'GNOME-DEFAULT': anitya.lib.backends.gnome.GnomeBackend.name,
    'NPM-DEFAULT': anitya.lib.backends.npmjs.NpmjsBackend.name,
    'RUBYGEMS-DEFAULT': anitya.lib.backends.rubygems.RubygemsBackend.name,
    'GITHUB-TAGS': anitya.lib.backends.github.GithubBackend.name,
}


def get_package_list():
    ''' Calling the cnucnu backend, retrieve the list of projects from the
    wiki.
    '''
    mediawiki = {
        'base url': 'https://fedoraproject.org/w/',
        'page': 'Upstream_release_monitoring',
    }
    print "Getting package list from %(base url)s/%(page)s" % mediawiki
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

    print "Migrating from wiki as %r" % agent

    SESSION = anitya.lib.utilities.init(
        config['DB_URL'],
        None,
        create=True)

    cnt = 0
    problems = []
    for pkg in get_package_list():

        name = None
        url = pkg.raw_url
        backend = 'custom'

        if pkg.name.lower().startswith('rubygem-'):
            name = pkg.name.replace('rubygem-', '')

        for key in CONVERT_URL:
            if url.startswith(key) and ':' in url:
                url, name = url.split(':')
        if url in CONVERT_URL:
            backend = name_mapping.get(url, url)
            url = CONVERT_URL[url] % (name or pkg.name)
        else:
            url = clean_url(url)

        project = db.Project.get_or_create(
            SESSION,
            name=(name or pkg.name),
            homepage=url,
            backend=backend,
        )
        if backend == 'custom':
            project.version_url = url
        if backend == 'GitHub':
            project.version_url = (name or pkg.name)

        try:
            package = anitya.lib.utilities.map_project(
                SESSION, project, pkg.name, 'Fedora', agent)
            project.packages.append(package)

            SESSION.commit()
            cnt += 1
        except Exception:
            problems.append(pkg.name)

    print '{0} projects imported'.format(cnt)
    print '{0} projects failed to imported'.format(len(problems))
    pprint.pprint(problems)


if __name__ == '__main__':
    agent = os.getlogin() + "@fedoraproject.org"
    migrate_wiki(agent)
