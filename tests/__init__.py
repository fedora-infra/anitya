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

'''
Anitya tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import logging
import unittest
import sys
import os

from datetime import date
from datetime import timedelta

from contextlib import contextmanager
from flask import appcontext_pushed, g

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from anitya.app import APP
import anitya.lib
import anitya.lib.model as model

#DB_PATH = 'sqlite:///:memory:'
## A file database is required to check the integrity, don't ask
DB_PATH = 'sqlite:////tmp/anitya_test.sqlite'
FAITOUT_URL = 'http://209.132.184.152/faitout/'

if os.environ.get('BUILD_ID'):
    try:
        import requests
        req = requests.get('%s/new' % FAITOUT_URL)
        if req.status_code == 200:
            DB_PATH = req.text
            print 'Using faitout at: %s' % DB_PATH
    except:
        pass


log = logging.getLogger('anitya.lib')
anitya.lib.log.handlers = []
log.handlers = []


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        if ':///' in DB_PATH:
            dbfile = DB_PATH.split(':///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        self.session = anitya.lib.init(DB_PATH, create=True, debug=False)

        anitya.lib.plugins.load_plugins(self.session)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if '///' in DB_PATH:
            dbfile = DB_PATH.split('///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)

        self.session.rollback()
        self.session.close()

        if DB_PATH.startswith('postgres'):
            db_name = DB_PATH.rsplit('/', 1)[1]
            req = requests.get(
                '%s/clean/%s' % (FAITOUT_URL, db_name))
            print req.text


def create_distro(session):
    """ Create some basic distro for testing. """
    distro = model.Distro(
        name='Fedora',
    )
    session.add(distro)

    distro = model.Distro(
        name='Debian',
    )
    session.add(distro)

    session.commit()


def create_project(session):
    """ Create some basic projects to work with. """
    anitya.lib.create_project(
        session,
        name='geany',
        homepage='http://www.geany.org/',
        version_url='http://www.geany.org/Download/Releases',
        regex='DEFAULT',
        user_mail='noreply@fedoraproject.org',
    )

    anitya.lib.create_project(
        session,
        name='subsurface',
        homepage='http://subsurface.hohndel.org/',
        version_url='http://subsurface.hohndel.org/downloads/',
        regex='DEFAULT',
        user_mail='noreply@fedoraproject.org',
    )

    anitya.lib.create_project(
        session,
        name='R2spec',
        homepage='https://fedorahosted.org/r2spec/',
        user_mail='noreply@fedoraproject.org',
    )


def create_package(session):
    """ Create some basic packages to work with. """
    package = model.Packages(
        project_id=1,
        distro='Fedora',
        package_name='geany',
    )
    session.add(package)

    package = model.Packages(
        project_id=2,
        distro='Fedora',
        package_name='subsurface',
    )
    session.add(package)

    session.commit()


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
