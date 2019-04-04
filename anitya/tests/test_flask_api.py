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

"""
anitya tests for the flask API.
"""

import json
import unittest

from anitya.db import models
from anitya.lib.backends import REGEX
from anitya.tests.base import (
    DatabaseTestCase,
    create_distro,
    create_project,
    create_package,
    create_ecosystem_projects,
)


# Py3 compatibility: UTF-8 decoding and JSON decoding may be separate steps
def _read_json(output):
    return json.loads(output.get_data(as_text=True))


class AnityaWebAPItests(DatabaseTestCase):
    """ Flask API tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(AnityaWebAPItests, self).setUp()

        self.flask_app.config["TESTING"] = True
        self.app = self.flask_app.test_client()

    def test_api_docs_no_slash(self):
        """Assert the legacy /api endpoint redirects to docs."""
        output = self.app.get("/api")
        self.assertEqual(302, output.status_code)
        self.assertEqual(
            "http://localhost/static/docs/api.html", output.headers["Location"]
        )

    def test_api_docs_with_slash(self):
        """Assert the legacy /api/ endpoint redirects to docs."""
        output = self.app.get("/api/")
        self.assertEqual(302, output.status_code)
        self.assertEqual(
            "http://localhost/static/docs/api.html", output.headers["Location"]
        )

    def test_api_projects(self):
        """ Test the api_projects function of the API. """
        create_distro(self.session)

        output = self.app.get("/api/projects")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {"projects": [], "total": 0}
        self.assertEqual(data, exp)

        create_project(self.session)

        output = self.app.get("/api/projects/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for key in range(len(data["projects"])):
            del data["projects"][key]["created_on"]
            del data["projects"][key]["updated_on"]

        exp = {
            "projects": [
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "https://www.geany.org/",
                    "ecosystem": "https://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://www.geany.org/Download/Releases",
                    "versions": [],
                },
                {
                    "id": 3,
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "ecosystem": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": [],
                },
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "https://subsurface-divelog.org/",
                    "ecosystem": "https://subsurface-divelog.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://subsurface-divelog.org/downloads/",
                    "versions": [],
                },
            ],
            "total": 3,
        }

        self.assertEqual(data, exp)

        output = self.app.get("/api/projects/?pattern=ge")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for key in range(len(data["projects"])):
            del data["projects"][key]["created_on"]
            del data["projects"][key]["updated_on"]

        exp = {
            "projects": [
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "https://www.geany.org/",
                    "ecosystem": "https://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://www.geany.org/Download/Releases",
                    "versions": [],
                }
            ],
            "total": 1,
        }

        self.assertEqual(data, exp)

        output = self.app.get("/api/projects/?homepage=https://www.geany.org/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for key in range(len(data["projects"])):
            del data["projects"][key]["created_on"]
            del data["projects"][key]["updated_on"]

        exp = {
            "projects": [
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "https://www.geany.org/",
                    "ecosystem": "https://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://www.geany.org/Download/Releases",
                    "versions": [],
                }
            ],
            "total": 1,
        }

        self.assertEqual(data, exp)

        output = self.app.get("/api/projects/?pattern=foo&homepage=bar")
        self.assertEqual(output.status_code, 400)

    def test_api_packages_wiki_list(self):
        """ Test the api_packages_wiki_list function of the API. """
        create_distro(self.session)
        output = self.app.get("/api/packages/wiki/")
        self.assertEqual(output.status_code, 200)

        self.assertEqual(output.data, b"")

        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/api/packages/wiki/")
        self.assertEqual(output.status_code, 200)

        exp = (
            b"* geany DEFAULT https://www.geany.org/Download/Releases\n"
            b"* subsurface DEFAULT https://subsurface-divelog.org/downloads/"
        )
        self.assertEqual(output.data, exp)

    def test_api_projects_names(self):
        """ Test the api_projects_names function of the API. """
        create_distro(self.session)
        output = self.app.get("/api/projects/names")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {"projects": [], "total": 0}
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/api/projects/names/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {"projects": ["geany", "R2spec", "subsurface"], "total": 3}
        self.assertEqual(data, exp)

        output = self.app.get("/api/projects/names/?pattern=ge")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {"projects": ["geany"], "total": 1}
        self.assertEqual(data, exp)

    def test_api_get_version(self):
        """ Test the api_get_version function of the API. """
        create_distro(self.session)

        output = self.app.post("/api/version/get")
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        exp = {"error": ["No project id specified"], "output": "notok"}
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        data = {"id": 10}
        output = self.app.post("/api/version/get", data=data)
        self.assertEqual(output.status_code, 404)
        data = _read_json(output)

        exp = {"error": "No such project", "output": "notok"}
        self.assertEqual(data, exp)

        # Modify the project so that it fails
        project = models.Project.get(self.session, 1)
        project.version_url = "https://www.geany.org/Down"
        self.session.add(project)
        self.session.commit()

        data = {"id": 1}
        output = self.app.post("/api/version/get", data=data)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        exp = {
            "error": [
                "geany: no upstream version found. "
                "- https://www.geany.org/Down - "
                " " + REGEX % ({"name": "geany"})
            ],
            "output": "notok",
        }

        self.assertEqual(data, exp)

        # Modify it back:
        project.version_url = "https://www.geany.org/Download/Releases"
        self.session.add(project)
        self.session.commit()

        data = {"id": 1}
        output = self.app.post("/api/version/get", data=data)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)
        del data["created_on"]
        del data["updated_on"]

        exp = {
            "id": 1,
            "backend": "custom",
            "homepage": "https://www.geany.org/",
            "ecosystem": "https://www.geany.org/",
            "name": "geany",
            "regex": "DEFAULT",
            "version": "1.33",
            "version_url": "https://www.geany.org/Download/Releases",
            "versions": ["1.33"],
            "packages": [{"distro": "Fedora", "package_name": "geany"}],
        }

        self.assertEqual(data, exp)

    def test_api_get_project(self):
        """ Test the api_get_project function of the API. """
        create_distro(self.session)
        output = self.app.get("/api/project/")
        self.assertEqual(output.status_code, 404)

        output = self.app.get("/api/project/10")
        self.assertEqual(output.status_code, 404)
        data = _read_json(output)

        exp = {"error": "no such project", "output": "notok"}
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/api/project/10")
        self.assertEqual(output.status_code, 404)

        output = self.app.get("/api/project/1")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        del data["created_on"]
        del data["updated_on"]

        exp = {
            "id": 1,
            "backend": "custom",
            "homepage": "https://www.geany.org/",
            "ecosystem": "https://www.geany.org/",
            "name": "geany",
            "regex": "DEFAULT",
            "version": None,
            "version_url": "https://www.geany.org/Download/Releases",
            "versions": [],
            "packages": [{"distro": "Fedora", "package_name": "geany"}],
        }

        self.assertEqual(exp, data)

    def test_api_get_project_distro(self):
        """ Test the api_get_project_distro function of the API. """
        create_distro(self.session)
        output = self.app.get("/api/project/Fedora/geany")
        self.assertEqual(output.status_code, 404)
        data = _read_json(output)

        exp = {
            "error": 'No package "geany" found in distro "Fedora"',
            "output": "notok",
        }
        self.assertEqual(data, exp)

        create_project(self.session)
        create_package(self.session)

        output = self.app.get("/api/project/Fedora/gnome-terminal/")
        self.assertEqual(output.status_code, 404)
        data = _read_json(output)

        exp = {
            "error": 'No package "gnome-terminal" found in distro ' '"Fedora"',
            "output": "notok",
        }
        self.assertEqual(data, exp)

        output = self.app.get("/api/project/Fedora/geany/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        del data["created_on"]
        del data["updated_on"]

        exp = {
            "id": 1,
            "backend": "custom",
            "homepage": "https://www.geany.org/",
            "ecosystem": "https://www.geany.org/",
            "name": "geany",
            "regex": "DEFAULT",
            "version": None,
            "version_url": "https://www.geany.org/Download/Releases",
            "versions": [],
            "packages": [{"distro": "Fedora", "package_name": "geany"}],
        }

        self.assertEqual(data, exp)

    def test_api_get_project_by_ecosystem(self):
        """ Test the api_get_project_ecosystem function of the API. """
        create_distro(self.session)
        output = self.app.get("/api/by_ecosystem/pypi/pypi_and_npm")
        self.assertEqual(output.status_code, 404)
        data = _read_json(output)

        exp = {
            "error": 'No project "pypi_and_npm" found in ecosystem "pypi"',
            "output": "notok",
        }
        self.assertEqual(data, exp)

        create_ecosystem_projects(self.session)

        output = self.app.get("/api/by_ecosystem/pypi/not-a-project")
        self.assertEqual(output.status_code, 404)
        data = _read_json(output)

        exp = {
            "error": 'No project "not-a-project" found in ecosystem "pypi"',
            "output": "notok",
        }
        self.assertEqual(data, exp)

        output = self.app.get("/api/by_ecosystem/pypi/pypi_and_npm")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        del data["created_on"]
        del data["updated_on"]

        exp = {
            "id": 1,
            "backend": "PyPI",
            "homepage": "https://example.com/not-a-real-pypi-project",
            "ecosystem": "pypi",
            "name": "pypi_and_npm",
            "regex": None,
            "version": None,
            "version_url": None,
            "versions": [],
            "packages": [],
        }

        self.assertEqual(data, exp)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(AnityaWebAPItests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
