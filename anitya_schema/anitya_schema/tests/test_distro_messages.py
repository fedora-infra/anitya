# Copyright (C) 2018  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Unit tests for the distribution related message schema."""

import unittest
import mock

from anitya_schema import DistroCreated, DistroEdited, DistroDeleted


class TestDistroCreated(unittest.TestCase):
    """Tests for anitya_schema.distro_messages.DistroCreated class."""

    def setUp(self):
        """Set up the tests."""
        self.message = DistroCreated()

    @mock.patch(
        "anitya_schema.distro_messages.DistroCreated.summary",
        new_callable=mock.PropertyMock,
    )
    def test__str__(self, mock_property):
        """Assert that correct string is returned."""
        mock_property.return_value = "Dummy"

        self.assertEqual(self.message.__str__(), "Dummy")

    @mock.patch(
        "anitya_schema.distro_messages.DistroCreated.distro_name",
        new_callable=mock.PropertyMock,
    )
    def test_summary(self, mock_property):
        """Assert that correct summary string is returned."""
        mock_property.return_value = "Dummy"

        exp = "A new distribution, Dummy, was added to release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_agent(self):
        """Assert that agent is returned."""
        self.message.body = {"message": {"agent": "Dummy"}}

        self.assertEqual(self.message.agent, "Dummy")

    def test_distro_name(self):
        """Assert that distro name is returned."""
        self.message.body = {"distro": {"name": "Dummy"}}

        self.assertEqual(self.message.distro_name, "Dummy")

    def test_distro_url(self):
        """Assert that distro url is returned."""
        self.message.body = {"distro": {"name": "Dummy"}}

        self.assertEqual(
            self.message.distro_url, "https://release-monitoring.org/distros/Dummy"
        )


class TestDistroEdited(unittest.TestCase):
    """Tests for anitya_schema.distro_messages.DistroEdited class."""

    def setUp(self):
        """Set up the tests."""
        self.message = DistroEdited()

    @mock.patch(
        "anitya_schema.distro_messages.DistroEdited.summary",
        new_callable=mock.PropertyMock,
    )
    def test__str__(self, mock_property):
        """Assert that correct string is returned."""
        mock_property.return_value = "Dummy"

        self.assertEqual(self.message.__str__(), "Dummy")

    @mock.patch(
        "anitya_schema.distro_messages.DistroEdited.distro_name_new",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "anitya_schema.distro_messages.DistroEdited.distro_name_old",
        new_callable=mock.PropertyMock,
    )
    def test_summary(self, mock_old_name, mock_new_name):
        """Assert that correct summary string is returned."""
        mock_new_name.return_value = "New name"
        mock_old_name.return_value = "Old name"

        exp = "The name of the Old name distribution changed to New name."
        self.assertEqual(self.message.summary, exp)

    def test_agent(self):
        """Assert that agent is returned."""
        self.message.body = {"message": {"agent": "Dummy"}}

        self.assertEqual(self.message.agent, "Dummy")

    def test_name_new(self):
        """Assert that new_name string is returned."""
        self.message.body = {"message": {"new": "Dummy"}}

        self.assertEqual(self.message.distro_name_new, "Dummy")

    def test_url_new(self):
        """Assert that correct anitya url is returned."""
        self.message.body = {"message": {"new": "Dummy"}}

        self.assertEqual(
            self.message.distro_url_new, "https://release-monitoring.org/distros/Dummy"
        )

    def test_name_old(self):
        """Assert that old_name string is returned."""
        self.message.body = {"message": {"old": "Dummy"}}

        self.assertEqual(self.message.distro_name_old, "Dummy")

    def test_url_old(self):
        """Assert that correct anitya url is returned."""
        self.message.body = {"message": {"old": "Dummy"}}

        self.assertEqual(
            self.message.distro_url_old, "https://release-monitoring.org/distros/Dummy"
        )


class TestDistroDeleted(unittest.TestCase):
    """Tests for anitya_schema.distro_messages.DistroDeleted class."""

    def setUp(self):
        """Set up the tests."""
        self.message = DistroDeleted()

    @mock.patch(
        "anitya_schema.distro_messages.DistroDeleted.summary",
        new_callable=mock.PropertyMock,
    )
    def test__str__(self, mock_property):
        """Assert that correct string is returned."""
        mock_property.return_value = "Dummy"

        self.assertEqual(self.message.__str__(), "Dummy")

    @mock.patch(
        "anitya_schema.distro_messages.DistroDeleted.distro_name",
        new_callable=mock.PropertyMock,
    )
    def test_summary(self, mock_property):
        """Assert that correct summary string is returned."""
        mock_property.return_value = "Dummy"

        exp = "The Dummy distribution was removed from release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_agent(self):
        """Assert that agent is returned."""
        self.message.body = {"message": {"agent": "Dummy"}}

        self.assertEqual(self.message.agent, "Dummy")

    def test_distro_name(self):
        """Assert that distro name is returned."""
        self.message.body = {"distro": {"name": "Dummy"}}

        self.assertEqual(self.message.distro_name, "Dummy")

    def test_distro_url(self):
        """Assert that distro url is returned."""
        self.message.body = {"distro": {"name": "Dummy"}}

        self.assertEqual(
            self.message.distro_url, "https://release-monitoring.org/distros/Dummy"
        )
