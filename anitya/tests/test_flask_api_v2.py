# -*- coding: utf-8 -*-
#
# Copyright © 2017  Red Hat, Inc.
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
Tests for the Flask-RESTful based v2 API
'''
from __future__ import unicode_literals

import json

from anitya.db import Session, models
from .base import (DatabaseTestCase, create_project)


# Py3 compatibility: UTF-8 decoding and JSON decoding may be separate steps
def _read_json(output):
    return json.loads(output.get_data(as_text=True))


class PackagesResourceGetTests(DatabaseTestCase):
    """Tests for HTTP GET on the ``api/v2/packages/`` resource."""

    def setUp(self):
        super(PackagesResourceGetTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.api_token = models.ApiToken(user=self.user)
        fedora = models.Distro('Fedora')
        debian = models.Distro('Debian')
        jcline_linux = models.Distro('jcline linux')
        session.add_all([self.user, self.api_token, fedora, debian, jcline_linux])
        session.commit()

    def test_no_packages(self):
        """Assert querying packages works, even if there are no packages."""
        output = self.app.get('/api/v2/packages/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 25, 'total_items': 0, 'items': []})

    def test_authenticated(self):
        """Assert the API works when authenticated."""
        output = self.app.get(
            '/api/v2/packages/', headers={'Authorization': 'Token ' + self.api_token.token})
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 25, 'total_items': 0, 'items': []})

    def test_packages(self):
        """Assert packages are returned when they exist."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.io/project/requests',
            backend='PyPI',
        )
        fedora_package = models.Packages(
            distro='Fedora', project=project, package_name='python-requests')
        debian_package = models.Packages(
            distro='Debian', project=project, package_name='python-requests')
        jcline_package = models.Packages(
            distro='jcline linux', project=project, package_name='requests')
        Session.add_all([project, fedora_package, debian_package, jcline_package])
        Session.commit()

        output = self.app.get('/api/v2/packages/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 3,
            'items': [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
                {
                    "distribution": "jcline linux",
                    "name": "requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_filter_packages_by_name(self):
        """Assert filtering packages by name works."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.io/project/requests',
            backend='PyPI',
        )
        fedora_package = models.Packages(
            distro='Fedora', project=project, package_name='python-requests')
        debian_package = models.Packages(
            distro='Debian', project=project, package_name='python-requests')
        jcline_package = models.Packages(
            distro='jcline linux', project=project, package_name='requests')
        Session.add_all([project, fedora_package, debian_package, jcline_package])
        Session.commit()

        output = self.app.get('/api/v2/packages/?name=python-requests')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 2,
            'items': [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_list_packages_items_per_page_no_items(self):
        """Assert pagination works and page size is adjustable."""
        api_endpoint = '/api/v2/packages/?items_per_page=1'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 1, 'total_items': 0, 'items': []})

    def test_list_packages_items_per_page(self):
        """Assert pagination works and page size is adjustable."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.io/project/requests',
            backend='PyPI',
        )
        fedora_package = models.Packages(
            distro='Fedora', project=project, package_name='python-requests')
        debian_package = models.Packages(
            distro='Debian', project=project, package_name='python-requests')
        Session.add_all([project, fedora_package, debian_package])
        Session.commit()
        output = self.app.get('/api/v2/packages/?items_per_page=1')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            'page': 1,
            'items_per_page': 1,
            'total_items': 2,
            'items': [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_list_packages_items_per_page_with_page(self):
        """Assert retrieving other pages works."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.io/project/requests',
            backend='PyPI',
        )
        fedora_package = models.Packages(
            distro='Fedora', project=project, package_name='python-requests')
        debian_package = models.Packages(
            distro='Debian', project=project, package_name='python-requests')
        Session.add_all([project, fedora_package, debian_package])
        Session.commit()
        output = self.app.get('/api/v2/packages/?items_per_page=1&page=2')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        exp = {
            'page': 2,
            'items_per_page': 1,
            'total_items': 2,
            'items': [
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_filter_distribution(self):
        """Assert retrieving other pages works."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.io/project/requests',
            backend='PyPI',
        )
        fedora_package = models.Packages(
            distro='Fedora', project=project, package_name='python-requests')
        debian_package = models.Packages(
            distro='Debian', project=project, package_name='python-requests')
        Session.add_all([project, fedora_package, debian_package])
        Session.commit()
        fedora = self.app.get('/api/v2/packages/?distribution=Fedora')
        debian = self.app.get('/api/v2/packages/?distribution=Debian')
        self.assertEqual(fedora.status_code, 200)
        self.assertEqual(debian.status_code, 200)
        fedora_data = _read_json(fedora)
        debian_data = _read_json(debian)

        fedora_exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 1,
            'items': [
                {
                    "distribution": "Fedora",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
            ]
        }
        debian_exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 1,
            'items': [
                {
                    "distribution": "Debian",
                    "name": "python-requests",
                    "project": "requests",
                    "ecosystem": "pypi"
                },
            ]
        }

        self.assertEqual(fedora_data, fedora_exp)
        self.assertEqual(debian_data, debian_exp)

    def test_list_packages_items_per_page_too_big(self):
        """Assert unreasonably large items per page results in an error."""
        api_endpoint = '/api/v2/packages/?items_per_page=500'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'items_per_page': u'Value must be less than or equal to 250.'}})

    def test_list_packages_items_per_page_negative(self):
        """Assert a negative value for items_per_page results in an error."""
        api_endpoint = '/api/v2/packages/?items_per_page=-25'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'items_per_page': u'Value must be greater than or equal to 1.'}})

    def test_list_packages_items_per_page_non_integer(self):
        """Assert a non-integer for items_per_page results in an error."""
        api_endpoint = '/api/v2/packages/?items_per_page=twenty'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {u'message': {u'items_per_page': u"invalid literal for int() with base 10: 'twenty'"}}
        )

    def test_list_packages_page_negative(self):
        """Assert a negative value for a page results in an error."""
        api_endpoint = '/api/v2/packages/?page=-25'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'page': u'Value must be greater than or equal to 1.'}})

    def test_list_packages_page_non_integer(self):
        """Assert a non-integer value for a page results in an error."""
        api_endpoint = '/api/v2/projects/?page=twenty'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'page': u"invalid literal for int() with base 10: 'twenty'"}})


class PackagesResourcePostTests(DatabaseTestCase):

    def setUp(self):
        super(PackagesResourcePostTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.api_token = models.ApiToken(user=self.user)
        self.project = models.Project(
            name='requests',
            homepage='https://pypi.io/project/requests',
            backend='PyPI',
        )
        self.fedora = models.Distro('Fedora')
        session.add_all([self.user, self.api_token, self.project, self.fedora])
        session.commit()

        self.auth = {'Authorization': 'Token ' + self.api_token.token}

    def test_unauthenticated(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post('/api/v2/packages/')

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_token(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post('/api/v2/packages/', headers={'Authorization': 'Token eh'})

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_auth_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post(
            '/api/v2/packages/', headers={'Authorization': 'Basic ' + self.api_token.token})

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_no_token_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post(
            '/api/v2/packages/', headers={'Authorization': 'pleaseletmein'})

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_request(self):
        """Assert invalid requests result in a helpful HTTP 400."""
        output = self.app.post('/api/v2/packages/', headers=self.auth)

        self.assertEqual(output.status_code, 400)
        # Error details should report the missing required fields
        data = _read_json(output)
        error_details = data["message"]
        self.assertIn("distribution", error_details)
        self.assertIn("package_name", error_details)
        self.assertIn("project_name", error_details)
        self.assertIn("project_ecosystem", error_details)

    def test_valid_request(self):
        """Assert packages can be created."""
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        output = self.app.post('/api/v2/packages/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 201)
        data = _read_json(output)
        self.assertEqual({'distribution': 'Fedora', 'name': 'python-requests'}, data)

    def test_same_package_two_distros(self):
        """Assert packages can be created."""
        Session.add(models.Distro('Debian'))
        Session.commit()
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        output = self.app.post('/api/v2/packages/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 201)

        request_data['distribution'] = 'Debian'
        output = self.app.post('/api/v2/packages/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 201)

    def test_conflicting_request(self):
        """Assert conflicts for packages result in HTTP 409."""
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        output = self.app.post('/api/v2/packages/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 201)
        output = self.app.post('/api/v2/packages/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 409)
        # Error details should report conflicting fields.
        data = _read_json(output)
        self.assertEqual(data, {'error': 'package already exists in distribution'})

    def test_missing_distro(self):
        """Assert a missing distribution results in HTTP 400."""
        request_data = {
            "project_ecosystem": "pypi",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Mythical Distribution",
        }

        output = self.app.post('/api/v2/packages/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)
        self.assertEqual({'error': 'Distribution "Mythical Distribution" not found'}, data)

    def test_missing_project(self):
        """Assert a missing project results in HTTP 400."""
        request_data = {
            "project_ecosystem": "Missing",
            "project_name": "requests",
            "package_name": "python-requests",
            "distribution": "Fedora",
        }

        output = self.app.post('/api/v2/packages/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)
        self.assertEqual(
            {'error': 'Project "requests" in ecosystem "Missing" not found'}, data)


class ProjectsResourceGetTests(DatabaseTestCase):

    def setUp(self):
        super(ProjectsResourceGetTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.api_token = models.ApiToken(user=self.user)
        session.add_all([self.user, self.api_token])
        session.commit()

    def test_no_projects(self):
        """Assert querying projects works, even if there are no projects."""
        output = self.app.get('/api/v2/projects/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 25, 'total_items': 0, 'items': []})

    def test_authenticated(self):
        """Assert the API works when authenticated."""
        output = self.app.get(
            '/api/v2/projects/', headers={'Authorization': 'Token ' + self.api_token.token})
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 25, 'total_items': 0, 'items': []})

    def test_list_projects(self):
        """Assert projects are returned when they exist."""
        create_project(self.session)

        output = self.app.get('/api/v2/projects/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 3,
            'items': [
                {
                    "id": 3,
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": []
                },
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "http://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://www.geany.org/Download/Releases",
                    "versions": []
                },
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "http://subsurface.hohndel.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://subsurface.hohndel.org/downloads/",
                    "versions": []
                }
            ]
        }

        self.assertEqual(data, exp)

    def test_filter_projects_by_ecosystem(self):
        """Assert projects can be filtered by ecosystem."""
        create_project(self.session)

        output = self.app.get(
            '/api/v2/projects/?ecosystem=http%3A%2F%2Fsubsurface.hohndel.org%2F')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 1,
            'items': [
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "http://subsurface.hohndel.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://subsurface.hohndel.org/downloads/",
                    "versions": []
                }
            ]
        }

        self.assertEqual(data, exp)

    def test_filter_projects_by_name(self):
        """Assert projects can be filtered by name."""
        create_project(self.session)

        output = self.app.get(
            '/api/v2/projects/?name=subsurface')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 1,
            'items': [
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "http://subsurface.hohndel.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://subsurface.hohndel.org/downloads/",
                    "versions": []
                }
            ]
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page(self):
        """Assert pagination works and page size is adjustable."""
        api_endpoint = '/api/v2/projects/?items_per_page=1'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 1, 'total_items': 0, 'items': []})

        create_project(self.session)

        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 1,
            'items_per_page': 1,
            'total_items': 3,
            'items': [
                {
                    "id": 3,
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": []
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page_with_page(self):
        """Assert retrieving other pages works."""
        api_endpoint = '/api/v2/projects/?items_per_page=1&page=2'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 2, 'items_per_page': 1, 'total_items': 0, 'items': []})

        create_project(self.session)

        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 2,
            'items_per_page': 1,
            'total_items': 3,
            'items': [
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "http://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://www.geany.org/Download/Releases",
                    "versions": []
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page_too_big(self):
        """Assert unreasonably large items per page results in an error."""
        api_endpoint = '/api/v2/projects/?items_per_page=500'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'items_per_page': u'Value must be less than or equal to 250.'}})

    def test_list_projects_items_per_page_negative(self):
        """Assert a negative value for items_per_page results in an error."""
        api_endpoint = '/api/v2/projects/?items_per_page=-25'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'items_per_page': u'Value must be greater than or equal to 1.'}})

    def test_list_projects_items_per_page_non_integer(self):
        """Assert a non-integer for items_per_page results in an error."""
        api_endpoint = '/api/v2/projects/?items_per_page=twenty'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {u'message': {u'items_per_page': u"invalid literal for int() with base 10: 'twenty'"}}
        )

    def test_list_projects_page_negative(self):
        """Assert a negative value for a page results in an error."""
        api_endpoint = '/api/v2/projects/?page=-25'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'page': u'Value must be greater than or equal to 1.'}})

    def test_list_projects_page_non_integer(self):
        """Assert a non-integer value for a page results in an error."""
        api_endpoint = '/api/v2/projects/?page=twenty'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'page': u"invalid literal for int() with base 10: 'twenty'"}})


class ProjectsResourcePostTests(DatabaseTestCase):

    def setUp(self):
        super(ProjectsResourcePostTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email='user@example.com', username='user')
        self.api_token = models.ApiToken(user=self.user)
        session.add_all([self.user, self.api_token])
        session.commit()

        self.auth = {'Authorization': 'Token ' + self.api_token.token}

    def test_unauthenticated(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post('/api/v2/projects/')

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_token(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post('/api/v2/projects/', headers={'Authorization': 'Token eh'})

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_auth_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post(
            '/api/v2/projects/', headers={'Authorization': 'Basic ' + self.api_token.token})

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_request(self):
        """Assert invalid requests result in a helpful HTTP 400."""
        output = self.app.post('/api/v2/projects/', headers=self.auth)

        self.assertEqual(output.status_code, 400)
        # Error details should report the missing required fields
        data = _read_json(output)
        error_details = data["message"]
        self.assertIn("backend", error_details)
        self.assertIn("homepage", error_details)
        self.assertIn("name", error_details)

    def test_conflicting_request(self):
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }

        output = self.app.post('/api/v2/projects/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 201)
        output = self.app.post('/api/v2/projects/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 409)
        # Error details should report conflicting fields.
        data = _read_json(output)
        self.assertIn("requested_project", data)
        self.assertEqual("PyPI", data["requested_project"]["backend"])
        self.assertEqual("http://python-requests.org", data["requested_project"]["homepage"])
        self.assertEqual("requests", data["requested_project"]["name"])

    def test_valid_request(self):
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }

        output = self.app.post('/api/v2/projects/', headers=self.auth, data=request_data)

        data = _read_json(output)
        self.assertEqual(output.status_code, 201)
        self.assertIn("backend", data)
        self.assertIn("homepage", data)
        self.assertIn("name", data)
        self.assertEqual("PyPI", data["backend"])
        self.assertEqual("http://python-requests.org", data["homepage"])
        self.assertEqual("requests", data["name"])
