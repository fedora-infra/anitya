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
anitya tests of the model.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import datetime
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya.lib.model as model
from tests import Modeltests, create_distro, create_project, create_package


class Modeltests(Modeltests):
    """ Model tests. """

    def test_init_distro(self):
        """ Test the __init__ function of Distro. """
        create_distro(self.session)
        self.assertEqual(2, model.Distro.all(self.session, count=True))

        distros = model.Distro.all(self.session)
        self.assertEqual(distros[0].name, 'Debian')
        self.assertEqual(distros[1].name, 'Fedora')

    def test_init_project(self):
        """ Test the __init__ function of Project. """
        create_project(self.session)
        self.assertEqual(3, model.Project.all(self.session, count=True))

        projects = model.Project.all(self.session)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[2].name, 'subsurface')

    def test_log_search(self):
        """ Test the Log.search function. """
        create_project(self.session)

        logs = model.Log.search(self.session)
        self.assertEqual(len(logs), 3)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: R2spec')
        self.assertEqual(
            logs[1].description,
            'noreply@fedoraproject.org added project: subsurface')
        self.assertEqual(
            logs[2].description,
            'noreply@fedoraproject.org added project: geany')

        logs = model.Log.search(self.session, count=True)
        self.assertEqual(logs, 3)

        from_date = datetime.date.today() - datetime.timedelta(days=1)
        logs = model.Log.search(
            self.session, from_date=from_date, offset=1, limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

        logs = model.Log.search(self.session, project_name='subsurface')
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

    def test_distro_search(self):
        """ Test the Distro.search function. """
        create_distro(self.session)

        logs = model.Distro.search(self.session, '*', count=True)
        self.assertEqual(logs, 2)

        logs = model.Distro.search(self.session, 'Fed*')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = model.Distro.search(self.session, 'Fed*', page=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = model.Distro.search(self.session, 'Fed*', page='as')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

    def test_packages_by_id(self):
        """ Test the Packages.by_id function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = model.Packages.by_id(self.session, 1)
        self.assertEqual(pkg.package_name, 'geany')
        self.assertEqual(pkg.distro, 'Fedora')

    def test_packages__repr__(self):
        """ Test the Packages.__repr__ function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = model.Packages.by_id(self.session, 1)
        self.assertEqual(str(pkg), '<Packages(1, Fedora: geany)>')

    def test_project_all(self):
        """ Test the Project.all function. """
        create_project(self.session)

        projects = model.Project.all(self.session, count=True)
        self.assertEqual(projects, 3)

        projects = model.Project.all(self.session, page=2)
        self.assertEqual(len(projects), 0)

        projects = model.Project.all(self.session, page='asd')
        self.assertEqual(len(projects), 3)

    def test_project_search(self):
        """ Test the Project.search function. """
        create_project(self.session)

        projects = model.Project.search(self.session, '*', count=True)
        self.assertEqual(projects, 3)

        projects = model.Project.search(self.session, '*', page=2)
        self.assertEqual(len(projects), 0)

        projects = model.Project.search(self.session, '*', page='asd')
        self.assertEqual(len(projects), 3)

    def test_backend_by_name(self):
        """ Test the Backend.by_name function. """
        import anitya.lib.plugins as plugins
        plugins.load_plugins(self.session)
        backend = model.Backend.by_name(self.session, 'pypi')
        self.assertEqual(backend.name, 'pypi')

    def test_project_get_or_create(self):
        """ Test the Project.get_or_create function. """
        project = model.Project.get_or_create(
            self.session,
            name='test',
            homepage='http://test.org',
            backend='custom')
        self.assertEqual(project.name, 'test')
        self.assertEqual(project.homepage, 'http://test.org')
        self.assertEqual(project.backend, 'custom')

        self.assertRaises(
            ValueError,
            model.Project.get_or_create,
            self.session,
            name='test_project',
            homepage='http://project.test.org',
            backend='foobar'
        )

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
