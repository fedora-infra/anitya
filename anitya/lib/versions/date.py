# -*- coding: utf-8 -*-
#
# Copyright © 2018  Red Hat, Inc.
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
This adds support for comparing project versions by date created.
"""
import functools

from .base import Version


@functools.total_ordering
class DateVersion(Version):
    """
    This class implements a Date version plugin.

    It sorts versions by date created.
    """

    name = u'Date'

    def __eq__(self, other):
        """
        Compare two versions for equality by date created.

        Returns:
            bool: True if the ```created_on``` attributes are equal.
        """
        return self.created_on == other.created_on

    def __lt__(self, other):
        """
        Compare two versions by date created.

        Returns:
            bool: True if the ```self.created_on``` attribute is lesser
            than ```other.created_on```.
        """
        if not self.created_on:
            # None < value
            return True

        if not other.created_on:
            # None < value
            return False

        return self.created_on < other.created_on
