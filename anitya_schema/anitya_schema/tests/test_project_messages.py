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
"""Unit tests for the project related message schema."""

import unittest
import mock

from anitya_schema import (
    ProjectCreated,
    ProjectDeleted,
    ProjectEdited,
    ProjectFlag,
    ProjectFlagSet,
    ProjectMapCreated,
    ProjectMapDeleted,
    ProjectMapEdited,
    ProjectVersionDeleted,
    ProjectVersionUpdated,
)


class TestProjectCreated(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectCreated class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectCreated()

    @mock.patch(
        'anitya_schema.project_messages.ProjectCreated.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectCreated.name',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """ Assert that correct summary string is returned. """
        mock_property.return_value = 'Dummy'

        exp = "A new project, Dummy, was added to release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')


class TestProjectEdited(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectEdited class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectEdited()

    @mock.patch(
        'anitya_schema.project_messages.ProjectEdited.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectEdited.name',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """ Assert that correct summary string is returned. """
        mock_property.return_value = 'Dummy'

        exp = "A project, Dummy, was edited in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')


class TestProjectDeleted(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectDeleted class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectDeleted()

    @mock.patch(
        'anitya_schema.project_messages.ProjectDeleted.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectDeleted.name',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """ Assert that correct summary string is returned. """
        mock_property.return_value = 'Dummy'

        exp = "A project, Dummy, was deleted in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')


class TestProjectFlag(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectFlag class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectFlag()

    @mock.patch(
        'anitya_schema.project_messages.ProjectFlag.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectFlag.name',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """ Assert that correct summary string is returned. """
        mock_property.return_value = 'Dummy'

        exp = "A flag was created on project Dummy in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')


class TestProjectFlagSet(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectFlagSet class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectFlagSet()

    @mock.patch(
        'anitya_schema.project_messages.ProjectFlagSet.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectFlagSet.flag',
        new_callable=mock.PropertyMock
    )
    @mock.patch(
        'anitya_schema.project_messages.ProjectFlagSet.state',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_state, mock_flag):
        """ Assert that correct summary string is returned. """
        mock_flag.return_value = '007'
        mock_state.return_value = 'closed'

        exp = "A flag '007' was closed in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_flag(self):
        """ Assert that flag string is returned. """
        self.message.body = {
            "message": {
                "flag": "Dummy"
            }
        }

        self.assertEqual(self.message.flag, 'Dummy')

    def test_state(self):
        """ Assert that state string is returned. """
        self.message.body = {
            "message": {
                "state": "Dummy"
            }
        }

        self.assertEqual(self.message.state, 'Dummy')


class TestProjectMapCreated(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectMapCreated class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectMapCreated()

    @mock.patch(
        'anitya_schema.project_messages.ProjectMapCreated.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectMapCreated.name',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """ Assert that correct summary string is returned. """
        mock_property.return_value = 'Dummy'

        exp = "A new mapping was created for project Dummy in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')


class TestProjectMapEdited(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectMapEdited class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectMapEdited()

    @mock.patch(
        'anitya_schema.project_messages.ProjectMapEdited.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectMapEdited.name',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """ Assert that correct summary string is returned. """
        mock_property.return_value = 'Dummy'

        exp = "A mapping for project Dummy was edited in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')


class TestProjectMapDeleted(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectMapDeleted class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectMapDeleted()

    @mock.patch(
        'anitya_schema.project_messages.ProjectMapDeleted.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectMapDeleted.name',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_property):
        """ Assert that correct summary string is returned. """
        mock_property.return_value = 'Dummy'

        exp = "A mapping for project Dummy was deleted in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')


class TestProjectVersionUpdated(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectVersionUpdated class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectVersionUpdated()

    @mock.patch(
        'anitya_schema.project_messages.ProjectVersionUpdated.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectVersionUpdated.name',
        new_callable=mock.PropertyMock
    )
    @mock.patch(
        'anitya_schema.project_messages.ProjectVersionUpdated.version',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_version, mock_name):
        """ Assert that correct summary string is returned. """
        mock_name.return_value = 'Dummy'
        mock_version.return_value = '1.0.0'

        exp = "A new version '1.0.0' was found for project Dummy in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')

    def test_version(self):
        """ Assert that version string is returned. """
        self.message.body = {
            "message": {
                "upstream_version": "1.0.0"
            }
        }

        self.assertEqual(self.message.version, '1.0.0')


class TestProjectVersionDeleted(unittest.TestCase):
    """ Tests for anitya_schema.project_messages.ProjectVersionDeleted class. """

    def setUp(self):
        """ Set up the tests. """
        self.message = ProjectVersionDeleted()

    @mock.patch(
        'anitya_schema.project_messages.ProjectVersionDeleted.summary',
        new_callable=mock.PropertyMock
    )
    def test__str__(self, mock_property):
        """ Assert that correct string is returned. """
        mock_property.return_value = 'Dummy'

        self.assertEqual(self.message.__str__(), 'Dummy')

    @mock.patch(
        'anitya_schema.project_messages.ProjectVersionDeleted.name',
        new_callable=mock.PropertyMock
    )
    @mock.patch(
        'anitya_schema.project_messages.ProjectVersionDeleted.version',
        new_callable=mock.PropertyMock
    )
    def test_summary(self, mock_version, mock_name):
        """ Assert that correct summary string is returned. """
        mock_name.return_value = 'Dummy'
        mock_version.return_value = '1.0.0'

        exp = "A version '1.0.0' was deleted in project Dummy in release-monitoring."
        self.assertEqual(self.message.summary, exp)

    def test_name(self):
        """ Assert that name string is returned. """
        self.message.body = {
            "project": {
                "name": "Dummy"
            }
        }

        self.assertEqual(self.message.name, 'Dummy')

    def test_version(self):
        """ Assert that version string is returned. """
        self.message.body = {
            "message": {
                "version": "1.0.0"
            }
        }

        self.assertEqual(self.message.version, '1.0.0')
