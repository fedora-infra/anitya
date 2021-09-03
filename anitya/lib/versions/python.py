# -*- coding: utf-8 -*-
#
# Copyright © 2017-2020 Red Hat, Inc.
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
This adds support for comparing project versions using the PEP 440 rules,
as used on the `Python Package Index`_.

See `Version scheme` in PEP 440.

.. _Version scheme:
   https://www.python.org/dev/peps/pep-0440/#version-scheme
.. _Python Package Index:
   https://pypi.org/
"""

import functools

# Import entire modules so it's clear which "Version" and "InvalidVersion"
# is used
import packaging.version

from . import base


@functools.total_ordering
class PythonVersion(base.Version):
    """Python (PEP 440) Version."""

    name = "Python (PEP 440)"

    def parse(self):
        """
        Parse the version string to an object representing the version.


        Returns:
            packaging.version.Version: This supports comparison operations and
            returns a parsed, prefix-stripped version from ``__str__``.

        Raises:
            base.InvalidVersion: If the version cannot be parsed.
        """
        # The base implementation does some minimal string processing
        version = super().parse()
        # The result should be usable with packaging.version
        try:
            return packaging.version.Version(version)
        except packaging.version.InvalidVersion as e:
            raise base.InvalidVersion(str(e)) from e

    def prerelease(self):
        """
        Check this is a pre-release version.
        """
        try:
            parsed = self.parse()
        except base.InvalidVersion:
            return False

        for pre_release_filter in self.pre_release_filters:
            if pre_release_filter and pre_release_filter in self.version:
                return True

        return parsed.is_prerelease

    def postrelease(self):
        """
        Check this is a post-release version.
        """
        try:
            parsed = self.parse()
        except base.InvalidVersion:
            return False
        return parsed.is_postrelease
