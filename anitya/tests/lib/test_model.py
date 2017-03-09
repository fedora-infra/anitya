# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
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
#

'''
anitya tests of the model.
'''

__requires__ = ['SQLAlchemy >= 0.7']  # noqa
import pkg_resources  # noqa

import datetime
import unittest

import mock

from anitya.lib import exceptions
from anitya.tests import base
import anitya.lib.model as model


class Modeltests(base.Modeltests):
    """ Model tests. """

    def test_init_distro(self):
        """ Test the __init__ function of Distro. """
        base.create_distro(self.session)
        self.assertEqual(2, model.Distro.all(self.session, count=True))

        distros = model.Distro.all(self.session)
        self.assertEqual(distros[0].name, 'Debian')
        self.assertEqual(distros[1].name, 'Fedora')

    def test_init_project(self):
        """ Test the __init__ function of Project. """
        base.create_project(self.session)
        self.assertEqual(3, model.Project.all(self.session, count=True))

        projects = model.Project.all(self.session)
        self.assertEqual(projects[0].name, 'geany')
        self.assertEqual(projects[1].name, 'R2spec')
        self.assertEqual(projects[2].name, 'subsurface')

    def test_log_search(self):
        """ Test the Log.search function. """
        base.create_project(self.session)

        logs = model.Log.search(self.session)
        self.assertEqual(len(logs), 3)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: R2spec')
        self.assertEqual(
            logs[1].description,
            'noreply@fedoraproject.org added project: subsurface')
        self.assertEqual(
            logs[2].description,
            'noreply@fedoraproject.org added project: geany')

        logs = model.Log.search(self.session, count=True)
        self.assertEqual(logs, 3)

        from_date = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
        logs = model.Log.search(
            self.session, from_date=from_date, offset=1, limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

        logs = model.Log.search(self.session, project_name='subsurface')
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].description,
            'noreply@fedoraproject.org added project: subsurface')

    def test_distro_search(self):
        """ Test the Distro.search function. """
        base.create_distro(self.session)

        logs = model.Distro.search(self.session, '*', count=True)
        self.assertEqual(logs, 2)

        logs = model.Distro.search(self.session, 'Fed*')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = model.Distro.search(self.session, 'Fed*', page=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

        logs = model.Distro.search(self.session, 'Fed*', page='as')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, 'Fedora')

    def test_packages_by_id(self):
        """ Test the Packages.by_id function. """
        base.create_project(self.session)
        base.create_distro(self.session)
        base.create_package(self.session)

        pkg = model.Packages.by_id(self.session, 1)
        self.assertEqual(pkg.package_name, 'geany')
        self.assertEqual(pkg.distro, 'Fedora')

    def test_packages__repr__(self):
        """ Test the Packages.__repr__ function. """
        base.create_project(self.session)
        base.create_distro(self.session)
        base.create_package(self.session)

        pkg = model.Packages.by_id(self.session, 1)
        self.assertEqual(str(pkg), '<Packages(1, Fedora: geany)>')

    def test_project_all(self):
        """ Test the Project.all function. """
        base.create_project(self.session)

        projects = model.Project.all(self.session, count=True)
        self.assertEqual(projects, 3)

        projects = model.Project.all(self.session, page=2)
        self.assertEqual(len(projects), 0)

        projects = model.Project.all(self.session, page='asd')
        self.assertEqual(len(projects), 3)

    def test_project_search(self):
        """ Test the Project.search function. """
        base.create_project(self.session)

        projects = model.Project.search(self.session, '*', count=True)
        self.assertEqual(projects, 3)

        projects = model.Project.search(self.session, '*', page=2)
        self.assertEqual(len(projects), 0)

        projects = model.Project.search(self.session, '*', page='asd')
        self.assertEqual(len(projects), 3)

    def test_backend_by_name(self):
        """ Test the Backend.by_name function. """
        import anitya.lib.plugins as plugins
        plugins.load_plugins(self.session)
        backend = model.Backend.by_name(self.session, 'PyPI')
        self.assertEqual(backend.name, 'PyPI')

        backend = model.Backend.by_name(self.session, 'pypi')
        self.assertEqual(backend, None)

    def test_ecosystem_by_name(self):
        """ Test the Ecosystem.by_name function. """
        import anitya.lib.plugins as plugins
        plugins.load_plugins(self.session)
        ecosystem = model.Ecosystem.by_name(self.session, 'pypi')
        self.assertEqual(ecosystem.name, 'pypi')

        ecosystem = model.Ecosystem.by_name(self.session, 'PyPI')
        self.assertEqual(ecosystem, None)

    def test_ecosystem_backend_links(self):
        """ Test the Ecosystem.by_name function. """
        import anitya.lib.plugins as plugins
        plugins.load_plugins(self.session)
        ecosystems = model.Ecosystem.all(self.session)
        for ecosystem in ecosystems:
            self.assertEqual(ecosystem.default_backend.default_ecosystem.name,
                             ecosystem.name)

    def test_project_get_or_create(self):
        """ Test the Project.get_or_create function. """
        project = model.Project.get_or_create(
            self.session,
            name='test',
            homepage='http://test.org',
            backend='custom')
        self.assertEqual(project.name, 'test')
        self.assertEqual(project.homepage, 'http://test.org')
        self.assertEqual(project.backend, 'custom')

        self.assertRaises(
            ValueError,
            model.Project.get_or_create,
            self.session,
            name='test_project',
            homepage='http://project.test.org',
            backend='foobar'
        )


