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

from anitya.lib.versions import calver


class CalendarVersionTests(unittest.TestCase):
    """Tests for the :class:`anitya.lib.versions.CalendarVersion` model."""

    def test_identity_string(self):
        """Assert the generic version constant is what we expect.
        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            projects.
        """
        self.assertEqual("Calendar", calver.CalendarVersion.name)

    def test_split_missing_pattern(self):
        """Assert that split function raises exception when pattern is missing."""
        version = calver.CalendarVersion(version="2019.04.23")
        self.assertRaises(ValueError, version.split)

    def test_split_nonsense_pattern(self):
        """Assert that split function raises exception when nonsense pattern is provided."""
        version = calver.CalendarVersion(version="2019.04.23", pattern="AAA")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_YYYY(self):
        """Assert that split function correctly parses YYYY release version pattern."""
        version = calver.CalendarVersion(version="2019", pattern="YYYY")
        expected = {
            "year": "2019",
            "month": None,
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_YYYY_incorrect_version(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="19", pattern="YYYY")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_YYYY_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="aaaa", pattern="YYYY")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_YY(self):
        """Assert that split function correctly parses YY release version pattern."""
        version = calver.CalendarVersion(version="119", pattern="YY")
        expected = {
            "year": "119",
            "month": None,
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_YY_incorrect_version(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="019", pattern="YY")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_YY_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="aa", pattern="YY")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0Y(self):
        """Assert that split function correctly parses 0Y release version pattern."""
        version = calver.CalendarVersion(version="09", pattern="0Y")
        expected = {
            "year": "09",
            "month": None,
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_0Y_incorrect_version(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="019", pattern="0Y")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0Y_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="aa", pattern="0Y")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_MM(self):
        """Assert that split function correctly parses MM release version pattern."""
        version = calver.CalendarVersion(version="9", pattern="MM")
        expected = {
            "year": None,
            "month": "9",
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_MM_incorrect_version(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="09", pattern="MM")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_MM_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="aa", pattern="MM")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0M(self):
        """Assert that split function correctly parses 0M release version pattern."""
        version = calver.CalendarVersion(version="09", pattern="0M")
        expected = {
            "year": None,
            "month": "09",
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_0M_10(self):
        """Assert that split function correctly parses 0M release version pattern."""
        version = calver.CalendarVersion(version="10", pattern="0M")
        expected = {
            "year": None,
            "month": "10",
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_0M_incorrect_version(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="13", pattern="0M")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0M_incorrect_version_zero_padded(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="013", pattern="0M")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0M_too_short_version(self):
        """Assert that split function raises `ValueError` when version is too short."""
        version = calver.CalendarVersion(version="3", pattern="0M")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0M_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="aa", pattern="0M")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_DD(self):
        """Assert that split function correctly parses DD release version pattern."""
        version = calver.CalendarVersion(version="9", pattern="DD")
        expected = {
            "year": None,
            "month": None,
            "day": "9",
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_DD_zero_padded(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="09", pattern="DD")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_DD_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="aa", pattern="DD")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0D(self):
        """Assert that split function correctly parses 0D release version pattern."""
        version = calver.CalendarVersion(version="09", pattern="0D")
        expected = {
            "year": None,
            "month": None,
            "day": "09",
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_0D_10(self):
        """Assert that split function correctly parses 0D release version pattern."""
        version = calver.CalendarVersion(version="10", pattern="0D")
        expected = {
            "year": None,
            "month": None,
            "day": "10",
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_0D_incorrect_version(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="-1", pattern="0D")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0D_incorrect_version_zero_padded(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="013", pattern="0D")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0D_too_short_version(self):
        """Assert that split function raises `ValueError` when version is too short."""
        version = calver.CalendarVersion(version="3", pattern="0D")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_0D_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="aa", pattern="0D")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_MINOR(self):
        """Assert that split function correctly parses MINOR release version pattern."""
        version = calver.CalendarVersion(version="9", pattern="MINOR")
        expected = {
            "year": None,
            "month": None,
            "day": None,
            "minor": "9",
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_MINOR_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="a", pattern="MINOR")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_MICRO(self):
        """Assert that split function correctly parses MICRO release version pattern."""
        version = calver.CalendarVersion(version="9", pattern="MICRO")
        expected = {
            "year": None,
            "month": None,
            "day": None,
            "minor": None,
            "micro": "9",
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_MICRO_not_a_number(self):
        """Assert that split function raises `ValueError` when version is not correct."""
        version = calver.CalendarVersion(version="a", pattern="MICRO")
        self.assertRaises(ValueError, version.split)

    def test_split_pattern_MODIFIER_no_number(self):
        """Assert that split function correctly parses MODIFIER release version pattern."""
        version = calver.CalendarVersion(version="rc", pattern="MODIFIER")
        expected = {
            "year": None,
            "month": None,
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": "rc",
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_pattern_MODIFIER_number(self):
        """Assert that split function correctly parses MODIFIER release version pattern."""
        version = calver.CalendarVersion(version="rc1", pattern="MODIFIER")
        expected = {
            "year": None,
            "month": None,
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": "rc",
            "rc_number": "1",
        }
        self.assertEqual(version.split(), expected)

    def test_split_ubuntu_pattern(self):
        """Assert that Ubuntu version can be correctly split."""
        version = calver.CalendarVersion(version="18.04.1", pattern="YY.0M.MICRO")
        expected = {
            "year": "18",
            "month": "04",
            "day": None,
            "minor": None,
            "micro": "1",
            "modifier": None,
            "rc_number": None,
        }
        self.assertEqual(version.split(), expected)

    def test_split_incorrect_delimiter(self):
        """Assert that incorrect delimiter is detected."""
        version = calver.CalendarVersion(version="18.04-1", pattern="YY.0M.MICRO")
        self.assertRaises(ValueError, version.split)

    def test_prerelease_false(self):
        """Assert prerelease is defined and returns False with non-prerelease versions."""
        version = calver.CalendarVersion(version="2019.04.23", pattern="YYYY.0M.DD")
        self.assertFalse(version.prerelease())

    def test_prerelease_no_number(self):
        """Assert pre-releases without a number are still valid pre-releases."""
        for suffix in ("rc", "alpha", "beta", "dev", "pre"):
            version = calver.CalendarVersion(
                version="2019.04.23-" + suffix, pattern="YYYY.0M.DD-MODIFIER"
            )
            self.assertTrue(version.prerelease())

    def test_prerelease_filter(self):
        """Assert pre-releases will be valid if filter is applied."""
        version = calver.CalendarVersion(
            version="2019.05.23", pattern="YYYY.0M.DD", pre_release_filter="05."
        )
        self.assertTrue(version.prerelease())

    def test_prerelease_multiple_filter(self):
        """Assert pre-releases will be valid if multiple filters is applied."""
        version = calver.CalendarVersion(
            version="2019.05.23", pattern="YYYY.0M.DD", pre_release_filter="05.;06."
        )
        self.assertTrue(version.prerelease())

    def test_prerelease_with_number(self):
        """Assert versions with RC are prerelease versions."""
        for suffix in ("rc1", "alpha2", "beta10", "dev3", "pre999"):
            version = calver.CalendarVersion(
                version="2019.04.23-" + suffix, pattern="YYYY.0M.DD-MODIFIER"
            )
            self.assertTrue(version.prerelease())

    def test_prerelease_nonsense(self):
        """Assert prerelease is defined and returns False with nonsense versions."""
        version = calver.CalendarVersion(version="2019.04.23", pattern="AAAA")
        self.assertFalse(version.prerelease())

    def test_lt_years(self):
        """Assert CalendarVersion supports < comparison by years."""
        old_version = calver.CalendarVersion(version="2019.04.23", pattern="YYYY.0M.DD")
        new_version = calver.CalendarVersion(version="2020.04.23", pattern="YYYY.0M.DD")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_months(self):
        """Assert CalendarVersion supports < comparison by months."""
        old_version = calver.CalendarVersion(version="04.23", pattern="0M.DD")
        new_version = calver.CalendarVersion(version="05.23", pattern="0M.DD")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_days(self):
        """Assert CalendarVersion supports < comparison by days."""
        old_version = calver.CalendarVersion(version="23", pattern="DD")
        new_version = calver.CalendarVersion(version="24", pattern="DD")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_minor(self):
        """Assert CalendarVersion supports < comparison by minor version."""
        old_version = calver.CalendarVersion(version="1", pattern="MINOR")
        new_version = calver.CalendarVersion(version="2", pattern="MINOR")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_micro(self):
        """Assert CalendarVersion supports < comparison by micro version."""
        old_version = calver.CalendarVersion(version="1", pattern="MICRO")
        new_version = calver.CalendarVersion(version="2", pattern="MICRO")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_one_prerelease_field(self):
        """Assert versions with prerelease fields are lesser than those that don't have them."""
        old_version = calver.CalendarVersion(
            version="2019.04.23-1-2_pre", pattern="YYYY.0M.DD-MINOR-MICRO_MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-1-2", pattern="YYYY.0M.DD-MINOR-MICRO_MODIFIER"
        )
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_two_prerelease_fields(self):
        """Assert prerelease fields are compared."""
        old_version = calver.CalendarVersion(
            version="2019.04.23-pre1", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-pre2", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_rc_vs_pre(self):
        """Assert rc prereleases are greater than pre prereleases of the same version."""
        old_version = calver.CalendarVersion(
            version="2019.04.23-pre1", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-rc1", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_pre_vs_beta(self):
        """Assert pre prereleases are greater than beta prereleases of the same version."""
        old_version = calver.CalendarVersion(
            version="2019.04.23-beta1", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-pre1", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_beta_vs_alpha(self):
        """Assert beta prereleases are greater than alpha prereleases of the same version."""
        old_version = calver.CalendarVersion(
            version="2019.04.23-alpha1", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-beta1", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_both_prerelease_one_unversioned(self):
        """Assert unversioned prereleases are less than versioned ones."""
        old_version = calver.CalendarVersion(
            version="2019.04.23-rc", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-rc1", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_nonsense(self):
        """Assert CalendarVersion supports < comparison."""
        # unclear if it should really be valid -junk modifier?
        old_version = calver.CalendarVersion(
            version="2019.04.23junk", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.24", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_lt_prerelease_both_same(self):
        """Assert < always return false when version are the same."""
        version1 = calver.CalendarVersion(
            version="2019.04.23-alpha", pattern="YYYY.0M.DD-MODIFIER"
        )
        version2 = calver.CalendarVersion(
            version="2019.04.23-alpha", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertFalse(version1 < version2)
        self.assertFalse(version2 < version1)

    def test_le(self):
        """Assert CalendarVersion supports <= comparison."""
        old_version = calver.CalendarVersion(
            version="2019.04.23", pattern="YYYY.0M.DD-MODIFIER"
        )
        equally_old_version = calver.CalendarVersion(
            version="2019.04.23", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.24", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert CalendarVersion supports > comparison."""
        old_version = calver.CalendarVersion(
            version="2019.04.23", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.24", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert CalendarVersion supports >= comparison."""
        old_version = calver.CalendarVersion(
            version="2019.04.23", pattern="YYYY.0M.DD-MODIFIER"
        )
        equally_new_version = calver.CalendarVersion(
            version="2019.04.24", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.24", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert CalendarVersion supports == comparison."""
        old_version = calver.CalendarVersion(
            version="2019.04.23", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(new_version == old_version)

    def test_eq_both_unnumbered_prereleases(self):
        """Assert two prereleases of the same type without versions are equal."""
        old_version = calver.CalendarVersion(
            version="2019.04.23-beta", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-beta", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(new_version == old_version)

    def test_eq_nonsense(self):
        """Assert nonsense version is not equal."""
        old_version = calver.CalendarVersion(
            version="2019.04.23junk", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23-beta", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertFalse(old_version == new_version)

    def test_eq_both_nonsense(self):
        """Assert two nonsense versions are equal."""
        old_version = calver.CalendarVersion(
            version="2019.04.23junk", pattern="YYYY.0M.DD-MODIFIER"
        )
        new_version = calver.CalendarVersion(
            version="2019.04.23junk", pattern="YYYY.0M.DD-MODIFIER"
        )
        self.assertTrue(old_version == new_version)

    def test_lt_no_delimiter(self):
        """
        Assert CalendarVersion supports < comparison by full pattern.
        Bug https://github.com/fedora-infra/anitya/issues/867.
        """
        old_version = calver.CalendarVersion(version="20191018", pattern="YYYY0M0D")
        new_version = calver.CalendarVersion(version="20191213", pattern="YYYY0M0D")
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)
