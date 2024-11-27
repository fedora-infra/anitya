# -*- coding: utf-8 -*-
#
# Copyright © 2019  Red Hat, Inc.
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
Tests for the Flask MethodView based v2 API
"""
from __future__ import unicode_literals

import json
from unittest import mock

import anitya_schema
from fedora_messaging import testing as fml_testing

from anitya.db import Session, models
from anitya.lib import exceptions

from .base import DatabaseTestCase, create_project


# Py3 compatibility: UTF-8 decoding and JSON decoding may be separate steps
def _read_json(output):
    return json.loads(output.get_data(as_text=True))


class PackagesResourceGetTests(DatabaseTestCase):
    """Tests for HTTP GET on the ``api/v2/packages/`` resource."""

    def setUp(self):
        super().setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")

        session.add(self.user)
        self.api_token = models.ApiToken(user=self.user)
        fedora = models.Distro("Fedora")
        debian = models.Distro("Debian")
        jcline_linux = models.Distro("jcline linux")
        session.add_all([self.api_token, fedora, debian, jcline_linux])
        session.commit()

    def test_no_packages(self):
        """Assert querying packages works, even if there are no packages."""
        output = self.app.get("/api/v2/packages/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"page": 1, "items_per_page": 25, "total_items": 0, "items": []}
        )

    def test_authenticated(self):
        """Assert the API works when authenticated."""
        output = self.app.get(
            "/api/v2/packages/",
            headers={"Authorization": "Token " + self.api_token.token},
        )
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"page": 1, "items_per_page": 25, "total_items": 0, "items": []}
        )

    def test_packages(self):
        """Assert packages are returned when they exist."""
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1",
        )
        fedora_package = models.Packages(
            distro_name="Fedora", project=project, package_name="python-requests"
        )
        debian_package = models.Packages(
            distro_name="Debian", project=project, package_name="python-requests"
        )
        jcline_package = models.Packages(
            distro_name="jcline linux", project=project, package_name="requests"
        )
        version = models.ProjectVersion(project=project, version="1")
        Session.add_all(
            [project, fedora_package, debian_package, jcline_package, version]
        )
        Session.commit()

        output = self.app.get("/api/v2/packages/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 3,
            "items": [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": "1",
                },
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": "1",
                },
                {
                    "distribution": "jcline linux",
                    "name": "requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": "1",
                },
            ],
        }

        self.assertEqual(data, exp)

    def test_filter_packages_by_name(self):
        """Assert filtering packages by name works."""
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1",
        )
        fedora_package = models.Packages(
            distro_name="Fedora", project=project, package_name="python-requests"
        )
        debian_package = models.Packages(
            distro_name="Debian", project=project, package_name="python-requests"
        )
        jcline_package = models.Packages(
            distro_name="jcline linux", project=project, package_name="requests"
        )
        Session.add_all([project, fedora_package, debian_package, jcline_package])
        Session.commit()

        output = self.app.get("/api/v2/packages/?name=python-requests")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 2,
            "items": [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                },
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                },
            ],
        }

        self.assertEqual(data, exp)

    def test_filter_packages_by_name_case_insensitive(self):
        """Assert filtering packages by case insensitive name works."""
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1",
        )
        fedora_package = models.Packages(
            distro_name="Fedora", project=project, package_name="python-requests"
        )
        debian_package = models.Packages(
            distro_name="Debian", project=project, package_name="python-requests"
        )
        jcline_package = models.Packages(
            distro_name="jcline linux", project=project, package_name="requests"
        )
        Session.add_all([project, fedora_package, debian_package, jcline_package])
        Session.commit()

        output = self.app.get("/api/v2/packages/?name=Python-requests")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 2,
            "items": [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                },
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                },
            ],
        }

        self.assertEqual(data, exp)

    def test_list_packages_items_per_page_no_items(self):
        """Assert pagination works and page size is adjustable."""
        api_endpoint = "/api/v2/packages/?items_per_page=1"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"page": 1, "items_per_page": 1, "total_items": 0, "items": []}
        )

    def test_list_packages_items_per_page(self):
        """Assert pagination works and page size is adjustable."""
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1",
        )
        fedora_package = models.Packages(
            distro_name="Fedora", project=project, package_name="python-requests"
        )
        debian_package = models.Packages(
            distro_name="Debian", project=project, package_name="python-requests"
        )
        Session.add_all([project, fedora_package, debian_package])
        Session.commit()
        output = self.app.get("/api/v2/packages/?items_per_page=1")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            "page": 1,
            "items_per_page": 1,
            "total_items": 2,
            "items": [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                }
            ],
        }

        self.assertEqual(data, exp)

    def test_list_packages_items_per_page_with_page(self):
        """Assert retrieving other pages works."""
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1",
        )
        fedora_package = models.Packages(
            distro_name="Fedora", project=project, package_name="python-requests"
        )
        debian_package = models.Packages(
            distro_name="Debian", project=project, package_name="python-requests"
        )
        Session.add_all([project, fedora_package, debian_package])
        Session.commit()
        output = self.app.get("/api/v2/packages/?items_per_page=1&page=2")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            "page": 2,
            "items_per_page": 1,
            "total_items": 2,
            "items": [
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                }
            ],
        }

        self.assertEqual(data, exp)

    def test_filter_distribution(self):
        """Assert retrieving other pages works."""
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1",
        )
        fedora_package = models.Packages(
            distro_name="Fedora", project=project, package_name="python-requests"
        )
        debian_package = models.Packages(
            distro_name="Debian", project=project, package_name="python-requests"
        )
        Session.add_all([project, fedora_package, debian_package])
        Session.commit()
        fedora = self.app.get("/api/v2/packages/?distribution=Fedora")
        debian = self.app.get("/api/v2/packages/?distribution=Debian")
        self.assertEqual(fedora.status_code, 200)
        self.assertEqual(debian.status_code, 200)
        fedora_data = _read_json(fedora)
        debian_data = _read_json(debian)

        fedora_exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 1,
            "items": [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                }
            ],
        }
        debian_exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 1,
            "items": [
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi",
                    "version": "1",
                    "stable_version": None,
                }
            ],
        }

        self.assertEqual(fedora_data, fedora_exp)
        self.assertEqual(debian_data, debian_exp)

    def test_list_packages_items_per_page_too_big(self):
        """Assert unreasonably large items per page results in an error."""
        api_endpoint = "/api/v2/packages/?items_per_page=500"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {"message": {"items_per_page": "Value must be less than or equal to 250."}},
        )

    def test_list_packages_items_per_page_negative(self):
        """Assert a negative value for items_per_page results in an error."""
        api_endpoint = "/api/v2/packages/?items_per_page=-25"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {
                "message": {
                    "items_per_page": "Value must be greater than or equal to 1."
                }
            },
        )

    def test_list_packages_items_per_page_non_integer(self):
        """Assert a non-integer for items_per_page results in an error."""
        api_endpoint = "/api/v2/packages/?items_per_page=twenty"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {"message": {"items_per_page": "Not a valid integer."}},
        )

    def test_list_packages_page_negative(self):
        """Assert a negative value for a page results in an error."""
        api_endpoint = "/api/v2/packages/?page=-25"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {"message": {"page": "Value must be greater than or equal to 1."}}
        )

    def test_list_packages_page_non_integer(self):
        """Assert a non-integer value for a page results in an error."""
        api_endpoint = "/api/v2/packages/?page=twenty"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {"message": {"page": "Not a valid integer."}},
        )


class PackagesResourcePostTests(DatabaseTestCase):
    """PackagesResourcePostTests"""

    def setUp(self):
        super().setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")

        session.add(self.user)
        self.api_token = models.ApiToken(user=self.user)
        self.project = models.Project(
            name="requests", homepage="https://pypi.io/project/requests", backend="PyPI"
        )
        self.fedora = models.Distro("Fedora")
        session.add_all([self.api_token, self.project, self.fedora])
        session.commit()

        self.auth = {"Authorization": "Token " + self.api_token.token}

    def test_unauthenticated(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post("/api/v2/packages/")

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_token(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post(
            "/api/v2/packages/", headers={"Authorization": "Token eh"}
        )

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_auth_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post(
            "/api/v2/packages/",
            headers={"Authorization": "Basic " + self.api_token.token},
        )

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_no_token_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post(
            "/api/v2/packages/", headers={"Authorization": "pleaseletmein"}
        )

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_request(self):
        """Assert invalid requests result in a helpful HTTP 400."""
        output = self.app.post("/api/v2/packages/", headers=self.auth)

        self.assertEqual(output.status_code, 400)
        # Error details should report the missing required fields
        data = _read_json(output)
        error_details = data["message"]
        self.assertIn("distribution", error_details)
        self.assertIn("package_name", error_details)
        self.assertIn("project_name", error_details)
        self.assertIn("project_ecosystem", error_details)

    @mock.patch("anitya.lib.utilities.publish_message")
    def test_valid_request(self, mock_publish):
        """Assert packages can be created."""
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        output = self.app.post(
            "/api/v2/packages/", headers=self.auth, data=request_data
        )
        self.assertEqual(output.status_code, 201)
        data = _read_json(output)
        self.assertEqual({"distribution": "Fedora", "name": "python-requests"}, data)

        project = models.Project.query.filter_by(
            name="requests", ecosystem_name="pypi"
        ).one()

        project = dict(project.__json__())
        distro = {"name": "Fedora"}
        message = {
            "agent": "user@fedoraproject.org",
            "project": "requests",
            "distro": "Fedora",
            "new": "python-requests",
        }
        mock_publish.assert_called_with(
            topic="project.map.new", project=project, distro=distro, message=message
        )

    @mock.patch("anitya.lib.utilities.publish_message")
    def test_valid_request_json(self, mock_publish):
        """Assert packages can be created with json."""
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        output = self.app.post(
            "/api/v2/packages/", headers=self.auth, json=request_data
        )
        self.assertEqual(output.status_code, 201)
        data = _read_json(output)
        self.assertEqual({"distribution": "Fedora", "name": "python-requests"}, data)

        project = models.Project.query.filter_by(
            name="requests", ecosystem_name="pypi"
        ).one()

        project = dict(project.__json__())
        distro = {"name": "Fedora"}
        message = {
            "agent": "user@fedoraproject.org",
            "project": "requests",
            "distro": "Fedora",
            "new": "python-requests",
        }
        mock_publish.assert_called_with(
            topic="project.map.new", project=project, distro=distro, message=message
        )

    def test_same_package_two_distros(self):
        """Assert packages can be created."""
        Session.add(models.Distro("Debian"))
        Session.commit()
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        with fml_testing.mock_sends(anitya_schema.ProjectMapCreated):
            output = self.app.post(
                "/api/v2/packages/", headers=self.auth, data=request_data
            )
        self.assertEqual(output.status_code, 201)

        request_data["distribution"] = "Debian"
        with fml_testing.mock_sends(anitya_schema.ProjectMapCreated):
            output = self.app.post(
                "/api/v2/packages/", headers=self.auth, data=request_data
            )
        self.assertEqual(output.status_code, 201)

    def test_conflicting_request(self):
        """Assert conflicts for packages result in HTTP 409."""
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        with fml_testing.mock_sends(anitya_schema.ProjectMapCreated):
            output = self.app.post(
                "/api/v2/packages/", headers=self.auth, data=request_data
            )
        self.assertEqual(output.status_code, 201)
        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/packages/", headers=self.auth, data=request_data
            )
        self.assertEqual(output.status_code, 409)
        # Error details should report conflicting fields.
        data = _read_json(output)
        self.assertEqual(data, {"error": "package already exists in distribution"})

    def test_missing_distro(self):
        """Assert a missing distribution results in HTTP 400."""
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Mythical Distribution",
        }

        output = self.app.post(
            "/api/v2/packages/", headers=self.auth, data=request_data
        )
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)
        self.assertEqual(
            {"error": 'Distribution "Mythical Distribution" not found'}, data
        )

    def test_missing_project(self):
        """Assert a missing project results in HTTP 400."""
        request_data = {
            "project_ecosystem": "Missing",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        output = self.app.post(
            "/api/v2/packages/", headers=self.auth, data=request_data
        )
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)
        self.assertEqual(
            {"error": 'Project "requests" in ecosystem "Missing" not found'}, data
        )


class ProjectsResourceGetTests(DatabaseTestCase):
    """ProjectsResourceGetTests"""

    def setUp(self):
        super().setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")

        session.add(self.user)
        self.api_token = models.ApiToken(user=self.user)
        session.add(self.api_token)
        session.commit()

    def test_no_projects(self):
        """Assert querying projects works, even if there are no projects."""
        output = self.app.get("/api/v2/projects/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"page": 1, "items_per_page": 25, "total_items": 0, "items": []}
        )

    def test_authenticated(self):
        """Assert the API works when authenticated."""
        output = self.app.get(
            "/api/v2/projects/",
            headers={"Authorization": "Token " + self.api_token.token},
        )
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"page": 1, "items_per_page": 25, "total_items": 0, "items": []}
        )

    def test_list_projects(self):
        """Assert projects are returned when they exist."""
        create_project(self.session)

        output = self.app.get("/api/v2/projects/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data["items"]:
            del item["created_on"]
            del item["updated_on"]

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 3,
            "items": [
                {
                    "id": 3,
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://fedorahosted.org/r2spec/",
                },
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "https://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://www.geany.org/Download/Releases",
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://www.geany.org/",
                },
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "https://subsurface-divelog.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://subsurface-divelog.org/downloads/",
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://subsurface-divelog.org/",
                },
            ],
        }

        self.assertEqual(data, exp)

    def test_list_projects_with_same_name(self):
        """Assert two projects with the same name are sorted by the ecosystem."""
        self.maxDiff = None
        session = Session()
        project1 = models.Project(
            name="zlib",
            homepage="https://hackage.haskell.org/package/zlib",
            backend="GitHub",
            ecosystem_name="https://hackage.haskell.org/package/zlib",
        )
        project2 = models.Project(
            name="zlib",
            homepage="http://www.zlib.net/",
            backend="custom",
            regex="DEFAULT",
            ecosystem_name="http://www.zlib.net/",
        )
        session.add_all([project1, project2])
        session.commit()

        output = self.app.get("/api/v2/projects/")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data["items"]:
            del item["created_on"]
            del item["updated_on"]

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 2,
            "items": [
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "http://www.zlib.net/",
                    "name": "zlib",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": None,
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "http://www.zlib.net/",
                },
                {
                    "id": 1,
                    "backend": "GitHub",
                    "homepage": "https://hackage.haskell.org/package/zlib",
                    "name": "zlib",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://hackage.haskell.org/package/zlib",
                },
            ],
        }

        self.assertEqual(data, exp)

    def test_filter_projects_by_ecosystem(self):
        """Assert projects can be filtered by ecosystem."""
        create_project(self.session)

        output = self.app.get(
            "/api/v2/projects/?ecosystem=https%3A%2F%2Fsubsurface-divelog.org%2F"
        )
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data["items"]:
            del item["created_on"]
            del item["updated_on"]

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 1,
            "items": [
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "https://subsurface-divelog.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://subsurface-divelog.org/downloads/",
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://subsurface-divelog.org/",
                }
            ],
        }

        self.assertEqual(data, exp)

    def test_filter_projects_by_name(self):
        """Assert projects can be filtered by name."""
        create_project(self.session)

        output = self.app.get("/api/v2/projects/?name=subsurface")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data["items"]:
            del item["created_on"]
            del item["updated_on"]

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 1,
            "items": [
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "https://subsurface-divelog.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://subsurface-divelog.org/downloads/",
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://subsurface-divelog.org/",
                }
            ],
        }

        self.assertEqual(data, exp)

    def test_filter_projects_by_name_case_insensitive(self):
        """Assert projects can be filtered by name case insensitive."""
        create_project(self.session)

        output = self.app.get("/api/v2/projects/?name=SubSurface")
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data["items"]:
            del item["created_on"]
            del item["updated_on"]

        exp = {
            "page": 1,
            "items_per_page": 25,
            "total_items": 1,
            "items": [
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "https://subsurface-divelog.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://subsurface-divelog.org/downloads/",
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://subsurface-divelog.org/",
                }
            ],
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page(self):
        """Assert pagination works and page size is adjustable."""
        api_endpoint = "/api/v2/projects/?items_per_page=1"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"page": 1, "items_per_page": 1, "total_items": 0, "items": []}
        )

        create_project(self.session)

        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data["items"]:
            del item["created_on"]
            del item["updated_on"]

        exp = {
            "page": 1,
            "items_per_page": 1,
            "total_items": 3,
            "items": [
                {
                    "id": 3,
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://fedorahosted.org/r2spec/",
                }
            ],
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page_with_page(self):
        """Assert retrieving other pages works."""
        api_endpoint = "/api/v2/projects/?items_per_page=1&page=2"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"page": 2, "items_per_page": 1, "total_items": 0, "items": []}
        )

        create_project(self.session)

        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data["items"]:
            del item["created_on"]
            del item["updated_on"]

        exp = {
            "page": 2,
            "items_per_page": 1,
            "total_items": 3,
            "items": [
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "https://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "https://www.geany.org/Download/Releases",
                    "versions": [],
                    "stable_versions": [],
                    "ecosystem": "https://www.geany.org/",
                }
            ],
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page_too_big(self):
        """Assert unreasonably large items per page results in an error."""
        api_endpoint = "/api/v2/projects/?items_per_page=500"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {"message": {"items_per_page": "Value must be less than or equal to 250."}},
        )

    def test_list_projects_items_per_page_negative(self):
        """Assert a negative value for items_per_page results in an error."""
        api_endpoint = "/api/v2/projects/?items_per_page=-25"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {
                "message": {
                    "items_per_page": "Value must be greater than or equal to 1."
                }
            },
        )

    def test_list_projects_items_per_page_non_integer(self):
        """Assert a non-integer for items_per_page results in an error."""
        api_endpoint = "/api/v2/projects/?items_per_page=twenty"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {"message": {"items_per_page": "Not a valid integer."}},
        )

    def test_list_projects_page_negative(self):
        """Assert a negative value for a page results in an error."""
        api_endpoint = "/api/v2/projects/?page=-25"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {"message": {"page": "Value must be greater than or equal to 1."}}
        )

    def test_list_projects_page_non_integer(self):
        """Assert a non-integer value for a page results in an error."""
        api_endpoint = "/api/v2/projects/?page=twenty"
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {"message": {"page": "Not a valid integer."}},
        )


class ProjectsResourcePostTests(DatabaseTestCase):
    """ProjectsResourcePostTests"""

    def setUp(self):
        super().setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")

        session.add(self.user)
        self.api_token = models.ApiToken(user=self.user)
        session.add(self.api_token)
        session.commit()

        self.auth = {
            "Authorization": "Token " + self.api_token.token,
        }

    def test_unauthenticated(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post("/api/v2/projects/")

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_token(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post(
            "/api/v2/projects/", headers={"Authorization": "Token eh"}
        )

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_auth_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post(
            "/api/v2/projects/",
            headers={"Authorization": "Basic " + self.api_token.token},
        )

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_request(self):
        """Assert invalid requests result in a helpful HTTP 400."""
        output = self.app.post("/api/v2/projects/", headers=self.auth)

        self.assertEqual(output.status_code, 400)
        # Error details should report the missing required fields
        data = _read_json(output)
        error_details = data["message"]
        self.assertIn("backend", error_details)
        self.assertIn("homepage", error_details)
        self.assertIn("name", error_details)

    def test_conflicting_request(self):
        """Test conflicting request"""
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }

        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            output = self.app.post(
                "/api/v2/projects/", headers=self.auth, data=request_data
            )
        self.assertEqual(output.status_code, 201)
        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/projects/", headers=self.auth, data=request_data
            )
        self.assertEqual(output.status_code, 409)
        # Error details should report conflicting fields.
        data = _read_json(output)
        self.assertIn("requested_project", data)
        self.assertEqual("PyPI", data["requested_project"]["backend"])
        self.assertEqual(
            "http://python-requests.org", data["requested_project"]["homepage"]
        )
        self.assertEqual("requests", data["requested_project"]["name"])

    def test_valid_request(self):
        """Test valid request"""
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }

        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            output = self.app.post(
                "/api/v2/projects/", headers=self.auth, data=request_data
            )

        data = _read_json(output)
        self.assertEqual(output.status_code, 201)
        self.assertIn("backend", data)
        self.assertIn("homepage", data)
        self.assertIn("name", data)
        self.assertEqual("PyPI", data["backend"])
        self.assertEqual("http://python-requests.org", data["homepage"])
        self.assertEqual("requests", data["name"])

    def test_valid_request_json(self):
        """
        Assert that request with header specifying json will be handled as well.
        """
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }

        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            output = self.app.post(
                "/api/v2/projects/",
                headers=self.auth,
                json=request_data,
            )

        data = _read_json(output)
        self.assertEqual(output.status_code, 201)
        self.assertIn("backend", data)
        self.assertIn("homepage", data)
        self.assertIn("name", data)
        self.assertEqual("PyPI", data["backend"])
        self.assertEqual("http://python-requests.org", data["homepage"])
        self.assertEqual("requests", data["name"])

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_check_release(self, mock_check):
        """
        Assert that check_project_release is called whe check_release
        parameter is provided.
        """
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
            "check_release": "True",
        }

        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            output = self.app.post(
                "/api/v2/projects/", headers=self.auth, data=request_data
            )

        mock_check.assert_called_once_with(mock.ANY, mock.ANY)
        self.assertEqual(output.status_code, 201)

    @mock.patch("anitya.lib.utilities.check_project_release")
    @mock.patch("anitya.api_v2._log")
    def test_check_release_exception(self, mock_log, mock_check):
        """
        Assert that exception thrown in check_project release is correctly handled.
        """
        mock_check.side_effect = exceptions.AnityaPluginException("Error")
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
            "check_release": "True",
        }

        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            output = self.app.post(
                "/api/v2/projects/", headers=self.auth, data=request_data
            )

        mock_check.assert_called_once_with(mock.ANY, mock.ANY)
        self.assertEqual(output.status_code, 201)
        self.assertIn("Error", mock_log.error.call_args_list[0][0])


class VersionsResourceGetTests(DatabaseTestCase):
    """Tests for ``api/v2/versions/`` API endpooint - GET method."""

    def setUp(self):
        super().setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")

        session.add(self.user)
        self.api_token = models.ApiToken(user=self.user)
        session.add(self.api_token)
        session.commit()

    def test_no_project(self):
        """Assert querying versions when project doesn't exists returns error."""
        output = self.app.get("/api/v2/versions/?project_id=1")
        self.assertEqual(output.status_code, 404)
        data = _read_json(output)

        self.assertEqual(data, {"output": "notok", "error": "No such project"})

    def test_authenticated(self):
        """Assert the API works when authenticated."""
        project = models.Project(
            name="requests", homepage="https://pypi.io/project/requests", backend="PyPI"
        )
        self.session.add(project)
        self.session.commit()
        output = self.app.get(
            "/api/v2/versions/?project_id=" + str(project.id),
            headers={"Authorization": "Token " + self.api_token.token},
        )
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(
            data, {"latest_version": None, "versions": [], "stable_versions": []}
        )

    def test_list_versions(self):
        """Assert versions are returned when they exist."""
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1.0.0",
        )
        self.session.add(project)
        self.session.commit()

        version = models.ProjectVersion(project=project, version="1.0.0")
        self.session.add(version)

        version = models.ProjectVersion(project=project, version="0.9.9")
        self.session.add(version)
        self.session.commit()

        output = self.app.get("/api/v2/versions/?project_id=" + str(project.id))
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            "latest_version": "1.0.0",
            "versions": ["1.0.0", "0.9.9"],
            "stable_versions": ["1.0.0", "0.9.9"],
        }

        self.assertEqual(data, exp)

    def test_list_versions_prefix(self):
        """
        Assert versions are returned when they exist without prefx.
        Test for https://github.com/fedora-infra/anitya/issues/1026
        """
        project = models.Project(
            name="requests",
            homepage="https://pypi.io/project/requests",
            backend="PyPI",
            latest_version="1.0.0",
            version_prefix="test-",
        )
        self.session.add(project)
        self.session.commit()

        version = models.ProjectVersion(project=project, version="test-1.0.0")
        self.session.add(version)

        version = models.ProjectVersion(project=project, version="test-0.9.9")
        self.session.add(version)
        self.session.commit()

        output = self.app.get("/api/v2/versions/?project_id=" + str(project.id))
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            "latest_version": "1.0.0",
            "versions": ["1.0.0", "0.9.9"],
            "stable_versions": ["1.0.0", "0.9.9"],
        }

        self.assertEqual(data, exp)


