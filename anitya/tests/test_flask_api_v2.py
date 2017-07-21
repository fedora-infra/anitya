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
import os.path

import oauthlib.oauth2
import requests_oauthlib

import mock
import unittest2 as unittest  # Ensure we always have TestCase.addCleanup

import anitya
from .base import (DatabaseTestCase, create_project)


# Py3 compatibility: UTF-8 decoding and JSON decoding may be separate steps
def _read_json(output):
    return json.loads(output.get_data(as_text=True))


class _APItestsMixin(object):
    """Helper mixin to set up API testing environment"""

    def setUp(self):
        super(_APItestsMixin, self).setUp()

        anitya.app.APP.config['TESTING'] = True
        self.oidc = anitya.authentication.oidc
        self.app = anitya.app.APP.test_client()


class AnonymousAccessTests(_APItestsMixin, DatabaseTestCase):
    """Test access to APIs that don't require authentication"""

    def test_list_projects(self):
        api_endpoint = '/api/v2/projects/'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 25, 'total_items': 0, 'items': []})

        create_project(self.session)

        output = self.app.get(api_endpoint)
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

    def test_list_projects_items_per_page(self):
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


class AuthenticationRequiredTests(_APItestsMixin, DatabaseTestCase):
    """Test anonymous access is blocked to APIs requiring authentication"""

    def _check_authentication_failure_response(self, output):
        data = _read_json(output)
        # Check we get the expected error details
        if not hasattr(self.oidc, 'flow'):
            exp = {
                'error': 'oidc_not_configured',
                'error_description': 'OpenID Connect is not configured on the server'
            }
        else:
            exp = {
                "error_description": "Token required but invalid",
                "error": "invalid_token",
            }
        self.assertEqual(data, exp)

    def test_project_monitoring_request(self):
        self.maxDiff = None
        output = self.app.post('/api/v2/projects/')
        self.assertEqual(output.status_code, 401)
        self._check_authentication_failure_response(output)


class _AuthenticatedAPItestsMixin(_APItestsMixin):
    """Common test definitions for tests of authenticated access"""

    def _post_app_url(self, post_url, **kwds):
        raise NotImplementedError("Subclass must define how to post a URL")

    def test_invalid_project_monitoring_request(self):
        # Check we get a 400 error reporting what we did wrong
        # rather than an authentication error
        output = self._post_app_url('/api/v2/projects/')
        self.assertEqual(output.status_code, 400)
        # Error details should report the missing required fields
        data = _read_json(output)
        error_details = data["message"]
        self.assertIn("backend", error_details)
        self.assertIn("homepage", error_details)
        self.assertIn("name", error_details)

    def test_conflicting_project_monitoring_request(self):
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }
        output = self._post_app_url("/api/v2/projects/", data=request_data)
        self.assertEqual(output.status_code, 201)
        output = self._post_app_url("/api/v2/projects/", data=request_data)
        self.assertEqual(output.status_code, 409)
        # Error details should report conflicting fields.
        data = _read_json(output)
        self.assertIn("requested_project", data)
        self.assertEqual("PyPI", data["requested_project"]["backend"])
        self.assertEqual("http://python-requests.org", data["requested_project"]["homepage"])
        self.assertEqual("requests", data["requested_project"]["name"])

    def test_valid_project_monitoring_request(self):
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }
        output = self._post_app_url('/api/v2/projects/', data=request_data)
        # Error details should report the missing required fields
        data = _read_json(output)
        self.assertEqual(output.status_code, 201)
        self.assertIn("backend", data)
        self.assertIn("homepage", data)
        self.assertIn("name", data)
        self.assertEqual("PyPI", data["backend"])
        self.assertEqual("http://python-requests.org", data["homepage"])
        self.assertEqual("requests", data["name"])


class MockAuthenticationTests(_AuthenticatedAPItestsMixin, DatabaseTestCase):
    """Test authenticated behaviour with authentication checks mocked out"""

    def setUp(self):
        super(MockAuthenticationTests, self).setUp()

        # Replace anitya.authentication._validate_api_token
        def _bypass_token_validation(validated, raw_api, *args, **kwds):
            return raw_api(*args, **kwds)
        mock_auth = mock.patch('anitya.authentication._validate_api_token',
                               _bypass_token_validation)
        mock_auth.start()
        self.addCleanup(mock_auth.stop)

        # Replace anitya.authentication.oidc.user_getfield
        mock_user_data = {
            "email": 'noreply@fedoraproject.org',
        }

        test_case = self

        class MockOIDC:
            # In the live API, `access_token` is optional, but here we expect
            # to receive it
            def user_getfield(self, fieldname, access_token):
                test_case._check_access_token(access_token)
                try:
                    return mock_user_data[fieldname]
                except KeyError:
                    msg = "No mock user data for field {}"
                    raise ValueError(msg.format(fieldname))
        mock_oidc = mock.patch('anitya.authentication.oidc', MockOIDC())
        mock_oidc.start()
        self.addCleanup(mock_oidc.stop)

    DUMMY_ACCESS_TOKEN = "THISISMYTOKEN"

    def _check_access_token(self, access_token):
        self.assertEqual(access_token, self.DUMMY_ACCESS_TOKEN)

    def _post_app_url(self, post_url, **kwds):
        query_string = "access_token={0}".format(self.DUMMY_ACCESS_TOKEN)
        return self.app.post(post_url, query_string=query_string, **kwds)


_this_dir = os.path.dirname(__file__)
CREDENTIALS_FILE = os.path.join(_this_dir, "oidc_credentials.json")


class LiveAuthenticationTests(_AuthenticatedAPItestsMixin, DatabaseTestCase):
    """Test authenticated behaviour with live FAS credentials"""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(CREDENTIALS_FILE):
            raise unittest.SkipTest("No saved OIDC credentials available")
        cls.access_token = cls._refresh_access_token()

    def setUp(self):
        super(LiveAuthenticationTests, self).setUp()
        if self.oidc is None:
            self.skipTest("OpenID Connect is not configured")

    def _post_app_url(self, post_url, **kwds):
        # Note: we currently assume all test cases can be completed
        # without needing to refresh the access token a second time
        query_string = "access_token={0}".format(self.access_token)
        return self.app.post(post_url, query_string=query_string, **kwds)

    @classmethod
    def _refresh_access_token(cls):
        with open(CREDENTIALS_FILE) as f:
            oidc_credentials = json.load(f)
        client_details = oidc_credentials["client_details"]
        client_id = client_details["client_id"]
        client_secret = client_details["client_secret"]
        refresh_uri = client_details["token_uri"]

        token = oidc_credentials["client_token"]
        token["expire_in"] = -1
        oauth = requests_oauthlib.OAuth2Session(client_id, token=token)
        try:
            token = oauth.refresh_token(refresh_uri,
                                        client_id=client_id,
                                        client_secret=client_secret)
        except oauthlib.oauth2.InvalidGrantError:
            msg = ("Token refresh failed, "
                   "try running './request_oidc_credentials.py' again")
            raise RuntimeError(msg)
        oidc_credentials["client_token"] = token

        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(oidc_credentials, f)
        return token["access_token"]


if __name__ == '__main__':
    unittest.main()
