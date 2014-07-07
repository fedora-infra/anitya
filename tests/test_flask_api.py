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
anitya tests for the flask API.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya
import anitya.lib.model as model
from tests import Modeltests, create_distro, create_project, create_package


class AnityaWebAPItests(Modeltests):
    """ Flask API tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(AnityaWebAPItests, self).setUp()

        anitya.app.APP.config['TESTING'] = True
        anitya.app.SESSION = self.session
        anitya.api.SESSION = self.session
        self.app = anitya.app.APP.test_client()

    def test_api_projects(self):
        """ Test the api_projects function of the API. """
        create_distro(self.session)

        output = self.app.get('/api/projects')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        exp = {"projects": [], "total": 0}
        self.assertEqual(data, exp)

        create_project(self.session)

        output = self.app.get('/api/projects/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        for key in range(len(data['projects'])):
            del(data['projects'][key]['created_on'])
            del(data['projects'][key]['updated_on'])

        exp = {
            "projects": [
                {
                    "backend": "custom",
                    "homepage": "http://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://www.geany.org/Download/Releases"
                },
                {
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None
                },
                {
                    "backend": "custom",
                    "homepage": "http://subsurface.hohndel.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://subsurface.hohndel.org/downloads/"
                }
            ],
            "total": 3
        }

        self.assertEqual(data, exp)

        output = self.app.get('/api/projects/?pattern=ge')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        for key in range(len(data['projects'])):
            del(data['projects'][key]['created_on'])
            del(data['projects'][key]['updated_on'])

        exp = {
            "projects": [
                {
                    "backend": "custom",
                    "homepage": "http://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://www.geany.org/Download/Releases"
                },
            ],
            "total": 1
        }
        self.assertEqual(data, exp)

    def test_api_projects_list(self):
        """ Test the api_projects_list function of the API. """
        create_distro(self.session)
        output = self.app.get('/api/projects/wiki/')
        self.assertEqual(output.status_code, 200)

        self.assertEqual(output.data, '')

        create_project(self.session)
        create_package(self.session)

        output = self.app.get('/api/projects/wiki/')
        self.assertEqual(output.status_code, 200)

        exp = "* geany DEFAULT http://www.geany.org/Download/Releases\n"\
            "* subsurface DEFAULT http://subsurface.hohndel.org/downloads/"
        self.assertEqual(output.data, exp)

    def test_api_projects_names(self):
        """ Test the api_projects_names function of the API. """
        create_distro(self.session)
        output = self.app.get('/api/projects/names')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        exp = {"projects": [], "total": 0}
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        output = self.app.get('/api/projects/names/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        exp = {
            "projects": [
                "geany",
                "R2spec",
                "subsurface"
            ],
            "total": 3
        }
        self.assertEqual(data, exp)

        output = self.app.get('/api/projects/names/?pattern=ge')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        exp = {
            "projects": [
                "geany"
            ],
            "total": 1
        }
        self.assertEqual(data, exp)

    def test_api_get_version(self):
        """ Test the api_get_version function of the API. """
        create_distro(self.session)
        output = self.app.post('/api/version')
        self.assertEqual(output.status_code, 301)

        output = self.app.post('/api/version/')
        self.assertEqual(output.status_code, 400)
        data = json.loads(output.data)

        exp = {"error": ["No project id specified"], "output": "notok"}
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        data = {'id': 10}
        output = self.app.post('/api/version/', data=data)
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)

        exp = {"error": "No such project", "output": "notok"}
        self.assertEqual(data, exp)

        # Modify the project so that it fails
        project = model.Project.get(self.session, 1)
        project.version_url = "http://www.geany.org/Down"
        self.session.add(project)
        self.session.commit()

        data = {'id': 1}
        output = self.app.post('/api/version/', data=data)
        self.assertEqual(output.status_code, 400)
        data = json.loads(output.data)

        exp = {
            "error": [
                "geany: no upstream version found. "
                "- http://www.geany.org/Down - "
                " geany[-_]([^-/_\\s]+?)(?i)(?:[-_](?:src|source))?"
                "\\.(?:tar|t[bglx]z|tbz2|zip)"
            ],
            "output": "notok"
        }

        # This test will break for every update of geany, so we need to
        # keep the output easy on hand.
        #print output.data
        self.assertEqual(data, exp)

        # Modify it back:
        project.version_url = "http://www.geany.org/Download/Releases"
        self.session.add(project)
        self.session.commit()

        data = {'id': 1}
        output = self.app.post('/api/version/', data=data)
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        del(data['created_on'])
        del(data['updated_on'])

        exp = {
            "backend": "custom",
            "homepage": "http://www.geany.org/",
            "name": "geany",
            "regex": "DEFAULT",
            "version": "1.24.1",
            "version_url": "http://www.geany.org/Download/Releases"
        }
        # This test will break for every update of geany, so we need to
        # keep the output easy on hand.
        #print output.data
        self.assertEqual(data, exp)

    def test_api_get_project(self):
        """ Test the api_get_project function of the API. """
        create_distro(self.session)
        output = self.app.get('/api/project/')
        self.assertEqual(output.status_code, 404)

        output = self.app.get('/api/project/10')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)

        exp = {"error": "no such project", "output": "notok"}
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        output = self.app.get('/api/project/10')
        self.assertEqual(output.status_code, 404)

        output = self.app.get('/api/project/1')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        del(data['created_on'])
        del(data['updated_on'])

        exp = {
            "backend": "custom",
            "homepage": "http://www.geany.org/",
            "name": "geany",
            "regex": 'DEFAULT',
            "version": None,
            "version_url": 'http://www.geany.org/Download/Releases',
        }

        self.assertEqual(exp, data)

    def test_api_get_project_distro(self):
        """ Test the api_get_project_distro function of the API. """
        create_distro(self.session)
        output = self.app.get('/api/project/Fedora/geany')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)

        exp = {
            "error": "No package \"geany\" found in distro \"Fedora\"",
            "output": "notok"
        }
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        output = self.app.get('/api/project/Fedora/gnome-terminal/')
        self.assertEqual(output.status_code, 404)
        data = json.loads(output.data)

        exp = {
            "error": "No package \"gnome-terminal\" found in distro "
                     "\"Fedora\"",
            "output": "notok"
        }
        self.assertEqual(data, exp)

        output = self.app.get('/api/project/Fedora/geany/')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        del(data['created_on'])
        del(data['updated_on'])

        exp = {
            "backend": "custom",
            "homepage": "http://www.geany.org/",
            "name": "geany",
            "regex": 'DEFAULT',
            "version": None,
            "version_url": 'http://www.geany.org/Download/Releases',
        }
        self.assertEqual(data, exp)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(AnityaWebAPItests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
