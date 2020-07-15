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
"""
This adds support for comparing project versions using the calendar version rules.

See `Calendar versioning`_.
.. _Calendar versioning:
   https://calver.org/
"""
import functools
import re
from typing import Tuple

from .base import Version


def split_by_match(regex: str, string: str) -> Tuple[str, str]:
    """
    Matches the start of the string by regex and returns tuple with
    the match and rest of the string.

    Args:
        regex: Regex used to parse string
        string: String to match

    Returns:
        Tuple with match, rest of string. If no match was found
        it returns empty string as first element and string as second.
    """
    match = re.match(regex, string)
    if match:
        match_string = string[: match.end()]
        rest_string = string[match.end() :]
        return match_string, rest_string

    return "", string


@functools.total_ordering
class CalendarVersion(Version):
    """
    This implements an Calendar version plugin.

    It sorts versions using the calendar version pattern.

    Attributes:
        pattern: Calendar version pattern.
            See `Calendar version scheme_` for more information.

    .. _Calendar version scheme:
       https://calver.org/#scheme
    """

    name = "Calendar"

    def split(self) -> dict:
        """
        Does a simple lexical analysis of the version against pattern.

        Returns:
            (dict): key - pattern key, value - part of version corresponding to key.

        Raises:
            ValueError: If version can't be parsed by specified pattern.
                This could happen if the pattern is not correct or if
                the version can't be parsed by the pattern.
        """
        result_dict = {
            "year": None,
            "month": None,
            "day": None,
            "minor": None,
            "micro": None,
            "modifier": None,
            "rc_number": None,
        }
        # Check if the pattern is correct
        if not self.pattern:
            raise ValueError("Pattern is missing")

        version_str = self.parse()
        pattern_str = self.pattern

        while pattern_str:
            index_version = 0
            index_pattern = 0

            if pattern_str.startswith("YYYY"):
                match = re.match(r"[1-9]\d{3}", version_str)
                if match:
                    result_dict["year"] = match.group(0)
                else:
                    raise ValueError("Can't parse version by pattern")
                index_version = 4
                index_pattern = 4
            elif pattern_str.startswith("YY"):
                match = re.match(r"[1-9]\d{1,2}", version_str)
                if match:
                    result_dict["year"] = match.group(0)
                else:
                    raise ValueError("Can't parse version by pattern")
                index_version = len(result_dict["year"])
                index_pattern = 2
            elif pattern_str.startswith("0Y"):
                match = re.match(r"[1-9]\d{1,2}|(0\d)", version_str)
                if match:
                    result_dict["year"] = match.group(0)
                else:
                    raise ValueError("Can't parse version by pattern")
                index_version = len(result_dict["year"])
                index_pattern = 2
            elif pattern_str.startswith("MM"):
                try:
                    match = re.match(r"(1\d)|\d", version_str)
                    if match and 1 <= int(match.group(0)) <= 12:
                        result_dict["month"] = match.group(0)
                    else:
                        raise ValueError("Can't parse version by pattern")
                except ValueError:
                    raise ValueError("Can't parse version by pattern")
                index_version = len(result_dict["month"])
                index_pattern = 2
            elif pattern_str.startswith("0M"):
                try:
                    version = version_str[:2]
                    if 1 <= int(version) < 10 and re.fullmatch(r"(0\d)", version):
                        result_dict["month"] = version
                    elif 10 <= int(version) <= 12 and not re.fullmatch(
                        r"(0\d+)", version
                    ):
                        result_dict["month"] = version
                    else:
                        raise ValueError("Can't parse version by pattern")
                except ValueError:
                    raise ValueError("Can't parse version by pattern")
                index_version = 2
                index_pattern = 2
            elif pattern_str.startswith("DD"):
                try:
                    match = re.match(r"([1-3]\d)|\d", version_str)
                    if match and 1 <= int(match.group(0)) <= 31:
                        result_dict["day"] = match.group(0)
                    else:
                        raise ValueError("Can't parse version by pattern")
                except ValueError:
                    raise ValueError("Can't parse version by pattern")
                index_version = len(result_dict["day"])
                index_pattern = 2
            elif pattern_str.startswith("0D"):
                try:
                    version = version_str[:2]
                    if 1 <= int(version) < 10 and re.fullmatch(r"(0\d)", version):
                        result_dict["day"] = version
                    elif 10 <= int(version) <= 31 and not re.fullmatch(
                        r"(0\d+)", version
                    ):
                        result_dict["day"] = version
                    else:
                        raise ValueError("Can't parse version by pattern")
                except ValueError:
                    raise ValueError("Can't parse version by pattern")
                index_version = 2
                index_pattern = 2
            elif pattern_str.startswith("MINOR"):
                for index in range(1, len(version_str) + 1):
                    if version_str[:index].isdigit():
                        continue
                    else:
                        # First character is not number
                        if index == 1:
                            raise ValueError("Can't parse version by pattern")
                        index_version = index - 1
                        result_dict["minor"] = version_str[:index_version]
                        break
                if index_version == 0:
                    # We are on the end of string
                    index_version = len(version_str)
                    result_dict["minor"] = version_str[:index_version]
                index_pattern = 5
            elif pattern_str.startswith("MICRO"):
                for index in range(1, len(version_str) + 1):
                    if version_str[:index].isdigit():
                        continue
                    else:
                        # First character is not number
                        if index == 1:
                            raise ValueError("Can't parse version by pattern")
                        index_version = index - 1
                        result_dict["micro"] = version_str[:index_version]
                        break
                if index_version == 0:
                    # We are on the end of string
                    index_version = len(version_str)
                    result_dict["micro"] = version_str[:index_version]
                index_pattern = 5
            # MODIFIER should be the last item in pattern
            elif pattern_str == "MODIFIER":
                match = re.match(r"(.+?)(\d)+", version_str)
                if match:
                    result_dict["modifier"] = match.group(1)
                    result_dict["rc_number"] = match.group(2)
                else:
                    result_dict["modifier"] = version_str
                index_pattern = 8
                index_version = len(version_str)
            # None of the above matched, so this must be a delimiter
            else:
                index_pattern = 1
                index_version = 1
                if pattern_str[:index_pattern] != version_str[:index_version]:
                    raise ValueError("Can't parse version by pattern")

            if len(pattern_str) > index_pattern:
                pattern_str = pattern_str[index_pattern:]
            else:
                pattern_str = ""

            if len(version_str) > index_version:
                version_str = version_str[index_version:]
                if not pattern_str:
                    raise ValueError("Can't parse version by pattern")
            else:
                break

        return result_dict

    def prerelease(self) -> bool:
        """
        Check if a version is a pre-release version.

        This recognizes versions containing "rc", "pre", "beta", "alpha", and
        "dev" as being pre-release versions.
        """
        try:
            version_dict = self.split()
        except ValueError:
            # The version can't be parsed, so it's not pre-release
            return False

        if version_dict["modifier"]:
            return True

        for pre_release_filter in self.pre_release_filters:
            if pre_release_filter and pre_release_filter in self.version:
                return True

        return False

    def __eq__(self, other: Version) -> bool:
        """
        Compare two versions for equality using the calendar rules with pre-release
        support.

        Params:
            other (`CalendarVersion`): Version object to compare to

        Returns:
            (bool) True if equal, False otherwise.
        """
        try:
            version_dict_self = self.split()
            version_dict_other = other.split()
        except ValueError:
            # The version can't be split, so compare them as strings
            if self.parse() == other.parse():
                return True
            else:
                return False

        if version_dict_self == version_dict_other:
            return True

        return False

    def __lt__(self, other: Version) -> bool:
        """
        Compare two versions for lower than using the calendar rules with pre-release
        support.

        Params:
            other (`CalendarVersion`): Version object to compare to

        Returns:
            (bool) True if lower than, False otherwise.
        """
        try:
            version_dict_self = self.split()
        except ValueError:
            # The version can't be split, so we consider it lesser
            return True

        try:
            version_dict_other = other.split()
        except ValueError:
            # The version can't be split, so we consider self greater
            return False

        # Compare years
        year_self = version_dict_self["year"]
        year_other = version_dict_other["year"]
        if year_self and year_other:
            if int(year_self) < int(year_other):
                return True
            elif int(year_self) > int(year_other):
                return False

        # Compare months
        month_self = version_dict_self["month"]
        month_other = version_dict_other["month"]
        if month_self and month_other:
            if int(month_self) < int(month_other):
                return True
            elif int(month_self) > int(month_other):
                return False

        # Compare days
        day_self = version_dict_self["day"]
        day_other = version_dict_other["day"]
        if day_self and day_other:
            if int(day_self) < int(day_other):
                return True
            elif int(day_self) > int(day_other):
                return False

        # Compare minors
        minor_self = version_dict_self["minor"]
        minor_other = version_dict_other["minor"]
        if minor_self and minor_other:
            if int(minor_self) < int(minor_other):
                return True
            elif int(minor_self) > int(minor_other):
                return False

        # Compare micro
        micro_self = version_dict_self["micro"]
        micro_other = version_dict_other["micro"]
        if micro_self and micro_other:
            if int(micro_self) < int(micro_other):
                return True
            elif int(micro_self) > int(micro_other):
                return False

        rc1 = version_dict_self["modifier"]
        rc2 = version_dict_other["modifier"]
        rcn1 = version_dict_self["rc_number"]
        rcn2 = version_dict_other["rc_number"]

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
