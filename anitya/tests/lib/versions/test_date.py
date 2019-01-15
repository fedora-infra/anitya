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

import unittest
from datetime import datetime

from anitya.lib.versions import date


class DateVersionTests(unittest.TestCase):
    """Tests for the :class:`anitya.lib.versions.Date` model."""

    def test_identity_string(self):
        """Assert the generic version constant is what we expect.

        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            projects.
        """
        self.assertEqual('Date', date.DateVersion.name)

    def test_eq_no_equal(self):
        version_old = date.DateVersion(version="1.0.0")
        version_new = date.DateVersion(version="1.0.1")

        self.assertFalse(version_old == version_new)

    def test_eq_equal(self):
        version_date = date.DateVersion(version="1.0.0")

        self.assertTrue(version_date == version_date)

    def test_eq_value_missing(self):
        version_date = date.DateVersion(version="1.0.0")
        version_no_date = date.DateVersion()

        self.assertFalse(version_date == version_no_date)

    def test_newer(self):
        version_old = date.DateVersion(created_on=datetime.now())
        version_new = date.DateVersion(created_on=datetime.now())

        self.assertTrue(version_old < version_new)

    def test_older(self):
        version_old = date.DateVersion(created_on=datetime.now())
        version_new = date.DateVersion(created_on=datetime.now())

        self.assertFalse(version_new < version_old)

    def test_missing_date_self(self):
        version_no_date = date.DateVersion()
        version_date = date.DateVersion(created_on=datetime.now())

        self.assertTrue(version_no_date < version_date)

    def test_missing_date_other(self):
        version_no_date = date.DateVersion()
        version_date = date.DateVersion(created_on=datetime.now())

        self.assertFalse(version_date < version_no_date)

    def test_le(self):
        version_old = date.DateVersion(version="1.0.0", created_on=datetime.now())
        version_new = date.DateVersion(version="1.0.1", created_on=datetime.now())

        self.assertTrue(version_old <= version_new)
        self.assertTrue(version_old <= version_old)
        self.assertFalse(version_new <= version_old)