class VersionsResourcePostTests(DatabaseTestCase):
    """VersionsResourcePostTests"""

    def setUp(self):
        super().setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")

        session.add(self.user)
        self.api_token = models.ApiToken(user=self.user)
        session.add(self.api_token)
        session.commit()

        self.auth = {"Authorization": "Token " + self.api_token.token}

    def test_unauthenticated(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post("/api/v2/versions/")

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_token(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post(
            "/api/v2/versions/", headers={"Authorization": "Token eh"}
        )

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_auth_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }

        output = self.app.post(
            "/api/v2/versions/",
            headers={"Authorization": "Basic " + self.api_token.token},
        )

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual("Token", output.headers["WWW-Authenticate"])

    def test_invalid_request(self):
        """Assert invalid requests result in a helpful HTTP 400."""
        output = self.app.post("/api/v2/versions/", headers=self.auth)

        self.assertEqual(output.status_code, 400)
        # Error details should report the missing required fields
        data = _read_json(output)
        self.assertIn("backend", data)
        self.assertIn("homepage", data)
        self.assertIn("name", data)

    def test_no_project_id(self):
        """Assert no project found when id provided result in HTTP 404."""
        request_data = {
            "id": 1,
        }

        output = self.app.post(
            "/api/v2/versions/", headers=self.auth, data=request_data
        )

        data = _read_json(output)
        self.assertEqual(output.status_code, 404)
        self.assertEqual("No such project", data)

    def test_multiple_projects_found(self):
        """
        Assert that finding multiple projects results in HTTP 400.
        """
        project = models.Project(
            name="requests", homepage="https://requests.com", backend="custom"
        )
        self.session.add(project)

        project = models.Project(
            name="requests", homepage="https://requests2.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()

        request_data = {
            "name": "requests",
        }

        output = self.app.post(
            "/api/v2/versions/", headers=self.auth, data=request_data
        )

        data = _read_json(output)
        self.assertEqual(output.status_code, 400)
        self.assertEqual(data, "More than one project found")

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_one_project_found(self, mock_check):
        """
        Assert that finding one project will not result in error.
        """
        project = models.Project(
            name="requests", homepage="https://requests.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()

        mock_check.return_value = ["1.0.0", "0.9.9"]
        request_data = {
            "name": "requests",
        }

        output = self.app.post(
            "/api/v2/versions/", headers=self.auth, data=request_data
        )

        data = _read_json(output)
        exp = {
            "latest_version": None,
            "found_versions": ["1.0.0", "0.9.9"],
            "versions": [],
            "stable_versions": [],
        }
        self.assertEqual(data, exp)

        mock_check.assert_called_once_with(mock.ANY, mock.ANY, test=True)
        self.assertEqual(output.status_code, 200)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_one_project_found_json(self, mock_check):
        """
        Assert that sending json request works correctly.
        """
        project = models.Project(
            name="requests", homepage="https://requests.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()

        mock_check.return_value = ["1.0.0", "0.9.9"]
        request_data = {
            "name": "requests",
        }

        output = self.app.post(
            "/api/v2/versions/", headers=self.auth, json=request_data
        )

        data = _read_json(output)
        exp = {
            "latest_version": None,
            "found_versions": ["1.0.0", "0.9.9"],
            "versions": [],
            "stable_versions": [],
        }
        self.assertEqual(data, exp)

        mock_check.assert_called_once_with(mock.ANY, mock.ANY, test=True)
        self.assertEqual(output.status_code, 200)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_no_project(self, mock_check):
        """
        Assert that temporary project is created when no project is found.
        """
        mock_check.return_value = ["1.0.0", "0.9.9"]
        request_data = {
            "backend": "PyPI",
            "homepage": "https://python-requests.org",
            "name": "requests",
            "dry_run": "false",
        }

        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/versions/", headers=self.auth, data=request_data
            )

        data = _read_json(output)
        exp = {
            "latest_version": None,
            "found_versions": ["1.0.0", "0.9.9"],
            "versions": [],
            "stable_versions": [],
        }
        self.assertEqual(data, exp)

        mock_check.assert_called_once_with(mock.ANY, mock.ANY, test=True)
        self.assertEqual(output.status_code, 200)

        projects = models.Project.query.all()

        self.assertEqual(len(projects), 1)
        project = projects[0]
        self.assertEqual(project.name, "requests")
        self.assertEqual(project.backend, "PyPI")
        self.assertEqual(project.homepage, "https://python-requests.org")
        self.assertEqual(project.version_url, "https://python-requests.org")
        self.assertEqual(project.version_scheme, None)
        self.assertEqual(project.version_pattern, None)
        self.assertEqual(project.version_prefix, None)
        self.assertEqual(project.pre_release_filter, None)
        self.assertEqual(project.version_filter, None)
        self.assertEqual(project.regex, None)
        self.assertFalse(project.insecure)
        self.assertFalse(project.releases_only)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_project_exists(self, mock_check):
        """
        Assert that project is edited when exists.
        """
        project = models.Project(
            name="requests", homepage="https://requests2.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()
        mock_check.return_value = ["1.0.0", "0.9.9"]
        request_data = {
            "id": project.id,
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
            "version_url": "https://dummy.org",
            "version_scheme": "calendar",
            "version_pattern": "YY-MM",
            "version_prefix": "a",
            "pre_release_filter": "alpha",
            "version_filter": "foo",
            "regex": "dummy",
            "insecure": "true",
            "releases_only": "true",
        }

        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/versions/", headers=self.auth, data=request_data
            )

        data = _read_json(output)
        exp = {
            "latest_version": None,
            "found_versions": ["1.0.0", "0.9.9"],
            "versions": [],
            "stable_versions": [],
        }
        self.assertEqual(data, exp)

        mock_check.assert_called_once_with(mock.ANY, mock.ANY, test=True)
        self.assertEqual(output.status_code, 200)

        # Check if the project was edited
        self.assertEqual(project.backend, "PyPI")
        self.assertEqual(project.homepage, "http://python-requests.org")
        self.assertEqual(project.version_url, "https://dummy.org")
        self.assertEqual(project.version_scheme, "calendar")
        self.assertEqual(project.version_pattern, "YY-MM")
        self.assertEqual(project.version_prefix, "a")
        self.assertEqual(project.pre_release_filter, "alpha")
        self.assertEqual(project.version_filter, "foo")
        self.assertEqual(project.regex, "dummy")
        self.assertTrue(project.insecure)
        self.assertTrue(project.releases_only)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_project_exists_versions(self, mock_check):
        """
        Assert that project is returned with existing versions.
        """
        project = models.Project(
            name="requests",
            homepage="https://requests2.com",
            backend="custom",
            version_prefix="test-",
        )
        self.session.add(project)
        self.session.commit()

        version = models.ProjectVersion(
            project_id=project.id, version="test-0.1.0", project=project
        )
        self.session.add(version)
        self.session.commit()

        mock_check.return_value = ["1.0.0", "0.9.9"]
        request_data = {
            "id": project.id,
        }

        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/versions/", headers=self.auth, data=request_data
            )

        data = _read_json(output)
        exp = {
            "latest_version": None,
            "found_versions": ["1.0.0", "0.9.9"],
            "versions": ["0.1.0"],
            "stable_versions": ["0.1.0"],
        }
        self.assertEqual(data, exp)

        mock_check.assert_called_once_with(mock.ANY, mock.ANY, test=True)
        self.assertEqual(output.status_code, 200)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_project_exists_no_change(self, mock_check):
        """
        Assert that project is checked when exists and no change is requested.
        """
        project = models.Project(
            name="requests", homepage="https://requests2.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()
        mock_check.return_value = ["1.0.0", "0.9.9"]
        request_data = {
            "id": project.id,
        }

        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/versions/", headers=self.auth, data=request_data
            )

        data = _read_json(output)
        exp = {
            "latest_version": None,
            "found_versions": ["1.0.0", "0.9.9"],
            "versions": [],
            "stable_versions": [],
        }
        self.assertEqual(data, exp)

        mock_check.assert_called_once_with(mock.ANY, mock.ANY, test=True)
        self.assertEqual(output.status_code, 200)

        # Check if the project was edited
        self.assertEqual(project.name, "requests")
        self.assertEqual(project.backend, "custom")
        self.assertEqual(project.homepage, "https://requests2.com")
        self.assertEqual(project.version_url, None)
        self.assertEqual(project.version_scheme, None)
        self.assertEqual(project.version_pattern, None)
        self.assertEqual(project.version_prefix, None)
        self.assertEqual(project.pre_release_filter, None)
        self.assertEqual(project.version_filter, None)
        self.assertEqual(project.regex, None)
        self.assertFalse(project.insecure)
        self.assertFalse(project.releases_only)

    @mock.patch("anitya.lib.utilities.edit_project")
    def test_project_exists_error(self, mock_edit):
        """
        Assert that edit project error is handled correctly.
        """
        project = models.Project(
            name="requests", homepage="https://requests2.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()
        mock_edit.side_effect = exceptions.AnityaException("Error")
        request_data = {
            "id": project.id,
        }

        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/versions/", headers=self.auth, data=request_data
            )

        data = _read_json(output)
        self.assertEqual(data, "Error")

        mock_edit.assert_called_once_with(
            mock.ANY,
            user_id="user@fedoraproject.org",
            project=mock.ANY,
            name="requests",
            backend="custom",
            homepage="https://requests2.com",
            version_url=None,
            version_scheme=None,
            version_pattern=None,
            version_prefix=None,
            pre_release_filter=None,
            version_filter=None,
            regex=None,
            insecure=False,
            releases_only=False,
            dry_run=True,
        )
        self.assertEqual(output.status_code, 500)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_project_check_error(self, mock_check):
        """
        Assert that check release error is handled correctly.
        """
        project = models.Project(
            name="requests", homepage="https://requests2.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()
        mock_check.side_effect = exceptions.AnityaException("Error")
        request_data = {
            "id": project.id,
        }

        with fml_testing.mock_sends():
            output = self.app.post(
                "/api/v2/versions/", headers=self.auth, data=request_data
            )

        data = _read_json(output)
        self.assertEqual(data, "Error when checking for new version: Error")

        mock_check.assert_called_once_with(mock.ANY, mock.ANY, test=True)
        self.assertEqual(output.status_code, 500)
