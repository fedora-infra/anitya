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
from __future__ import unicode_literals

import unittest

import mock

from anitya.lib import exceptions
from anitya.lib.versions import base


class VersionTests(unittest.TestCase):
    """Tests for the :class:`anitya.lib.versions.Version` model."""

    def test_identity_string(self):
        """Assert the generic version constant is what we expect.
        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            versions.
        """
        self.assertEqual('Generic Version', base.Version.name)

    def test_str(self):
        """Assert __str__ calls parse"""
        version = base.Version(version='v1.0.0')
        self.assertEqual('1.0.0', str(version))

    def test_str_parse_error(self):
        """Assert __str__ calls parse"""
        version = base.Version(version='v1.0.0')
        version.parse = mock.Mock(side_effect=exceptions.InvalidVersion('boop'))
        self.assertEqual('v1.0.0', str(version))

    def test_str_parse_error_none(self):
        """Assert __str__ calls parse throws InvalidVersion when version is None"""
        version = base.Version(version=None)
        self.assertRaises(
            exceptions.InvalidVersion,
            version.parse,
        )

    def test_parse_no_v(self):
        """Assert parsing a version sans leading 'v' works."""
        version = base.Version(version='1.0.0')
        self.assertEqual('1.0.0', version.parse())

    def test_parse_leading_v(self):
        """Assert parsing a version with a leading 'v' works."""
        version = base.Version(version='v1.0.0')
        self.assertEqual('1.0.0', version.parse())

    def test_parse_odd_version(self):
        """Assert parsing an odd version works."""
        version = base.Version(version='release_1_0_0')
        self.assertEqual('release_1_0_0', version.parse())

    def test_parse_v_not_alone(self):
        """Assert leading 'v' isn't stripped if it's not followed by a number."""
        version = base.Version(version='version1.0.0')
        self.assertEqual('version1.0.0', version.parse())

    def test_parse_with_prefix_no_v(self):
        version = base.Version(version='release1.0.0', prefix='release')
        self.assertEqual('1.0.0', version.parse())

    def test_parse_with_prefix_with_v(self):
        version = base.Version(version='release-v1.0.0', prefix='release-')
        self.assertEqual('1.0.0', version.parse())

    def test_prerelease(self):
        """Assert prerelease is defined and returns False"""
        version = base.Version(version='v1.0.0')
        self.assertFalse(version.prerelease())

    def test_postrelease(self):
        """Assert postrelease is defined and returns False"""
        version = base.Version(version='v1.0.0')
        self.assertFalse(version.postrelease())

    def test_newer_single_version(self):
        """Assert newer is functional with a single instance of Version."""
        version = base.Version(version='v1.0.0')
        newer_version = base.Version(version='v2.0.0')
        self.assertFalse(version.newer(newer_version))
        self.assertTrue(newer_version.newer(version))

    def test_newer_multiple_versions(self):
        """Assert newer is functional with multiple instances of Version."""
        version = base.Version(version='v1.0.0')
        version2 = base.Version(version='v1.1.0')
        newer_version = base.Version(version='v2.0.0')
        self.assertFalse(version.newer(newer_version))
        self.assertTrue(newer_version.newer([version, version2]))

    def test_newer_with_strings(self):
        """Assert newer handles string arguments."""
        version = base.Version(version='v1.0.0')
        self.assertFalse(version.newer('v2.0.0'))

    def test_lt(self):
        """Assert Version supports < comparison."""
        old_version = base.Version(version='v1.0.0')
        new_version = base.Version(version='v1.1.0')
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_one_unparsable(self):
        """Assert unparsable versions sort lower than parsable ones."""
        unparsable_version = base.Version(version='blarg')
        unparsable_version.parse = mock.Mock(side_effect=exceptions.InvalidVersion('blarg'))
        new_version = base.Version(version='v1.0.0')
        self.assertTrue(unparsable_version < new_version)
        self.assertFalse(new_version < unparsable_version)

    def test_lt_both_unparsable(self):
        """Assert unparsable versions resort to string sorting."""
        alphabetically_lower = base.Version(version='arg')
        alphabetically_lower.parse = mock.Mock(side_effect=exceptions.InvalidVersion('arg'))
        alphabetically_higher = base.Version(version='blarg')
        alphabetically_higher.parse = mock.Mock(side_effect=exceptions.InvalidVersion('blarg'))
        self.assertTrue(alphabetically_lower < alphabetically_higher)

    def test_le(self):
        """Assert Version supports <= comparison."""
        old_version = base.Version(version='v1.0.0')
        equally_old_version = base.Version(version='v1.0.0')
        new_version = base.Version(version='v1.1.0')
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert Version supports > comparison."""
        old_version = base.Version(version='v1.0.0')
        new_version = base.Version(version='v1.1.0')
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert Version supports >= comparison."""
        old_version = base.Version(version='v1.0.0')
        equally_new_version = base.Version(version='v1.1.0')
        new_version = base.Version(version='v1.1.0')
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert Version supports == comparison."""
        v1 = base.Version(version='v1.0.0')
        v2 = base.Version(version='v1.0.0')
        self.assertTrue(v1 == v2)

    def test_eq_one_with_v(self):
        """Assert Versions where one just has a v prefix are still equal"""
        v1 = base.Version(version='1.0.0')
        v2 = base.Version(version='v1.0.0')
        self.assertTrue(v1 == v2)

    def test_eq_one_with_prefix(self):
        """Assert Versions where one just has a v prefix are still equal"""
        v1 = base.Version(version='1.0.0')
        v2 = base.Version(version='prefix1.0.0', prefix='prefix')
        self.assertTrue(v1 == v2)

    def test_eq_both_unparsable(self):
        """Assert unparsable versions that are the same string are equal."""
        v1 = base.Version(version='arg')
        v2 = base.Version(version='arg')
        v1.parse = mock.Mock(side_effect=exceptions.InvalidVersion('arg'))
        v2.parse = mock.Mock(side_effect=exceptions.InvalidVersion('arg'))
        self.assertEqual(v1, v2)
