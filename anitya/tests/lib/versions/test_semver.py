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
import unittest

from anitya.lib.versions import semver


class SemanticVersionTests(unittest.TestCase):
    """Tests for the :class:`anitya.lib.versions.SemanticVersion` model."""

    def test_identity_string(self):
        """Assert the generic version constant is what we expect.

        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            projects.
        """
        self.assertEqual("Semantic", semver.SemanticVersion.name)

    def test_prerelease_false(self):
        """Assert prerelease is defined and returns False with non-prerelease versions."""
        version = semver.SemanticVersion(version="1.0.0")
        self.assertFalse(version.prerelease())

    def test_prerelease_prerelease_no_number(self):
        """Assert pre-releases without a number are still valid pre-releases."""
        for suffix in ("rc", "alpha", "beta", "dev", "pre"):
            version = semver.SemanticVersion(version="1.0.0-" + suffix)
            self.assertTrue(version.prerelease())

    def test_prerelease_with_number(self):
        """Assert versions with RC are prerelease versions."""
        for suffix in ("rc1", "alpha2", "beta10", "dev3", "pre999"):
            version = semver.SemanticVersion(version="1.0.0-" + suffix)
            self.assertTrue(version.prerelease())

    def test_prerelease_nonsense(self):
        """
        Assert versions with junk following the version without '-'
        aren't prerelease versions.
        """
        version = semver.SemanticVersion(version="1.0.0junk1")
        self.assertFalse(version.prerelease())

    def test_lt(self):
        """Assert SemanticVersion supports < comparison."""
        old_version = semver.SemanticVersion(version="1.0.0")
        new_version = semver.SemanticVersion(version="1.1.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_one_prerelease_field(self):
        """Assert versions with prerelease fields are lesser than those that don't have them."""
        old_version = semver.SemanticVersion(version="1.0.0-pre")
        new_version = semver.SemanticVersion(version="1.0.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_two_prerelease_fields(self):
        """Assert prerelease fields are compared."""
        old_version = semver.SemanticVersion(version="1.0.0-pre1")
        new_version = semver.SemanticVersion(version="1.0.0-pre2")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_rc_vs_pre(self):
        """Assert rc prereleases are greater than pre prereleases of the same version."""
        old_version = semver.SemanticVersion(version="1.0.0-pre2")
        new_version = semver.SemanticVersion(version="1.0.0-rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_pre_vs_beta(self):
        """Assert pre prereleases are greater than beta prereleases of the same version."""
        old_version = semver.SemanticVersion(version="1.0.0-pre2")
        new_version = semver.SemanticVersion(version="1.0.0-rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_beta_vs_alpha(self):
        """Assert beta prereleases are greater than alpha prereleases of the same version."""
        old_version = semver.SemanticVersion(version="1.0.0-alpha2")
        new_version = semver.SemanticVersion(version="1.0.0-beta1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_beta_vs_newer_alpha(self):
        """Assert alpha prereleases of newer versions are larger than older betas."""
        old_version = semver.SemanticVersion(version="1.0.0-beta1")
        new_version = semver.SemanticVersion(version="1.0.1-alpha2")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_both_prerelease_one_unversioned(self):
        """Assert unversioned prereleases are less than versioned ones."""
        old_version = semver.SemanticVersion(version="1.1.0-rc")
        new_version = semver.SemanticVersion(version="1.1.0-rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_nonsense(self):
        """Assert SemanticVersion supports < comparison."""
        old_version = semver.SemanticVersion(version="1.0.0junk")
        new_version = semver.SemanticVersion(version="1.1.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_le(self):
        """Assert SemanticVersion supports <= comparison."""
        old_version = semver.SemanticVersion(version="1.0.0")
        equally_old_version = semver.SemanticVersion(version="1.0.0")
        new_version = semver.SemanticVersion(version="1.1.0")
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert SemanticVersion supports > comparison."""
        old_version = semver.SemanticVersion(version="1.0.0")
        new_version = semver.SemanticVersion(version="1.1.0")
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert SemanticVersion supports >= comparison."""
        old_version = semver.SemanticVersion(version="1.0.0")
        equally_new_version = semver.SemanticVersion(version="1.1.0")
        new_version = semver.SemanticVersion(version="1.1.0")
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert SemanticVersion supports == comparison."""
        old_version = semver.SemanticVersion(version="1.0.0")
        new_version = semver.SemanticVersion(version="1.0.0")
        self.assertTrue(new_version == old_version)

    def test_eq_both_unnumbered_prereleases(self):
        """Assert two prereleases of the same type without versions are equal."""
        old_version = semver.SemanticVersion(version="1.0.0-beta")
        new_version = semver.SemanticVersion(version="1.0.0-beta")
        self.assertTrue(new_version == old_version)

    def test_eq_nonsense(self):
        """Assert nonsense version is not equal."""
        old_version = semver.SemanticVersion(version="1.0.0junk")
        new_version = semver.SemanticVersion(version="1.0.0")
        self.assertFalse(old_version == new_version)

    def test_eq_both_nonsense(self):
        """Assert two nonsense versions are equal."""
        old_version = semver.SemanticVersion(version="1.0.0junk")
        new_version = semver.SemanticVersion(version="1.0.0junk")
        self.assertTrue(old_version == new_version)
