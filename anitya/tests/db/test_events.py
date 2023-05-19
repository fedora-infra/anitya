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

from anitya.db import Session, models
from anitya.tests.base import DatabaseTestCase


class SetEcosystemBackendTests(DatabaseTestCase):
    def test_set_backend(self):
        """Assert the ecosystem gets set to correct backend."""
        project = models.Project(
            name="requests", homepage="https://pypi.org/requests", backend="PyPI"
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual("pypi", project.ecosystem_name)

        project.backend = "crates.io"
        Session.add(project)
        Session.commit()

        self.assertEqual("crates.io", project.ecosystem_name)

    def test_set_backend_no_change(self):
        """Assert the ecosystem is not changed when the backend is set to same value."""
        project = models.Project(
            name="requests", homepage="https://pypi.org/requests", backend="PyPI"
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual("pypi", project.ecosystem_name)

        project.backend = "PyPI"
        Session.add(project)
        Session.commit()

        self.assertEqual("pypi", project.ecosystem_name)

    def test_set_wrong_backend(self):
        """Assert the ecosystem will not be set if backend is not related to any ecosystem."""
        project = models.Project(
            name="requests", homepage="https://pypi.org/requests", backend="PyPI"
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual("pypi", project.ecosystem_name)

        project.backend = "GitHub"
        Session.add(project)
        Session.commit()

        self.assertEqual("https://pypi.org/requests", project.ecosystem_name)


class SetEcosystemHomepageTests(DatabaseTestCase):
    def test_set_backend(self):
        """Assert the ecosystem gets set to correct backend, even when homepage is changed."""
        project = models.Project(
            name="requests", homepage="https://pypi.org/requests", backend="PyPI"
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual("pypi", project.ecosystem_name)

        project.homepage = "https://example.com"
        Session.add(project)
        Session.commit()
        self.assertEqual("pypi", project.ecosystem_name)

    def test_set_homepage(self):
        """Assert the ecosystem will be set to homepage when backend
        is not related to any ecosystem."""
        project = models.Project(
            name="requests", homepage="https://pypi.org/requests", backend="GitHub"
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual("https://pypi.org/requests", project.ecosystem_name)

        project.homepage = "https://example.com"
        Session.add(project)
        Session.commit()
        self.assertEqual("https://example.com", project.ecosystem_name)

    def test_set_homepage_no_change(self):
        """Assert the ecosystem will not be changed
        when the homepage is set to same value."""
        project = models.Project(
            name="requests", homepage="https://pypi.org/requests", backend="GitHub"
        )

        Session.add(project)
        Session.commit()

        project = models.Project.query.all()[0]
        self.assertEqual("https://pypi.org/requests", project.ecosystem_name)

        project.homepage = "https://pypi.org/requests"
        Session.add(project)
        Session.commit()
        self.assertEqual("https://pypi.org/requests", project.ecosystem_name)
