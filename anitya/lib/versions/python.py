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
from datetime import datetime
from typing import Optional

# Import entire modules so it's clear which "Version" and "InvalidVersion"
# is used
import packaging.version

from . import base


@functools.total_ordering
class PythonVersion(base.Version):
    """Python (PEP 440) Version."""

    name = "Python (PEP 440)"

    def __init__(
        self,
        version: Optional[str] = None,
        prefix: Optional[str] = None,
        created_on: Optional[datetime] = None,
        pattern: Optional[str] = None,
        cursor: Optional[str] = None,
        commit_url: Optional[str] = None,
        pre_release_filter: Optional[str] = None,
    ):
        """
        Constructor of Version class.

        Params:
            version: Raw version
            prefix: Prefix to remove
            created_on: Date of creation
            pattern: Calendar version pattern.
                See `Calendar version scheme_` for more information.
            cursor: An opaque, backend-specific cursor pointing to the version.
            commit_url: A URL pointing to the commit tagged as the version.
            pre_release_filter: A filter used to identify pre-release versions
        """
        super().__init__(
            version, prefix, created_on, pattern, cursor, commit_url, pre_release_filter
        )

        self.version_object = self.get_version_object()

    def get_version_object(self):
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
        except packaging.version.InvalidVersion:
            return None

    def parse(self):
        """
        Parse the version string and returns something usable by Anitya.

        Returns:
          str: The version string processed by `packaging` module.
        """
        if self.version_object:
            return str(self.version_object)
        else:
            return super().parse()

    def prerelease(self) -> bool:
        """
        Check this is a pre-release version.
        """
        if not self.version_object:
            return False

        if self.version_object.is_prerelease:
            return True

        return super().prerelease()

    def postrelease(self):
        """
        Check this is a post-release version.
        """
        if not self.version_object:
            return False

        return self.version_object.is_postrelease

    def newer(self, other_versions):
        """
        Check a version against a list of other versions to see if it's newer.

        Example:
            >>> version = Version(version='1.1.0')
            >>> version.newer([Version(version='1.0.0')])
            True
            >>> version.newer(['1.0.0', '0.0.1'])  # You can pass strings!
            True
            >>> version.newer(['1.2.0', '2.0.1'])
            False

        Args:
            other_versions (list): A list of version strings or Version
                objects to check the `version` string against.
        Returns:
            bool: True if self is the newest version, ``False otherwise``.
        Raises:
            InvalidVersion: if one or more of the version
                strings provided cannot be parsed.
        """
        if isinstance(other_versions, (base.Version, str)):
            other_versions = [other_versions]
        cast_versions = []
        for version in other_versions:
            if not isinstance(version, type(self)):
                version = type(self)(version=version)
            cast_versions.append(version)
        return all(  # pylint: disable=R1729
            [self.version_object > v.version_object for v in cast_versions]
        )

    def __lt__(self, other):
        """Support < comparison via objects returned from :meth:`version_object`"""
        # Handle the cases where one or both can't be validated. Validated versions
        # always sort higher than unvalidated versions.
        if not self.version_object and not other.version_object:
            return self.version.__lt__(other.version)
        if not other.version_object:
            return False
        if not self.version_object:
            return True

        return self.version_object.__lt__(other.version_object)

    def __eq__(self, other):
        """Support == comparison via objects returned from :meth:`version_object`"""
        # Handle the cases where one or both can't be validated.
        if not self.version_object or not other.version_object:
            return self.version.__eq__(other.version)
        return self.version_object.__eq__(other.version_object)
