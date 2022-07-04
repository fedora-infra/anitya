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
from anitya.lib.versions import rpm


class RpmVersionTests(unittest.TestCase):
    """Tests for the :class:`anitya.lib.versions.Version` model."""

    def test_identity_string(self):
        """Assert the generic version constant is what we expect.

        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            projects.
        """
        self.assertEqual("RPM", rpm.RpmVersion.name)

    def test_split_rc_prerelease_tag(self):
        result = rpm.RpmVersion.split_rc("1.8.23-alpha1")
        self.assertEqual(("1.8.23", "alpha", "1"), result)

    def test_split_rc_no_prerelease_tag(self):
        result = rpm.RpmVersion.split_rc("1.8.23")
        self.assertEqual(("1.8.23", "", ""), result)

    def test_str(self):
        """Assert __str__ calls parse"""
        version = rpm.RpmVersion(version="v1.0.0")
        self.assertEqual("1.0.0", str(version))

    def test_str_parse_error(self):
        """Assert __str__ calls parse"""
        version = rpm.RpmVersion(version="v1.0.0")
        version.parse = mock.Mock(side_effect=exceptions.InvalidVersion("boop"))
        self.assertEqual("v1.0.0", str(version))

    def test_parse_no_v(self):
        """Assert parsing a version sans leading 'v' works."""
        version = rpm.RpmVersion(version="1.0.0")
        self.assertEqual("1.0.0", version.parse())

    def test_parse_leading_v(self):
        """Assert parsing a version with a leading 'v' works."""
        version = rpm.RpmVersion(version="v1.0.0")
        self.assertEqual("1.0.0", version.parse())

    def test_parse_odd_version(self):
        """Assert parsing an odd version works."""
        version = rpm.RpmVersion(version="release_1_0_0")
        self.assertEqual("release_1_0_0", version.parse())

    def test_parse_v_not_alone(self):
        """Assert leading 'v' isn't stripped if it's not followed by a number."""
        version = rpm.RpmVersion(version="version1.0.0")
        self.assertEqual("version1.0.0", version.parse())

    def test_prerelease_false(self):
        """Assert prerelease is defined and returns False with non-prerelease versions."""
        version = rpm.RpmVersion(version="v1.0.0")
        self.assertFalse(version.prerelease())

    def test_prerelease_prerelease_no_number(self):
        """Assert pre-releases without a number are still valid pre-releases."""
        for suffix in ("rc", "alpha", "beta", "dev", "pre"):
            version = rpm.RpmVersion(version="v1.0.0" + suffix)
            self.assertTrue(version.prerelease())

    def test_prerelease_with_number(self):
        """Assert versions with RC are prerelease versions."""
        for suffix in ("rc1", "alpha2", "beta10", "dev3", "pre999"):
            version = rpm.RpmVersion(version="v1.0.0" + suffix)
            self.assertTrue(version.prerelease())

    def test_prerelease_nonsense(self):
        """Assert versions with junk following the version aren't prerelease versions."""
        version = rpm.RpmVersion(version="v1.0.0junk1")
        self.assertFalse(version.prerelease())

    def test_prerelease_filter(self):
        """Assert pre-releases will be valid if filter is applied."""
        version = rpm.RpmVersion(version="v1.0.0", pre_release_filter="v")
        self.assertTrue(version.prerelease())

    def test_prerelease_multiple_filter(self):
        """Assert pre-releases will be valid if multiple filters is applied."""
        version = rpm.RpmVersion(version="v1.0.0", pre_release_filter="v;a")
        self.assertTrue(version.prerelease())

    def test_postrelease_false(self):
        """Assert postrelease is defined and returns False for non-postreleases."""
        version = rpm.RpmVersion(version="v1.0.0")
        self.assertFalse(version.postrelease())

    def test_postrelease(self):
        """Assert postrelease is currently unsupported."""
        version = rpm.RpmVersion(version="v1.0.0post1")
        self.assertFalse(version.postrelease())

    def test_newer(self):
        """Assert newer is functional."""
        version = rpm.RpmVersion(version="v1.0.0")
        newer_version = rpm.RpmVersion(version="v2.0.0")
        self.assertFalse(version.newer(newer_version))
        self.assertTrue(newer_version.newer(version))

    def test_newer_with_strings(self):
        """Assert newer handles string arguments,"""
        version = rpm.RpmVersion(version="v1.0.0")
        self.assertFalse(version.newer("v2.0.0"))

    def test_newer_numerical(self):
        """Assert newer is functional."""
        version = rpm.RpmVersion(version="v1.1.0")
        newer_version = rpm.RpmVersion(version="v1.11.0")
        self.assertFalse(version.newer(newer_version))
        self.assertTrue(newer_version.newer(version))

    def test_lt(self):
        """Assert RpmVersion supports < comparison."""
        old_version = rpm.RpmVersion(version="v1.0.0")
        new_version = rpm.RpmVersion(version="v1.1.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_one_release_field(self):
        """Assert versions with release fields are greater than those that don't have them."""
        old_version = rpm.RpmVersion(version="v1.0.0")
        new_version = rpm.RpmVersion(version="v1.0.0-1.fc26")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_two_release_fields(self):
        """Assert release fields are compared."""
        old_version = rpm.RpmVersion(version="v1.0.0-1.fc26")
        new_version = rpm.RpmVersion(version="v1.0.0-11.fc26")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_rc_vs_pre(self):
        """Assert rc prereleases are greater than pre prereleases of the same version."""
        old_version = rpm.RpmVersion(version="1.0.0pre2")
        new_version = rpm.RpmVersion(version="1.0.0rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_pre_vs_beta(self):
        """Assert pre prereleases are greater than beta prereleases of the same version."""
        old_version = rpm.RpmVersion(version="1.0.0pre2")
        new_version = rpm.RpmVersion(version="1.0.0rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_beta_vs_alpha(self):
        """Assert beta prereleases are greater than alpha prereleases of the same version."""
        old_version = rpm.RpmVersion(version="1.0.0alpha2")
        new_version = rpm.RpmVersion(version="1.0.0beta1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_beta_vs_newer_alpha(self):
        """Assert alpha prereleases of newer versions are larger than older betas."""
        old_version = rpm.RpmVersion(version="1.0.0beta1")
        new_version = rpm.RpmVersion(version="1.0.1alpha2")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_one_prerelease(self):
        """Assert prereleases are less than non-prereleases."""
        old_version = rpm.RpmVersion(version="v1.1.0rc1")
        new_version = rpm.RpmVersion(version="v1.1.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_both_prerelease(self):
        """Assert prereleases sort numerically."""
        old_version = rpm.RpmVersion(version="v1.1.0rc1")
        new_version = rpm.RpmVersion(version="v1.1.0rc11")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_both_prerelease_one_unversioned(self):
        """Assert unversioned prereleases are less than versioned ones."""
        old_version = rpm.RpmVersion(version="v1.1.0rc")
        new_version = rpm.RpmVersion(version="v1.1.0rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_nonsense_version(self):
        """
        Assert nonsense version is less than right one.
        See https://github.com/fedora-infra/anitya/issues/1390
        """
        old_version = rpm.RpmVersion(version="prerelease")
        new_version = rpm.RpmVersion(version="1.1.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_le(self):
        """Assert RpmVersion supports <= comparison."""
        old_version = rpm.RpmVersion(version="v1.0.0")
        equally_old_version = rpm.RpmVersion(version="v1.0.0")
        new_version = rpm.RpmVersion(version="v1.1.0")
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert RpmVersion supports > comparison."""
        old_version = rpm.RpmVersion(version="v1.0.0")
        new_version = rpm.RpmVersion(version="v1.1.0")
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert RpmVersion supports >= comparison."""
        old_version = rpm.RpmVersion(version="v1.0.0")
        equally_new_version = rpm.RpmVersion(version="v1.1.0")
        new_version = rpm.RpmVersion(version="v1.1.0")
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert RpmVersion supports == comparison."""
        old_version = rpm.RpmVersion(version="v1.0.0")
        new_version = rpm.RpmVersion(version="v1.0.0")
        self.assertTrue(new_version == old_version)

    def test_eq_both_unnumbered_prereleases(self):
        """Assert two prereleases of the same type without versions are equal."""
        old_version = rpm.RpmVersion(version="1.0.0beta")
        new_version = rpm.RpmVersion(version="1.0.0beta")
        self.assertTrue(new_version == old_version)

    def test_eq_one_v_prefix(self):
        """Assert versions that are the same except one has a v prefix are equal."""
        old_version = rpm.RpmVersion(version="v1.0.0-1.fc26")
        new_version = rpm.RpmVersion(version="1.0.0-1.fc26")
        self.assertTrue(new_version == old_version)
