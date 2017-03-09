# -*- coding: utf-8 -*-
#
# Copyright © 2017  Red Hat, Inc.
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
Tests for :mod:`anitya.lib.versions`
"""
from __future__ import absolute_import, unicode_literals

from anitya.lib import events, model
from anitya.tests import base


class SetVersionTypesTests(base.Modeltests):
    """Tests for the :func:`events.set_version_types` function"""

    def test_set_version_types_new(self):
        """Assert new projects have their version type adjusted"""
        session = self.session()
        project = model.Project(
            name='test',
            homepage='http://www.example.com/',
            backend='PyPI',
            version_scheme=model.PEP440_VERSION,
        )
        version = model.ProjectVersion(project=project, version='1.0.0')

        session.add(project)
        session.add(version)

        self.assertEqual(model.GENERIC_VERSION, version.type)
        events.set_version_types(session, None, None)
        self.assertEqual(model.PEP440_VERSION, version.type)

    def test_set_version_types_dirty(self):
        """Assert dirty projects have their version type adjusted"""
        session = self.session()
        project = model.Project(
            name='test',
            homepage='http://www.example.com/',
            backend='PyPI',
            version_scheme=model.GENERIC_VERSION,
            ecosystem_name='pypi',
        )
        version = model.ProjectVersion(project=project, version='1.0.0')
        session.add(project)
        session.add(version)
        session.commit()

        # Reload the object and modify it so it enters the dirty state
        project = session.query(model.Project).first()
        self.assertEqual(model.GENERIC_VERSION, project.versions_obj[0].type)
        project.version_scheme = model.PEP440_VERSION
        session.add(project)
        events.set_version_types(session, None, None)
        self.assertEqual(model.PEP440_VERSION, project.versions_obj[0].type)
