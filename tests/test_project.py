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
cnucnuweb tests for the Project object.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya.lib.model as model
from tests import Modeltests, create_project


class Projecttests(Modeltests):
    """ Project tests. """

    def test_project_init(self):
        """ Test the __init__ function of Project. """
        create_project(self.session)
        self.assertEqual(3, model.Project.all(self.session, count=True))

        projects = model.Project.all(self.session)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[2].name, 'subsurface')

    def test_project_by_name(self):
        """ Test the by_name function of Project. """
        create_project(self.session)

        project = model.Project.by_name(self.session, 'geany')
        self.assertEqual(project[0].name, 'geany')
        self.assertEqual(project[0].homepage, 'http://www.geany.org/')

        project = model.Project.by_name(self.session, 'terminal')
        self.assertEqual(project, [])

    def test_project_by_id(self):
        """ Test the by_id function of Project. """
        create_project(self.session)

        project = model.Project.by_id(self.session, 1)
        self.assertEqual(project.name, 'geany')
        self.assertEqual(project.homepage, 'http://www.geany.org/')

        project = model.Project.get(self.session, 1)
        self.assertEqual(project.name, 'geany')
        self.assertEqual(project.homepage, 'http://www.geany.org/')

        project = model.Project.by_id(self.session, 2)
        self.assertEqual(project.name, 'subsurface')
        self.assertEqual(project.homepage, 'http://subsurface.hohndel.org/')

        project = model.Project.get(self.session, 2)
        self.assertEqual(project.name, 'subsurface')
        self.assertEqual(project.homepage, 'http://subsurface.hohndel.org/')

        project = model.Project.by_id(self.session, 10)
        self.assertEqual(project, None)

    def test_project_by_homepage(self):
        """ Test the by_homepage function of Project. """
        create_project(self.session)

        projects = model.Project.by_homepage(
            self.session, 'http://www.geany.org/')
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[0].homepage, 'http://www.geany.org/')

        projects = model.Project.by_homepage(
            self.session, 'http://subsurface.hohndel.org/')
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].name, 'subsurface')
        self.assertEqual(projects[0].homepage, 'http://subsurface.hohndel.org/')

        project = model.Project.by_homepage(self.session, 'terminal')
        self.assertEqual(project, [])

    def test_project_all(self):
        """ Test the all function of Project. """
        create_project(self.session)

        projects = model.Project.all(self.session)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[0].homepage, 'http://www.geany.org/')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(
            projects[1].homepage, 'https://fedorahosted.org/r2spec/')

        projects = model.Project.all(self.session, page=3)
        self.assertEqual(projects, [])

    def test_project_search(self):
        """ Test the search function of Project. """
        create_project(self.session)

        projects = model.Project.search(self.session, 'gea')
        self.assertEqual(projects, [])

        projects = model.Project.search(self.session, 'gea*')
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[0].homepage, 'http://www.geany.org/')

    def test_distro_repr(self):
        """ Test the __repr__ function of Project. """
        create_project(self.session)

        obs = '<Project(geany, http://www.geany.org/)>'
        project = model.Project.by_id(self.session, 1)
        self.assertEqual(str(project), obs)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Projecttests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
