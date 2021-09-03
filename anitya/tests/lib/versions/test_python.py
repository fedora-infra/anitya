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

from anitya.lib.versions import python


# Note that the tests aren't comprehensive. We trust the packaging library
# to order and normalize versions correctly, but we do test several edge cases
# to verify our handling of the version obnjects is OK.


class PythonVersionTests(unittest.TestCase):
    """Tests for the :class:`anitya.lib.versions.PythonVersion` model."""

    def test_identity_string(self):
        """Assert the generic version constant is what we expect.

        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            projects.
        """
        self.assertEqual("Python (PEP 440)", python.PythonVersion.name)

    def test_prerelease_false(self):
        """Assert prerelease is defined and returns False with non-prerelease versions."""
        version = python.PythonVersion(version="1.0.0")
        self.assertFalse(version.prerelease())

    def test_prerelease_with_number(self):
        """Assert versions with RC are prerelease versions."""
        for suffix in ("rc1", "a2", "b10", ".dev3"):
            version = python.PythonVersion(version="1.0.0" + suffix)
            self.assertTrue(version.prerelease())

    def test_prerelease_prerelease_separators(self):
        """Assert pre-release separators are normalized away."""
        for suffix in (".rc1", ".a2", ".b10", "-rc2", "-a3", "-b20"):
            version = python.PythonVersion(version="1.0.0" + suffix[1:])
            self.assertTrue(version.prerelease())

    def test_prerelease_prerelease_no_number(self):
        """Assert pre-releases without a number are still valid pre-releases."""
        for suffix in ("rc", "a", "b", ".dev"):
            version = python.PythonVersion(version="1.0.0" + suffix + "0")
            self.assertTrue(version.prerelease())

    def test_prerelease_nonsense(self):
        """
        Assert versions with junk following the version
        aren't prerelease versions.
        """
        version = python.PythonVersion(version="1.0.0junk1")
        self.assertFalse(version.prerelease())

    def test_prerelease_filter(self):
        """Assert pre-releases will be valid if filter is applied."""
        version = python.PythonVersion(version="1.0.0", pre_release_filter="1.")
        self.assertTrue(version.prerelease())

    def test_prerelease_multiple_filter(self):
        """Assert pre-releases will be valid if multiple filters is applied."""
        version = python.PythonVersion(version="v1.0.0", pre_release_filter="a;v")
        self.assertTrue(version.prerelease())

    def test_lt(self):
        """Assert PythonVersion supports < comparison."""
        old_version = python.PythonVersion(version="1.0.0")
        new_version = python.PythonVersion(version="1.1.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_one_prerelease_field(self):
        """Assert missing prerelease fields are equivalent to 0."""
        old_version = python.PythonVersion(version="1.0.0a0")
        new_version = python.PythonVersion(version="1.0.0a")
        self.assertTrue(old_version == new_version)
        self.assertTrue(new_version == old_version)

    def test_lt_two_prerelease_fields(self):
        """Assert prerelease fields are compared."""
        old_version = python.PythonVersion(version="1.0.0a1")
        new_version = python.PythonVersion(version="1.0.0a2")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_ab_prerelease_fields(self):
        """Assert prerelease fields are compared."""
        old_version = python.PythonVersion(version="1.0.0a1")
        new_version = python.PythonVersion(version="1.0.0b1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_rc_vs_a(self):
        """Assert rc prereleases are greater than pre prereleases of the same version."""
        old_version = python.PythonVersion(version="1.0.0a2")
        new_version = python.PythonVersion(version="1.0.0rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_alpha_vs_beta(self):
        """Assert alpha prereleases are greater than beta prereleases of the same version."""
        old_version = python.PythonVersion(version="1.0.0a2")
        new_version = python.PythonVersion(version="1.0.0rc1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_beta_vs_alpha(self):
        """Assert beta prereleases are greater than alpha prereleases of the same version."""
        old_version = python.PythonVersion(version="1.0.0a2")
        new_version = python.PythonVersion(version="1.0.0b1")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_beta_vs_newer_alpha(self):
        """Assert alpha prereleases of newer versions are larger than older betas."""
        old_version = python.PythonVersion(version="1.0.0b1")
        new_version = python.PythonVersion(version="1.0.1a2")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_both_prerelease_one_unversioned(self):
        """Assert unversioned prereleases are treated as 0."""
        old_version = python.PythonVersion(version="1.1.0rc")
        new_version = python.PythonVersion(version="1.1.0rc0")
        self.assertTrue(old_version == new_version)
        self.assertTrue(new_version == old_version)

    def test_lt_nonsense(self):
        """Assert PythonVersion supports < comparison."""
        old_version = python.PythonVersion(version="1.0.0junk")
        new_version = python.PythonVersion(version="1.1.0")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_le(self):
        """Assert PythonVersion supports <= comparison."""
        old_version = python.PythonVersion(version="1.0.0")
        equally_old_version = python.PythonVersion(version="1.0.0")
        new_version = python.PythonVersion(version="1.1.0")
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert PythonVersion supports > comparison."""
        old_version = python.PythonVersion(version="1.0.0")
        new_version = python.PythonVersion(version="1.1.0")
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert PythonVersion supports >= comparison."""
        old_version = python.PythonVersion(version="1.0.0")
        equally_new_version = python.PythonVersion(version="1.1.0")
        new_version = python.PythonVersion(version="1.1.0")
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert PythonVersion supports == comparison."""
        old_version = python.PythonVersion(version="1.0.0")
        new_version = python.PythonVersion(version="1.0.0")
        self.assertTrue(new_version == old_version)

    def test_eq_both_unnumbered_prereleases(self):
        """Assert two prereleases of the same type without versions are equal."""
        old_version = python.PythonVersion(version="1.0.0b")
        new_version = python.PythonVersion(version="1.0.0b")
        self.assertTrue(new_version == old_version)

    def test_eq_nonsense(self):
        """Assert nonsense version is not equal."""
        old_version = python.PythonVersion(version="1.0.0junk")
        new_version = python.PythonVersion(version="1.0.0")
        self.assertFalse(old_version == new_version)

    def test_eq_both_nonsense(self):
        """Assert two nonsense versions are equal."""
        old_version = python.PythonVersion(version="1.0.0junk")
        new_version = python.PythonVersion(version="1.0.0junk")
        self.assertTrue(old_version == new_version)
