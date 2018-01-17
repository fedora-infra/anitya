# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright © 2018 Red Hat, Inc.
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
"""Tests for the :mod:`anitya.db.events` module."""

from anitya.db import models, Session
from anitya.tests.base import DatabaseTestCase


class SetEcosystemTests(DatabaseTestCase):

    def test_set_manually(self):
        """Assert the ecosystem can be set manually."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.org/requests',
            ecosystem_name='crates.io',
            backend='PyPI',
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual('crates.io', project.ecosystem_name)

    def test_set_automatically(self):
        """Assert the ecosystem gets set automatically based on the backend."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.org/requests',
            backend='PyPI',
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual('pypi', project.ecosystem_name)

    def test_invalid(self):
        """Assert invalid ecosystems raise an exception."""
        project = models.Project(
            name='requests',
            homepage='https://pypi.org/requests',
            backend='PyPI',
            ecosystem_name='invalid_ecosystem',
        )

        Session.add(project)
        self.assertRaises(ValueError, Session.commit)
