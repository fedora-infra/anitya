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
anitya tests for the Distro object.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya.lib.model as model
from tests import Modeltests, create_distro


class Distrotests(Modeltests):
    """ Distro tests. """

    def test_init_distro(self):
        """ Test the __init__ function of Distro. """
        create_distro(self.session)
        self.assertEqual(2, model.Distro.all(self.session, count=True))

        distros = model.Distro.all(self.session)
        self.assertEqual(distros[0].name, 'Debian')
        self.assertEqual(distros[1].name, 'Fedora')

    def test_distro_by_name(self):
        """ Test the by_name function of Distro. """
        create_distro(self.session)

        distro = model.Distro.by_name(self.session, 'fedora')
        self.assertEqual(distro.name, 'Fedora')

        distro = model.Distro.get(self.session, 'fedora')
        self.assertEqual(distro.name, 'Fedora')

        distro = model.Distro.by_name(self.session, 'DEBIAN')
        self.assertEqual(distro.name, 'Debian')

        distro = model.Distro.get(self.session, 'DEBIAN')
        self.assertEqual(distro.name, 'Debian')

    def test_distro_all(self):
        """ Test the all function of Distro. """
        create_distro(self.session)

        distro = model.Distro.all(self.session, page=2)
        self.assertEqual(distro, [])

        distro = model.Distro.all(self.session, page='b')
        distro2 = model.Distro.all(self.session)
        self.assertEqual(distro, distro2)

    def test_distro_json(self):
        """ Test the __json__ function of Distro. """
        create_distro(self.session)

        distro = model.Distro.by_name(self.session, 'fedora')
        self.assertEqual(distro.__json__(), {'name': 'Fedora'})

    def test_distro_search(self):
        """ Test the search function of Distro. """
        create_distro(self.session)

        distro = model.Distro.search(self.session, 'fed')
        self.assertEqual(distro, [])

        distro = model.Distro.search(self.session, 'fed*')
        self.assertNotEqual(distro, [])
        self.assertEqual(distro[0].name, 'Fedora')
        self.assertEqual(len(distro), 1)

    def test_distro_get_or_create(self):
        """ Test the get_or_create function of Distro. """
        create_distro(self.session)

        distro = model.Distro.get_or_create(self.session, 'fedora')
        self.assertEqual(distro.name, 'Fedora')
        self.assertEqual(2, model.Distro.all(self.session, count=True))

        distro = model.Distro.get_or_create(self.session, 'CentOS')
        self.assertEqual(distro.name, 'CentOS')
        self.assertEqual(3, model.Distro.all(self.session, count=True))


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Distrotests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
