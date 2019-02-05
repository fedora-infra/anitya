# -*- coding: utf-8 -*-
#
# Copyright © 2017 Red Hat, Inc.
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

import arrow

from anitya.lib import exceptions


class AnityaInvalidMappingTests(unittest.TestCase):
    """ Tests for :class:`exceptions.AnityaInvalidMappingException`."""

    def test_message(self):
        """Assert message creation"""
        pkgname = "foo"
        distro = "fedora"
        found_pkgname = "bar"
        found_distro = "debian"
        project_id = 1
        project_name = "Cthulhu"
        link = "link"
        exp = (
            "Could not edit the mapping of {pkgname} on "
            "{distro}, there is already a package {found_pkgname} on "
            '{found_distro} as part of the project <a href="{link}">'
            "{project_name}</a>.".format(
                pkgname=pkgname,
                distro=distro,
                found_pkgname=found_pkgname,
                found_distro=found_distro,
                project_id=project_id,
                project_name=project_name,
                link=None,
            )
        )
        e = exceptions.AnityaInvalidMappingException(
            pkgname, distro, found_pkgname, found_distro, project_id, project_name
        )
        self.assertEqual(exp, e.message)

        exp = (
            "Could not edit the mapping of {pkgname} on "
            "{distro}, there is already a package {found_pkgname} on "
            '{found_distro} as part of the project <a href="{link}">'
            "{project_name}</a>.".format(
                pkgname=pkgname,
                distro=distro,
                found_pkgname=found_pkgname,
                found_distro=found_distro,
                project_id=project_id,
                project_name=project_name,
                link=link,
            )
        )
        e = exceptions.AnityaInvalidMappingException(
            pkgname, distro, found_pkgname, found_distro, project_id, project_name, link
        )
        self.assertEqual(exp, e.message)


class InvalidVersionTests(unittest.TestCase):
    """Tests for :class:`exceptions.InvalidVersion`."""

    def test_str(self):
        """Assert the __str__ method provides a human-readable value."""
        e = exceptions.InvalidVersion("notaversion")
        self.assertEqual('Invalid version "notaversion"', str(e))

    def test_str_with_wrapped_exception(self):
        """Assert the __str__ method provides a human-readable value including the exception."""
        e = exceptions.InvalidVersion("notaversion", IOError("womp womp"))
        self.assertEqual('Invalid version "notaversion": womp womp', str(e))


class RateLimitExceptionTests(unittest.TestCase):
    """Tests for :class:`exceptions.RateLimitException`."""

    def test_reset_time(self):
        """Assert the property returns valid value."""
        time = "2018-08-24T09:36:15Z"
        exp = arrow.get(time)
        e = exceptions.RateLimitException(time)
        self.assertEqual(exp, e.reset_time)

    def test_str(self):
        """Assert the __str__ method provides a human-readable value."""
        time = "2018-08-24T09:36:15Z"
        exp = 'Rate limit was reached. Will be reset in "2018-08-24T09:36:15+00:00".'
        e = exceptions.RateLimitException(time)

        self.assertEqual(exp, str(e))
