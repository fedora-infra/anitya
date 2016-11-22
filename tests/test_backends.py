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
Unit tests for the anitya.lib.backends module.
"""
from __future__ import absolute_import, unicode_literals

import re
import unittest

import mock

from anitya.lib import backends
from anitya.lib.exceptions import AnityaPluginException


class GetVersionsByRegexTextTests(unittest.TestCase):
    """
    Unit tests for anitya.lib.backends.get_versions_by_regex_text
    """

    def test_get_versions_by_regex_for_text(self):
        """Assert finding versions with a simple regex in text works"""
        text = """
        some release: 0.0.1
        some other release: 0.0.2
        The best release: 1.0.0
        """
        regex = r'\d\.\d\.\d'
        mock_project = mock.Mock(version_prefix='')
        versions = backends.get_versions_by_regex_for_text(
            text, 'url', regex, mock_project)
        self.assertEqual(sorted(['0.0.1', '0.0.2', '1.0.0']), sorted(versions))

    def test_get_versions_by_regex_for_text_prefix(self):
        """Assert prefixes are stripped from regex matches"""
        text = """
        some release: v0.0.1
        some other release: v0.0.2
        The best release: v1.0.0
        """
        regex = r'v\d\.\d\.\d'
        mock_project = mock.Mock(version_prefix='v')
        versions = backends.get_versions_by_regex_for_text(
            text, 'url', regex, mock_project)
        self.assertEqual(sorted(['0.0.1', '0.0.2', '1.0.0']), sorted(versions))

    def test_get_versions_by_regex_for_text_slice_prefix(self):
        """Assert prefixes are sliced rather than lstripped"""
        text = """
        some release: version-v0.0.1-dev
        some other release: version-v0.0.2-dev
        The best release: version-v1.0.0
        """
        regex = r'[\w]*-v\d\.\d\.\d-?[\w]*'
        mock_project = mock.Mock(version_prefix='version-')
        versions = backends.get_versions_by_regex_for_text(
            text, 'url', regex, mock_project)
        self.assertEqual(
            sorted(['v0.0.1-dev', 'v0.0.2-dev', 'v1.0.0']), sorted(versions))

    def test_get_versions_by_regex_for_text_tuples(self):
        """Assert regex that result in tuples are joined into a string"""
        text = """
        some release: 0.0.1
        some other release: 0.0.2
        The best release: 1.0.0
        """
        regex = r'(\d)\.(\d)\.(\d)'
        mock_project = mock.Mock(version_prefix='')
        versions = backends.get_versions_by_regex_for_text(
            text, 'url', regex, mock_project)
        self.assertEqual(sorted(['0.0.1', '0.0.2', '1.0.0']), sorted(versions))
        # Demonstrate that the regex does result in an iterable
        self.assertEqual(3, len(re.findall(regex, '0.0.1')[0]))

    def test_get_versions_by_regex_for_text_no_versions(self):
        """Assert an exception is raised if no matches are found"""
        text = "This text doesn't have a release!"
        regex = r'(\d)\.(\d)\.(\d)'
        mock_project = mock.Mock(version_prefix='')
        self.assertRaises(
            AnityaPluginException,
            backends.get_versions_by_regex_for_text,
            text,
            'url',
            regex,
            mock_project
        )


if __name__ == '__main__':
    unittest.main()
