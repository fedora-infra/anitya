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
"""Tests for the :mod:`anitya.lib.utilities` module."""

from sqlalchemy.exc import SQLAlchemyError
import mock

from anitya.db import models
from anitya.lib import utilities, exceptions
from anitya.lib.exceptions import AnityaException, ProjectExists
from anitya.tests.base import DatabaseTestCase, create_distro, create_project


class CreateProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.create_project` function."""

    def test_create_project(self):
        """ Test the create_project function of Distro. """
        create_distro(self.session)
        self.assertEqual(2, models.Distro.all(self.session, count=True))

        utilities.create_project(
            self.session,
            name='geany',
            homepage='https://www.geany.org/',
            version_url='https://www.geany.org/Download/Releases',
            regex='DEFAULT',
            user_id='noreply@fedoraproject.org',
        )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 1)
        self.assertEqual(project_objs[0].name, 'geany')
        self.assertEqual(project_objs[0].homepage, 'https://www.geany.org/')

        self.assertRaises(
            ProjectExists,
            utilities.create_project,
            self.session,
            name='geany',
            homepage='https://www.geany.org/',
            version_url='https://www.geany.org/Download/Releases',
            regex='DEFAULT',
            user_id='noreply@fedoraproject.org',
        )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 1)
        self.assertEqual(project_objs[0].name, 'geany')
        self.assertEqual(project_objs[0].homepage, 'https://www.geany.org/')

    def test_create_project_general_error(self):
        """Assert general SQLAlchemy exceptions result in AnityaException."""
        with mock.patch.object(
                self.session, 'flush', mock.Mock(side_effect=[SQLAlchemyError(), None])):
            self.assertRaises(
                AnityaException,
                utilities.create_project,
                self.session,
                name='geany',
                homepage='https://www.geany.org/',
                version_url='https://www.geany.org/Download/Releases',
                regex='DEFAULT',
                user_id='noreply@fedoraproject.org',
            )


class EditProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.edit_project` function."""

    def test_edit_project(self):
        """ Test the edit_project function of Distro. """
        create_distro(self.session)
        create_project(self.session)

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, 'geany')
        self.assertEqual(project_objs[0].homepage, 'https://www.geany.org/')
        self.assertEqual(project_objs[1].name, 'R2spec')
        self.assertEqual(project_objs[2].name, 'subsurface')

        utilities.edit_project(
            self.session,
            project=project_objs[0],
            name=project_objs[0].name,
            homepage='https://www.geany.org',
            backend='PyPI',
            version_scheme='Date',
            version_url=None,
            version_prefix=None,
            regex=None,
            insecure=False,
            user_id='noreply@fedoraproject.org')

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, 'geany')
        self.assertEqual(project_objs[0].homepage, 'https://www.geany.org')
        self.assertEqual(project_objs[0].backend, 'PyPI')

    def test_edit_project_creating_duplicate(self):
        """
        Assert that attempting to edit a project and creating a duplicate fails
        """
        create_distro(self.session)
        create_project(self.session)

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, 'geany')
        self.assertEqual(project_objs[0].homepage, 'https://www.geany.org/')
        self.assertEqual(project_objs[1].name, 'R2spec')
        self.assertEqual(project_objs[2].name, 'subsurface')

        self.assertRaises(
            AnityaException,
            utilities.edit_project,
            self.session,
            project=project_objs[2],
            name='geany',
            homepage='https://www.geany.org/',
            backend=project_objs[2].backend,
            version_scheme=project_objs[2].version_scheme,
            version_url=project_objs[2].version_url,
            version_prefix=None,
            regex=project_objs[2].regex,
            insecure=False,
            user_id='noreply@fedoraproject.org',
        )


class CheckProjectReleaseTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.check_project_release` function."""

    @mock.patch('anitya.db.models.Project')
    def test_check_project_release_no_backend(self, mock_project):
        """ Test the check_project_release function for Project. """
        m_project = mock_project.return_value
        m_project.backend.return_value = 'dummy'
        self.assertRaises(
            AnityaException,
            utilities.check_project_release,
            m_project,
            self.session
        )

    @mock.patch(
        'anitya.lib.backends.npmjs.NpmjsBackend.get_versions',
        return_value=['1.0.0', '0.9.9', '0.9.8'])
    def test_check_project_release_backend(self, mock_method):
        """ Test the check_project_release function for Project. """
        project = utilities.create_project(
            self.session,
            name='pypi_and_npm',
            homepage='https://example.com/not-a-real-npmjs-project',
            backend='npmjs',
            user_id='noreply@fedoraproject.org'
        )
        versions = utilities.check_project_release(
            project,
            self.session,
            test=True
        )
        self.assertEqual(versions, ['1.0.0', '0.9.9', '0.9.8'])

    @mock.patch(
        'anitya.lib.backends.npmjs.NpmjsBackend.get_versions',
        mock.Mock(side_effect=exceptions.AnityaPluginException("")))
    def test_check_project_release_plugin_exception(self):
        """ Test the check_project_release function for Project. """
        project = utilities.create_project(
            self.session,
            name='pypi_and_npm',
            homepage='https://example.com/not-a-real-npmjs-project',
            backend='npmjs',
            user_id='noreply@fedoraproject.org'
        )
        self.assertRaises(
            exceptions.AnityaPluginException,
            utilities.check_project_release,
            project,
            self.session,
        )

    @mock.patch(
        'anitya.lib.backends.npmjs.NpmjsBackend.get_versions',
        return_value=['1.0.0'])
    def test_check_project_release_no_new_version(self, mock_method):
        """ Test the check_project_release function for Project. """
        project = utilities.create_project(
            self.session,
            name='pypi_and_npm',
            homepage='https://example.com/not-a-real-npmjs-project',
            backend='npmjs',
            user_id='noreply@fedoraproject.org',
        )
        project.latest_version = '1.0.0'
        version = models.ProjectVersion(
            version='1.0.0',
            project_id=project.id
        )
        self.session.add(version)
        self.session.commit()

        utilities.check_project_release(
            project,
            self.session
        )

        self.assertEqual(project.latest_version, '1.0.0')
        self.assertEqual(
            project.logs,
            'No new version found'
        )

    @mock.patch(
        'anitya.lib.backends.npmjs.NpmjsBackend.get_versions',
        return_value=['1.0.0', '0.9.9', '0.9.8'])
    def test_check_project_release_new_version(self, mock_method):
        """ Test the check_project_release function for Project. """
        project = utilities.create_project(
            self.session,
            name='pypi_and_npm',
            homepage='https://example.com/not-a-real-npmjs-project',
            backend='npmjs',
            user_id='noreply@fedoraproject.org',
            version_scheme='RPM',
        )
        utilities.check_project_release(
            project,
            self.session
        )
        versions = project.get_sorted_version_objects()
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].version, '1.0.0')


class MapProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.map_project` function."""

    def test_map_project(self):
        """ Test the map_project function of Distro. """
        create_distro(self.session)
        create_project(self.session)

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, 'geany')
        self.assertEqual(len(project_obj.packages), 0)

        # Map `geany` project to CentOS
        utilities.map_project(
            self.session,
            project=project_obj,
            package_name='geany',
            distribution='CentOS',
            user_id='noreply@fedoraproject.org',
            old_package_name=None,
        )
        self.session.commit()

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, 'geany')
        self.assertEqual(len(project_obj.packages), 1)
        self.assertEqual(project_obj.packages[0].package_name, 'geany')
        self.assertEqual(project_obj.packages[0].distro, 'CentOS')

        # Map `geany` project to CentOS, exactly the same way
        utilities.map_project(
            self.session,
            project=project_obj,
            package_name='geany2',
            distribution='CentOS',
            user_id='noreply@fedoraproject.org',
            old_package_name=None,
        )
        self.session.commit()

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, 'geany')
        self.assertEqual(len(project_obj.packages), 2)
        self.assertEqual(project_obj.packages[0].package_name, 'geany')
        self.assertEqual(project_obj.packages[0].distro, 'CentOS')
        self.assertEqual(project_obj.packages[1].package_name, 'geany2')
        self.assertEqual(project_obj.packages[1].distro, 'CentOS')

        # Edit the mapping of the `geany` project to Fedora
        utilities.map_project(
            self.session,
            project=project_obj,
            package_name='geany3',
            distribution='Fedora',
            user_id='noreply@fedoraproject.org',
            old_package_name='geany',
            old_distro_name='CentOS',
        )
        self.session.commit()

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, 'geany')
        self.assertEqual(len(project_obj.packages), 2)
        pkgs = sorted(project_obj.packages, key=lambda x: x.package_name)
        self.assertEqual(pkgs[0].package_name, 'geany2')
        self.assertEqual(pkgs[0].distro, 'CentOS')
        self.assertEqual(pkgs[1].package_name, 'geany3')
        self.assertEqual(pkgs[1].distro, 'Fedora')

        # Edit the mapping of the `geany` project to Fedora
        project_obj = models.Project.get(self.session, 2)
        self.assertEqual(project_obj.name, 'subsurface')
        self.assertEqual(len(project_obj.packages), 0)

        self.assertRaises(
            exceptions.AnityaInvalidMappingException,
            utilities.map_project,
            self.session,
            project=project_obj,
            package_name='geany2',
            distribution='CentOS',
            user_id='noreply@fedoraproject.org',
        )