class ProjectVersionTests(base.Modeltests):
    """Tests for the :class:`model.ProjectVersion` model."""

    def test_identity_string(self):
        """Assert the generic version constant is what we expect.

        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            versions.
        """
        self.assertEqual('Generic Version', model.GENERIC_VERSION)

    def test_type_identity(self):
        """Assert the class polymorphic identity is set in the type column."""
        version = model.ProjectVersion(version='v1.0.0')
        self.assertEqual(model.GENERIC_VERSION, version.type)
        self.assertEqual(
            model.GENERIC_VERSION, model.ProjectVersion.__mapper_args__['polymorphic_identity'])

    def test_str(self):
        """Assert __str__ calls parse"""
        version = model.ProjectVersion(version='v1.0.0')
        self.assertEqual('1.0.0', str(version))

    def test_str_parse_error(self):
        """Assert __str__ calls parse"""
        version = model.ProjectVersion(version='v1.0.0')
        version.parse = mock.Mock(side_effect=exceptions.InvalidVersion('boop'))
        self.assertEqual('v1.0.0', str(version))

    def test_parse_no_v(self):
        """Assert parsing a version sans leading 'v' works."""
        version = model.ProjectVersion(version='1.0.0')
        self.assertEqual('1.0.0', version.parse())

    def test_parse_leading_v(self):
        """Assert parsing a version with a leading 'v' works."""
        version = model.ProjectVersion(version='v1.0.0')
        self.assertEqual('1.0.0', version.parse())

    def test_parse_odd_version(self):
        """Assert parsing an odd version works."""
        version = model.ProjectVersion(version='release_1_0_0')
        self.assertEqual('release_1_0_0', version.parse())

    def test_parse_v_not_alone(self):
        """Assert leading 'v' isn't stripped if it's not followed by a number."""
        version = model.ProjectVersion(version='version1.0.0')
        self.assertEqual('version1.0.0', version.parse())

    def test_prerelease(self):
        """Assert prerelease is defined and returns False"""
        version = model.ProjectVersion(version='v1.0.0')
        self.assertFalse(version.prerelease())

    def test_postrelease(self):
        """Assert postrelease is defined and returns False"""
        version = model.ProjectVersion(version='v1.0.0')
        self.assertFalse(version.postrelease())

    def test_newer(self):
        """Assert newer is functional."""
        version = model.ProjectVersion(version='v1.0.0')
        newer_version = model.ProjectVersion(version='v2.0.0')
        self.assertFalse(version.newer(newer_version))
        self.assertTrue(newer_version.newer(version))

    def test_newer_with_strings(self):
        """Assert newer handles string arguments"""
        version = model.ProjectVersion(version='v1.0.0')
        self.assertFalse(version.newer('v2.0.0'))

    def test_lt(self):
        """Assert ProjectVersion supports < comparison."""
        old_version = model.ProjectVersion(version='v1.0.0')
        new_version = model.ProjectVersion(version='v1.1.0')
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_le(self):
        """Assert ProjectVersion supports <= comparison."""
        old_version = model.ProjectVersion(version='v1.0.0')
        equally_old_version = model.ProjectVersion(version='v1.0.0')
        new_version = model.ProjectVersion(version='v1.1.0')
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert ProjectVersion supports > comparison."""
        old_version = model.ProjectVersion(version='v1.0.0')
        new_version = model.ProjectVersion(version='v1.1.0')
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert ProjectVersion supports >= comparison."""
        old_version = model.ProjectVersion(version='v1.0.0')
        equally_new_version = model.ProjectVersion(version='v1.1.0')
        new_version = model.ProjectVersion(version='v1.1.0')
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert ProjectVersion supports == comparison."""
        old_version = model.ProjectVersion(version='v1.0.0')
        new_version = model.ProjectVersion(version='v1.0.0')
        self.assertTrue(new_version == old_version)


class Pep440VersionTests(ProjectVersionTests):
    """Tests for the :class:`model.Pep440Version` model."""

    def test_identity_string(self):
        """Assert the PEP-440 version constant is what we expect.

        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            versions.
        """
        self.assertEqual('PEP-440', model.PEP440_VERSION)

    def test_type_identity(self):
        """Assert the class polymorphic identity is set in the type column."""
        version = model.Pep440Version(version='v1.0.0')
        self.assertEqual(model.PEP440_VERSION, version.type)
        self.assertEqual(
            model.PEP440_VERSION, model.Pep440Version.__mapper_args__['polymorphic_identity'])

    def test_str(self):
        """Assert __str__ calls parse"""
        version = model.Pep440Version(version='v1.0.0-alpha1')
        self.assertEqual('1.0.0a1', str(version))

    def test_str_parse_error(self):
        """Assert __str__ falls back to the raw version string with parsing fails"""
        version = model.Pep440Version(version='thisisntaversion')
        self.assertEqual('thisisntaversion', str(version))

    def test_parse_no_v(self):
        """Assert parsing a version sans leading 'v' works."""
        version = model.Pep440Version(version='1.0.0')
        self.assertEqual('1.0.0', str(version.parse()))

    def test_parse_leading_v(self):
        """Assert parsing a version with a leading 'v' works."""
        version = model.Pep440Version(version='v1.0.0')
        self.assertEqual('1.0.0', str(version.parse()))

    def test_parse_odd_version(self):
        """Assert parsing an odd version works."""
        version = model.Pep440Version(version='version1.0.0')
        self.assertRaises(exceptions.InvalidVersion, version.parse)

    def test_prerelease_false(self):
        """Assert prerelease is defined and returns False"""
        version = model.Pep440Version(version='v1.0.0')
        self.assertFalse(version.prerelease())

    def test_prerelease_true(self):
        """Assert prerelease is defined and returns False"""
        version = model.Pep440Version(version='v1.0.0-alpha1')
        self.assertTrue(version.prerelease())

    def test_postrelease_false(self):
        """Assert postrelease is defined and returns False"""
        version = model.Pep440Version(version='v1.0.0')
        self.assertFalse(version.postrelease())

    def test_postrelease_true(self):
        """Assert postrelease is defined and returns False"""
        version = model.Pep440Version(version='v1.0.0.post1')
        self.assertTrue(version.postrelease())

    def test_newer(self):
        """Assert newer is functional."""
        version = model.Pep440Version(version='v1.1.0')
        newer_version = model.Pep440Version(version='v1.11.0')
        self.assertFalse(version.newer(newer_version))
        self.assertTrue(newer_version.newer(version))

    def test_newer_with_strings(self):
        """Assert newer handles string arguments"""
        version = model.Pep440Version(version='v1.1.1')
        self.assertFalse(version.newer('v1.11.0'))
        self.assertTrue(version.newer('v1.1.0'))

    def test_lt(self):
        """Assert Pep440Version supports < comparison."""
        old_version = model.Pep440Version(version='v1.1.0')
        new_version = model.Pep440Version(version='v1.11.0')
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_le(self):
        """Assert Pep440Version supports <= comparison."""
        old_version = model.Pep440Version(version='v1.0.0')
        equally_old_version = model.Pep440Version(version='v1.0.0')
        new_version = model.Pep440Version(version='v1.1.0')
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert Pep440Version supports > comparison."""
        old_version = model.Pep440Version(version='v1.0.0')
        new_version = model.Pep440Version(version='v1.1.0')
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert Pep440Version supports >= comparison."""
        old_version = model.Pep440Version(version='v1.0.0')
        equally_new_version = model.Pep440Version(version='v1.1.0')
        new_version = model.Pep440Version(version='v1.1.0')
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert Pep440Version supports == comparison."""
        old_version = model.Pep440Version(version='v1.0.0')
        new_version = model.Pep440Version(version='v1.0.0')
        self.assertTrue(new_version == old_version)


