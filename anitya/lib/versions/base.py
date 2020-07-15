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
"""The Anitya versions API."""

from __future__ import unicode_literals

import functools
import re
from typing import Optional
from datetime import datetime

from anitya.lib.exceptions import InvalidVersion


#: A regular expression to determine if the version string contains a 'v' prefix.
v_prefix = re.compile(r"v\d.*")


@functools.total_ordering
class Version(object):
    """The base class for versions."""

    name = "Generic Version"

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
        self.version = version
        if prefix:
            self.prefixes = prefix.split(";")
            # Sort from shorter to longest, this will prevent stripping
            # shorter prefix instead of larger.
            # For example:
            # version = release_db-1.2.3
            # prefixes = release_db-;release
            # would return db-1.2.3 instead of 1.2.3 if the sort is not done
            self.prefixes.sort(key=len)
        else:
            self.prefixes = []
        self.created_on = created_on
        if pattern:
            self.pattern = pattern.upper()
        else:
            self.pattern = None
        self.cursor = cursor
        self.commit_url = commit_url
        if pre_release_filter:
            self.pre_release_filters = pre_release_filter.split(";")
        else:
            self.pre_release_filters = []

    def __str__(self):
        """
        Return a parsed, string version of this instance's version.
        If parsing fails, the original version string is returned.
        """
        try:
            return str(self.parse())
        except InvalidVersion:
            return self.version

    def parse(self):
        """
        Parse the version string to an object representing the version.

        This does some minimal string processing, stripping any prefix set on
        project.

        Returns:
            str: The version string. Sub-classes may return a different type.
            object: Sub-classes may return a special class that represents the
            version. This must support comparison operations and return
            a parsed, prefix-stripped version when ``__str__`` is invoked.

        Raises:
            InvalidVersion: If the version cannot be parsed.
        """
        # If there's a prefix set on the project, strip it if it's present
        version = self.version
        for prefix in self.prefixes:
            if prefix and self.version.startswith(prefix):
                version = self.version[len(prefix) :].strip()

        # Many projects prefix their tags with 'v', so strip it if it's present
        if v_prefix.match(version):
            version = version[1:]

        return version

    def prerelease(self):
        """
        Check if a version is a pre-release version.

        This basic version implementation does not have a concept of
        pre-releases.
        """
        return False

    def postrelease(self):
        """
        Check if a version is a post-release version.

        This basic version implementation does not have a concept of
        post-releases.
        """
        return False

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
        if isinstance(other_versions, (Version, str)):
            other_versions = [other_versions]
        cast_versions = []
        for version in other_versions:
            if not isinstance(version, type(self)):
                version = type(self)(version=version)
            cast_versions.append(version)
        return all([self.parse() > v.parse() for v in cast_versions])

    def __lt__(self, other):
        """Support < comparison via objects returned from :meth:`parse`"""
        try:
            parsed_self = self.parse()
        except InvalidVersion:
            parsed_self = None
        try:
            parsed_other = other.parse()
        except InvalidVersion:
            parsed_other = None

        # Handle the cases where one or both aren't parsable. Parsable versions
        # always sort higher than unparsable versions.
        if not parsed_self and not parsed_other:
            return self.version.__lt__(other.version)
        if not parsed_other:
            return False
        if not parsed_self:
            return True

        return parsed_self.__lt__(parsed_other)

    def __eq__(self, other):
        """Support == comparison via objects returned from :meth:`parse`"""
        try:
            parsed_self = self.parse()
        except InvalidVersion:
            parsed_self = None
        try:
            parsed_other = other.parse()
        except InvalidVersion:
            parsed_other = None

        if not parsed_self or not parsed_other:
            return self.version.__eq__(other.version)
        return parsed_self.__eq__(parsed_other)
