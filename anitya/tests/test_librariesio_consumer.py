# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2017-2019 Red Hat, Inc.
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""
Tests for the libraries.io SSE client.
"""

import unittest
from unittest import mock

import sseclient

from anitya import config
from anitya.db import Project
from anitya.lib.exceptions import AnityaPluginException, AnityaException
from anitya.librariesio_consumer import LibrariesioConsumer
from anitya.tests.base import DatabaseTestCase


class LibrariesioConsumerTests(DatabaseTestCase):
    """
    Test class for `anitya.librariesio_consumer.LibrariesioConsumer` class.

    Attributes:
        client (`anitya.librariesio_consumer.LibrariesioConsumer``): librariesio SSE client.
    """

    def setUp(self):
        """
        Set up the test environments.
        """
        super(LibrariesioConsumerTests, self).setUp()

        self.client = LibrariesioConsumer()

    def test_init(self):
        """Assert that correct values are initialized."""

        self.assertEqual(self.client.feed, config.config["SSE_FEED"])
        self.assertEqual(
            self.client.whitelist, config.config["LIBRARIESIO_PLATFORM_WHITELIST"]
        )

    @mock.patch("anitya.librariesio_consumer._log")
    def test_invalid_json(self, mock_log):
        """Assert that log message is logged when invalid json is received."""
        event = sseclient.Event(data="Invalid JSON")

        self.client.process_message(event)

        self.assertIn(
            "Dropping librariesio update message. Invalid json 'Invalid JSON'.",
            mock_log.warning.call_args_list[0][0][0],
        )

    @mock.patch("anitya.librariesio_consumer._log")
    def test_unknown_ecosystem(self, mock_log):
        """Assert that log message is logged when unknown ecosystem is received."""
        event = sseclient.Event(
            data="{"
            '"name": "test",'
            '"platform": "unknown",'
            '"version": "1.0",'
            '"package_manager_url": "https://homepage.net"'
            "}"
        )
        self.client.process_message(event)

        self.assertIn(
            "Dropped librariesio update to 1.0 for test (https://homepage.net) since"
            " it is on the unsupported unknown platform",
            mock_log.debug.call_args_list[0][0][0],
        )

    def test_new_project_configured_off(self):
        """libraries.io events shouldn't create projects if the configuration is off."""
        event = sseclient.Event(
            data="{"
            '"name": "test",'
            '"platform": "PyPi",'
            '"version": "1.0",'
            '"package_manager_url": "https://homepage.net"'
            "}"
        )

        with mock.patch.object(self.client, "whitelist", []):
            self.client.process_message(event)
        self.assertEqual(0, self.session.query(Project).count())

    def test_new_project_configured_on(self):
        """Assert that a libraries.io event about an unknown project creates that project"""
        event = sseclient.Event(
            data="{"
            '"name": "ImageMetaTag",'
            '"platform": "PyPi",'
            '"version": "0.6.9",'
            '"package_manager_url": "https://pypi.org/project/ImageMetaTag/"'
            "}"
        )

        with mock.patch.object(self.client, "whitelist", ["pypi"]):
            self.client.process_message(event)
        self.assertEqual(1, self.session.query(Project).count())
        project = self.session.query(Project).first()
        self.assertEqual("ImageMetaTag", project.name)
        self.assertEqual("pypi", project.ecosystem_name)
        self.assertEqual("0.6.9", project.latest_version)

    @mock.patch("anitya.librariesio_consumer._log")
    @mock.patch("anitya.lib.utilities.create_project")
    def test_new_project_failure(self, mock_create, mock_log):
        """Assert failures to create projects are logged as errors."""
        mock_create.side_effect = AnityaException("boop")
        event = sseclient.Event(
            data="{"
            '"name": "ImageMetaTag",'
            '"platform": "PyPi",'
            '"version": "0.6.9",'
            '"package_manager_url": "https://pypi.org/project/ImageMetaTag/"'
            "}"
        )

        with mock.patch.object(self.client, "whitelist", ["pypi"]):
            self.client.process_message(event)
        self.assertEqual(0, self.session.query(Project).count())
        self.assertIn(
            "A new project was discovered via libraries.io, ImageMetaTag,"
            ' but we failed with "boop"',
            mock_log.error.call_args_list[0][0][0],
        )

    def test_existing_project(self):
        """Assert that a libraries.io event about an existing project updates that project"""
        project = Project(
            name="ImageMetaTag",
            homepage="https://pypi.org/project/ImageMetaTag/",
            ecosystem_name="pypi",
            backend="PyPI",
        )
        self.session.add(project)
        self.session.commit()
        event = sseclient.Event(
            data="{"
            '"name": "ImageMetaTag",'
            '"platform": "PyPi",'
            '"version": "0.6.9",'
            '"package_manager_url": "https://pypi.org/project/ImageMetaTag/"'
            "}"
        )

        self.assertEqual(1, self.session.query(Project).count())
        self.client.process_message(event)
        self.assertEqual(1, self.session.query(Project).count())
        project = self.session.query(Project).first()
        self.assertEqual("ImageMetaTag", project.name)
        self.assertEqual("pypi", project.ecosystem_name)
        self.assertEqual("0.6.9", project.latest_version)

    @mock.patch("anitya.librariesio_consumer.utilities.check_project_release")
    def test_existing_project_check_failure(self, mock_check):
        """Assert that when an existing project fails a version check nothing happens"""
        mock_check.side_effect = AnityaPluginException()
        project = Project(
            name="ImageMetaTag",
            homepage="https://pypi.python.org/pypi/ImageMetaTag",
            ecosystem_name="pypi",
            backend="PyPI",
        )
        self.session.add(project)
        self.session.commit()
        event = sseclient.Event(
            data="{"
            '"name": "ImageMetaTag",'
            '"platform": "PyPi",'
            '"version": "0.6.9",'
            '"package_manager_url": "https://pypi.org/project/ImageMetaTag/"'
            "}"
        )

        self.assertEqual(1, self.session.query(Project).count())
        self.client.process_message(event)
        self.assertEqual(1, self.session.query(Project).count())
        project = self.session.query(Project).first()
        self.assertIs(project.latest_version, None)

    @mock.patch("anitya.librariesio_consumer._log")
    def test_mismatched_versions(self, mock_log):
        """Assert when libraries.io and Anitya disagree on version, it's logged"""
        project = Project(
            name="ImageMetaTag",
            homepage="https://pypi.org/project/ImageMetaTag/",
            ecosystem_name="pypi",
            backend="PyPI",
        )
        self.session.add(project)
        self.session.commit()
        event = sseclient.Event(
            data="{"
            '"name": "ImageMetaTag",'
            '"platform": "PyPi",'
            '"version": "0.6.11",'
            '"package_manager_url": "https://pypi.org/project/ImageMetaTag/"'
            "}"
        )
        self.client.process_message(event)
        project = self.session.query(Project).first()
        self.assertEqual("0.6.9", project.latest_version)
        self.assertIn(
            "libraries.io has found an update (version 0.6.11) for project ImageMetaTag",
            mock_log.info.call_args_list[0][0][0],
        )


if __name__ == "__main__":
    unittest.main()