class SemanticVersionTests(ProjectVersionTests):
    """Tests for the :class:`model.SemanticVersion` model."""

    def test_identity_string(self):
        """Assert the PEP-440 version constant is what we expect.

        .. note::
            If this test starts failing because the constant was modified, you
            *must* write a migration to change the type column on existing
            versions.
        """
        self.assertEqual('Semantic Version', model.SEMANTIC_VERSION)

    def test_type_identity(self):
        """Assert the class polymorphic identity is set in the type column."""
        version = model.SemanticVersion(version='v1.0.0')
        self.assertEqual(model.SEMANTIC_VERSION, version.type)
        self.assertEqual(
            model.SEMANTIC_VERSION, model.SemanticVersion.__mapper_args__['polymorphic_identity'])

    def test_str(self):
        """Assert __str__ calls parse"""
        version = model.SemanticVersion(version='v1.0.0-alpha1')
        self.assertEqual('1.0.0-alpha1', str(version))

    def test_str_parse_error(self):
        """Assert __str__ falls back to the raw version string with parsing fails"""
        version = model.SemanticVersion(version='thisisntaversion')
        self.assertEqual('thisisntaversion', str(version))

    def test_parse_no_v(self):
        """Assert parsing a version sans leading 'v' works."""
        version = model.SemanticVersion(version='1.0.0')
        self.assertEqual('1.0.0', str(version.parse()))

    def test_parse_leading_v(self):
        """Assert parsing a version with a leading 'v' works."""
        version = model.SemanticVersion(version='v1.0.0')
        self.assertEqual('1.0.0', str(version.parse()))

    def test_parse_odd_version(self):
        """Assert parsing an odd version raises an exception."""
        version = model.SemanticVersion(version='version1.0.0')
        self.assertRaises(exceptions.InvalidVersion, version.parse)

    def test_prerelease_false(self):
        """Assert prerelease is defined and returns False"""
        version = model.SemanticVersion(version='v1.0.0')
        self.assertFalse(version.prerelease())

    def test_prerelease_true(self):
        """Assert prerelease is defined and returns False"""
        version = model.SemanticVersion(version='v1.0.0-alpha1')
        self.assertTrue(version.prerelease())

    def test_postrelease_false(self):
        """Assert postrelease is defined and returns False"""
        version = model.SemanticVersion(version='v1.0.0-post1')
        self.assertFalse(version.postrelease())

    def test_newer(self):
        """Assert newer is functional."""
        version = model.SemanticVersion(version='v1.1.0')
        newer_version = model.SemanticVersion(version='v1.11.0')
        self.assertFalse(version.newer(newer_version))
        self.assertTrue(newer_version.newer(version))

    def test_newer_with_strings(self):
        """Assert newer handles string arguments"""
        version = model.SemanticVersion(version='v1.1.1')
        self.assertFalse(version.newer('v1.11.0'))
        self.assertTrue(version.newer('v1.1.0'))

    def test_lt(self):
        """Assert SemanticVersion supports < comparison."""
        old_version = model.SemanticVersion(version='v1.1.0')
        new_version = model.SemanticVersion(version='v1.11.0')
        self.assertTrue(old_version < new_version)
        self.assertFalse(new_version < old_version)

    def test_le(self):
        """Assert SemanticVersion supports <= comparison."""
        old_version = model.SemanticVersion(version='v1.0.0')
        equally_old_version = model.SemanticVersion(version='v1.0.0')
        new_version = model.SemanticVersion(version='v1.1.0')
        self.assertTrue(old_version <= new_version)
        self.assertTrue(old_version <= equally_old_version)
        self.assertFalse(new_version <= old_version)

    def test_gt(self):
        """Assert SemanticVersion supports > comparison."""
        old_version = model.SemanticVersion(version='v1.0.0')
        new_version = model.SemanticVersion(version='v1.1.0')
        self.assertTrue(new_version > old_version)
        self.assertFalse(old_version > new_version)

    def test_ge(self):
        """Assert SemanticVersion supports >= comparison."""
        old_version = model.SemanticVersion(version='v1.0.0')
        equally_new_version = model.SemanticVersion(version='v1.1.0')
        new_version = model.SemanticVersion(version='v1.1.0')
        self.assertFalse(old_version >= new_version)
        self.assertTrue(new_version >= equally_new_version)
        self.assertTrue(new_version >= old_version)

    def test_eq(self):
        """Assert SemanticVersion supports == comparison."""
        old_version = model.SemanticVersion(version='v1.0.0')
        new_version = model.SemanticVersion(version='v1.0.0')
        self.assertTrue(new_version == old_version)


if __name__ == '__main__':
    unittest.main(verbosity=2)
