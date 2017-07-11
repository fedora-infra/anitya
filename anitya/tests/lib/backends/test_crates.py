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
"""
Tests for the :mod:`anitya.lib.backends.crates` module.
"""
from __future__ import unicode_literals

import unittest

import mock

from anitya.lib.exceptions import AnityaPluginException
from anitya.lib.backends import crates
from anitya.tests.base import DatabaseTestCase
import anitya.lib.model as model


class CratesBackendTests(DatabaseTestCase):
    """Crates backend tests."""

    def setUp(self):
        """Set up the environnment, run before every test"""
        super(CratesBackendTests, self).setUp()
        self.create_project()

    def create_project(self):
        """Create some basic projects to work with."""
        project1 = model.Project(
            name='itoa',
            homepage='https://crates.io/crates/itoa',
            backend='crates.io',
        )
        project2 = model.Project(
            name='pleasedontmakethisprojectitllbreakmytests',
            homepage='https://crates.io/crates/somenonsensehomepage',
            backend='crates.io',
        )
        self.session.add(project1)
        self.session.add(project2)
        self.session.commit()

    def test_get_version(self):
        """Test the get_version function of the crates backend."""
        project = model.Project.by_id(self.session, 1)
        self.assertEqual('0.2.1', crates.CratesBackend.get_version(project))

    def test_get_version_missing(self):
        """Assert an exception is raised if a project doesn't exist and get_version is called"""
        project = model.Project.get(self.session, 2)
        self.assertRaises(
            AnityaPluginException,
            crates.CratesBackend.get_version,
            project
        )

    def test_get_versions(self):
        """Test the get_versions function of the crates backend."""
        expected_versions = ['0.2.1', '0.2.0', '0.1.1', '0.1.0']
        project = model.Project.by_id(self.session, 1)
        self.assertEqual(expected_versions, crates.CratesBackend.get_versions(project))

    def test_get_ordered_versions(self):
        """Test the get_ordered_versions function of the crates backend. """
        expected_versions = ['0.2.1', '0.2.0', '0.1.1', '0.1.0']
        project = model.Project.by_id(self.session, 1)
        self.assertEqual(expected_versions, crates.CratesBackend.get_ordered_versions(project))

    @mock.patch('anitya.lib.backends.crates.CratesBackend.call_url')
    def test__get_versions_no_json(self, mock_call_url):
        """Assert we handle getting non-JSON responses gracefully"""
        mock_call_url.return_value.json.side_effect = ValueError
        project = model.Project.by_id(self.session, 1)
        with self.assertRaises(AnityaPluginException) as context_manager:
            crates.CratesBackend._get_versions(project)
            self.assertIn('Failed to decode JSON', str(context_manager.exception))


if __name__ == '__main__':
    unittest.main(verbosity=2)
