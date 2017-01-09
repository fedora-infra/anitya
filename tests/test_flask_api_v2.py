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

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest

import anitya
from tests import (Modeltests, create_project)

# Py3 compatibility: UTF-8 decoding and JSON decoding may be separate steps
def _read_json(output):
    return json.loads(output.get_data(as_text=True))

class _APItestsMixin(object):
    """Helper mixin to set up API testing environment"""

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(_APItestsMixin, self).setUp()

        anitya.app.APP.config['TESTING'] = True
        anitya.app.SESSION = self.session
        anitya.api.SESSION = self.session
        self.app = anitya.app.APP.test_client()


class AnonymousAccessTests(_APItestsMixin, Modeltests):
    """Test access to APIs that don't require authentication"""

    def test_list_projects(self):
        output = self.app.get('/api/v2/projects/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, [])

        create_project(self.session)

        output = self.app.get('/api/projects/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for key in range(len(data['projects'])):
            del(data['projects'][key]['created_on'])
            del(data['projects'][key]['updated_on'])

        exp = {
            "projects": [
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
                    "id": 2,
                    "backend": "custom",
                    "homepage": "http://subsurface.hohndel.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://subsurface.hohndel.org/downloads/",
                    "versions": []
                }
            ],
            "total": 3
        }

        self.assertEqual(data, exp)

class AuthenticationRequiredTests(_APItestsMixin, Modeltests):
    """Test anonymous access is blocked to APIs requiring authentication"""

    def test_project_monitoring_request(self):
        output = self.app.post('/api/v2/projects/')
        self.assertEqual(output.status_code, 401)
        data = _read_json(output)
        # Temporary workaround for rendering-to-str on the server
        data = json.loads(data)
        exp = {
            "error_description": "Token required but invalid",
            "error": "invalid_token",
        }
        self.assertEqual(data, exp)


class _AuthenticatedAPItestsMixin(_APItestsMixin):
    """Common test definitions for tests of authenticated access"""
    pass

class MockAuthenticationTests(_AuthenticatedAPItestsMixin, Modeltests):
    """Test authenticated behaviour with authentication checks mocked out"""
    pass

class LiveAuthenticationTests(_AuthenticatedAPItestsMixin, Modeltests):
    """Test authenticated behaviour with live FAS credentials"""
    pass

if __name__ == '__main__':
    unittest.main()
