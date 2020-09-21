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
This adds support for comparing project versions using the RPM version rules.
"""
from __future__ import unicode_literals

import functools
import re

from .base import Version


try:
    from rpm import labelCompare as _compare_rpm_labels
except ImportError:
    # Emulate RPM field comparisons as described in
    # https://stackoverflow.com/a/3206477
    #
    # * Search each string for alphabetic fields [a-zA-Z]+ and
    #   numeric fields [0-9]+ separated by junk [^a-zA-Z0-9]*.
    # * Successive fields in each string are compared to each other.
    # * Alphabetic sections are compared lexicographically, and the
    #   numeric sections are compared numerically.
    # * In the case of a mismatch where one field is numeric and one is
    #   alphabetic, the numeric field is always considered greater (newer).
    # * In the case where one string runs out of fields, the other is always
    #   considered greater (newer).

    import warnings

    warnings.warn("Failed to import 'rpm', emulating RPM label comparisons")

    try:
        from itertools import zip_longest
    except ImportError:
        from itertools import izip_longest as zip_longest

    _subfield_pattern = re.compile(
        r"(?P<junk>[^a-zA-Z0-9]*)((?P<text>[a-zA-Z]+)|(?P<num>[0-9]+))"
    )

    def _iter_rpm_subfields(field):
        """Yield subfields as 2-tuples that sort in the desired order

        Text subfields are yielded as (0, text_value)
        Numeric subfields are yielded as (1, int_value)
        """
        for subfield in _subfield_pattern.finditer(field):
            text = subfield.group("text")
            if text is not None:
                yield (0, text)
            else:
                yield (1, int(subfield.group("num")))

    def _compare_rpm_field(lhs, rhs):
        # Short circuit for exact matches (including both being None)
        if lhs == rhs:
            return 0
        # Otherwise assume both inputs are strings
        lhs_subfields = _iter_rpm_subfields(lhs)
        rhs_subfields = _iter_rpm_subfields(rhs)
        for lhs_sf, rhs_sf in zip_longest(lhs_subfields, rhs_subfields):
            if lhs_sf == rhs_sf:
                # When both subfields are the same, move to next subfield
                continue
            if lhs_sf is None:
                # Fewer subfields in LHS, so it's less than/older than RHS
                return -1
            if rhs_sf is None:
                # More subfields in LHS, so it's greater than/newer than RHS
                return 1
            # Found a differing subfield, so it determines the relative order
            return -1 if lhs_sf < rhs_sf else 1
        # No relevant differences found between LHS and RHS
        return 0

    def _compare_rpm_labels(lhs, rhs):
        lhs_epoch, lhs_version, lhs_release = lhs
        rhs_epoch, rhs_version, rhs_release = rhs
        result = _compare_rpm_field(lhs_epoch, rhs_epoch)
        if result:
            return result
        result = _compare_rpm_field(lhs_version, rhs_version)
        if result:
            return result
        return _compare_rpm_field(lhs_release, rhs_release)


@functools.total_ordering
class RpmVersion(Version):
    """
    This implements an RPM version plugin.

    It sorts versions using the rpm Python binding, if available, and falls
    back to a pure Python implementation if they are not installed.
    """

    name = "RPM"

    _rc_upstream_regex = re.compile(
        r"(.*?)\.?(-?(rc|pre|beta|alpha|dev)([0-9]*))", re.I
    )

    @classmethod
    def split_rc(cls, version):
        """Split (upstream) version into version and release candidate string +
        release candidate number if possible

        Code from Till Maas as part of
        `cnucnu <https://fedorapeople.org/cgit/till/public_git/cnucnu.git/>`_

        Args:
            version (str): A version string to split.

        Returns:
            tuple: A tuple of (version, release_string, release_number) where release_string
                is one of (rc, pre, beta, alpha, dev).
        """
        match = cls._rc_upstream_regex.match(version)
        if not match:
            return (version, "", "")

        return (match.group(1), match.group(3), match.group(4))

    def prerelease(self):
        """
        Check if a version is a pre-release version.

        This recognizes versions containing "rc", "pre", "beta", "alpha", and
        "dev" as being pre-release versions.
        """
        if self.split_rc(self.parse())[1]:
            return True

        for pre_release_filter in self.pre_release_filters:
            if pre_release_filter and pre_release_filter in self.version:
                return True

        return False

    def __eq__(self, other):
        """
        Compare two versions for equality using the RPM rules with pre-release
        support.
        """
        v1, rc1, rcn1 = self.split_rc(self.parse())
        v2, rc2, rcn2 = self.split_rc(other.parse())
        result = _compare_rpm_labels((None, v1, None), (None, v2, None))
        if result != 0:
            return False

        if rc1 == rc2 and rcn1 == rcn2:
            return True
        else:
            return False

    def __lt__(self, other):
        v1, rc1, rcn1 = self.split_rc(self.parse())
        v2, rc2, rcn2 = self.split_rc(other.parse())
        result = _compare_rpm_labels((None, v1, None), (None, v2, None))
        if result == -1:
            return True
        elif result == 1:
            return False

        if rc1 and rc2:
            # both are rc, higher rc is newer
            rc1_text = rc1.lower()
            rc2_text = rc2.lower()
            # rc > pre > beta > alpha
            if rc1_text < rc2_text:
                return True
            if rc1_text > rc2_text:
                return False
            if rcn1 and rcn2:
                # both have rc number
                return int(rcn1) < int(rcn2)
            if rcn1:
                # only first has rc number, then it is newer
                return False
            if rcn2:
                # only second has rc number, then it is newer
                return True
            # both rc numbers are missing or same
            return False

        if rc1:
            # only first is rc, then second is newer
            return True
        if rc2:
            # only second is rc, then first is newer
            return False

        # neither is a rc
        return False
