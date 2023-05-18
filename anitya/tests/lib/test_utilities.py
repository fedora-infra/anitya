# -*- coding: utf-8 -*-
#
# Copyright © 2014-2020  Red Hat, Inc.
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

import unittest

import anitya_schema
import arrow
import mock
from fedora_messaging import testing as fml_testing
from sqlalchemy.exc import SQLAlchemyError

from anitya.db import models
from anitya.lib import exceptions, plugins, utilities
from anitya.lib.exceptions import AnityaException, ProjectExists
from anitya.tests.base import (
    DatabaseTestCase,
    create_distro,
    create_flagged_project,
    create_project,
)


class CreateProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.create_project` function."""

    def test_create_project(self):
        """Test the create_project function of Distro."""
        create_distro(self.session)
        self.assertEqual(2, models.Distro.all(self.session, count=True))

        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="geany",
                homepage="https://www.geany.org/",
                version_url="https://www.geany.org/Download/Releases",
                regex="DEFAULT",
                user_id="noreply@fedoraproject.org",
            )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 1)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org/")

    def test_create_project_duplicate(self):
        """Assert that duplicate can't be created."""
        create_distro(self.session)
        self.assertEqual(2, models.Distro.all(self.session, count=True))

        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="geany",
                homepage="https://www.geany.org/",
                version_url="https://www.geany.org/Download/Releases",
                regex="DEFAULT",
                user_id="noreply@fedoraproject.org",
            )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 1)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org/")

        self.assertRaises(
            ProjectExists,
            utilities.create_project,
            self.session,
            name="geany",
            homepage="https://www.geany.org/",
            version_url="https://www.geany.org/Download/Releases",
            regex="DEFAULT",
            user_id="noreply@fedoraproject.org",
        )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 1)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org/")

    def test_create_project_general_error(self):
        """Assert general SQLAlchemy exceptions result in AnityaException."""
        with mock.patch.object(
            self.session, "flush", mock.Mock(side_effect=[SQLAlchemyError(), None])
        ):
            with fml_testing.mock_sends():
                self.assertRaises(
                    AnityaException,
                    utilities.create_project,
                    self.session,
                    name="geany",
                    homepage="https://www.geany.org/",
                    version_url="https://www.geany.org/Download/Releases",
                    regex="DEFAULT",
                    user_id="noreply@fedoraproject.org",
                )

    def test_create_project_dry_run(self):
        """Test the create_project dry_run parameter."""
        create_distro(self.session)
        self.assertEqual(2, models.Distro.all(self.session, count=True))

        with fml_testing.mock_sends():
            utilities.create_project(
                self.session,
                name="geany",
                homepage="https://www.geany.org/",
                version_url="https://www.geany.org/Download/Releases",
                regex="DEFAULT",
                user_id="noreply@fedoraproject.org",
                dry_run=True,
            )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 1)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org/")

        # This should be still a running transaction
        self.session.rollback()
        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 0)


class EditProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.edit_project` function."""

    def test_edit_project(self):
        """Test the edit_project function of Distro."""
        create_distro(self.session)
        create_project(self.session)

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org/")
        self.assertEqual(project_objs[1].name, "R2spec")
        self.assertEqual(project_objs[2].name, "subsurface")
        self.assertFalse(project_objs[0].releases_only)

        with fml_testing.mock_sends(anitya_schema.ProjectEdited):
            utilities.edit_project(
                self.session,
                project=project_objs[0],
                name=project_objs[0].name,
                homepage="https://www.geany.org",
                backend="PyPI",
                version_scheme="RPM",
                version_pattern=None,
                version_url=None,
                version_prefix=None,
                pre_release_filter="a;v",
                version_filter="alpha",
                regex=None,
                insecure=False,
                user_id="noreply@fedoraproject.org",
                releases_only=True,
                archived=True,
            )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org")
        self.assertEqual(project_objs[0].backend, "PyPI")
        self.assertEqual(project_objs[0].pre_release_filter, "a;v")
        self.assertTrue(project_objs[0].version_filter, "alpha")
        self.assertTrue(project_objs[0].releases_only)
        self.assertTrue(project_objs[0].archived)

    def test_edit_project_creating_duplicate(self):
        """
        Assert that attempting to edit a project and creating a duplicate fails
        """
        create_distro(self.session)
        create_project(self.session)

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org/")
        self.assertEqual(project_objs[1].name, "R2spec")
        self.assertEqual(project_objs[2].name, "subsurface")

        with fml_testing.mock_sends(anitya_schema.ProjectEdited):
            self.assertRaises(
                AnityaException,
                utilities.edit_project,
                self.session,
                project=project_objs[2],
                name="geany",
                homepage="https://www.geany.org/",
                backend=project_objs[2].backend,
                version_scheme=project_objs[2].version_scheme,
                version_pattern=None,
                version_url=project_objs[2].version_url,
                version_prefix=None,
                pre_release_filter=None,
                version_filter=None,
                regex=project_objs[2].regex,
                insecure=False,
                user_id="noreply@fedoraproject.org",
                releases_only=False,
            )

    def test_edit_project_insecure(self):
        """
        Assert change of project insecure flag
        """
        create_project(self.session)

        project_objs = models.Project.all(self.session)
        self.assertFalse(project_objs[0].insecure)

        with fml_testing.mock_sends(anitya_schema.ProjectEdited):
            utilities.edit_project(
                self.session,
                project=project_objs[0],
                name="geany",
                homepage="https://www.geany.org/",
                backend=project_objs[0].backend,
                version_scheme="RPM",
                version_pattern=None,
                version_url=project_objs[0].version_url,
                version_prefix=None,
                pre_release_filter=None,
                version_filter=None,
                regex=project_objs[0].regex,
                insecure=True,
                user_id="noreply@fedoraproject.org",
                releases_only=False,
            )

        project_objs = models.Project.all(self.session)
        self.assertTrue(project_objs[0].insecure)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_edit_project_check_release(self, mock_check):
        """
        Assert that check_release is working as it should
        """
        create_project(self.session)

        project_objs = models.Project.all(self.session)

        utilities.edit_project(
            self.session,
            project=project_objs[0],
            name="geany",
            homepage="https://www.geany.org/",
            backend=project_objs[0].backend,
            version_scheme="RPM",
            version_pattern=None,
            version_url=project_objs[0].version_url,
            version_prefix=None,
            pre_release_filter=None,
            version_filter=None,
            regex=project_objs[0].regex,
            insecure=False,
            user_id="noreply@fedoraproject.org",
            releases_only=False,
            check_release=True,
        )

        project_objs = models.Project.all(self.session)

        mock_check.assert_called_with(project_objs[0], mock.ANY)

    def test_edit_dry_run(self):
        """Test the edit_project function dry_run parameter."""
        create_distro(self.session)
        create_project(self.session)

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org/")
        self.assertEqual(project_objs[1].name, "R2spec")
        self.assertEqual(project_objs[2].name, "subsurface")
        self.assertFalse(project_objs[0].releases_only)

        with fml_testing.mock_sends():
            utilities.edit_project(
                self.session,
                project=project_objs[0],
                name=project_objs[0].name,
                homepage="https://www.geany.org",
                backend="PyPI",
                version_scheme="RPM",
                version_pattern=None,
                version_url=None,
                version_prefix=None,
                pre_release_filter="a;v",
                version_filter="foo",
                regex=None,
                insecure=False,
                user_id="noreply@fedoraproject.org",
                releases_only=True,
                archived=True,
                dry_run=True,
            )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org")
        self.assertEqual(project_objs[0].backend, "PyPI")
        self.assertEqual(project_objs[0].pre_release_filter, "a;v")
        self.assertEqual(project_objs[0].version_filter, "foo")
        self.assertTrue(project_objs[0].releases_only)
        self.assertTrue(project_objs[0].archived)

        # This should be still a running transaction
        self.session.rollback()
        self.assertEqual(project_objs[0].backend, "custom")
        self.assertEqual(project_objs[0].pre_release_filter, None)
        self.assertEqual(project_objs[0].version_filter, None)
        self.assertFalse(project_objs[0].releases_only)
        self.assertFalse(project_objs[0].archived)


class CheckProjectReleaseTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.check_project_release` function."""

    @mock.patch("anitya.db.models.Project")
    def test_check_project_release_no_backend(self, mock_project):
        """Test the check_project_release function for Project."""
        m_project = mock_project.return_value
        m_project.backend.return_value = "dummy"
        self.assertRaises(
            AnityaException, utilities.check_project_release, m_project, self.session
        )

    def test_check_project_release_archived(self):
        """Test the check_project_release function for archived Project."""
        project = models.Project(
            name="foobar", homepage="https://foo.bar", backend="npmjs", archived=True
        )
        self.session.add(project)
        self.session.commit()

        self.assertRaises(
            AnityaException, utilities.check_project_release, project, self.session
        )

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0", "0.9.9", "0.9.8"],
    )
    def test_check_project_release_backend(self, mock_method):
        """Test the check_project_release function for Project."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        versions = utilities.check_project_release(project, self.session, test=True)
        self.assertEqual(versions, ["1.0.0", "0.9.9", "0.9.8"])

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        mock.Mock(side_effect=exceptions.AnityaPluginException("")),
    )
    def test_check_project_release_plugin_exception(self):
        """Test the check_project_release function for Project."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        self.assertRaises(
            exceptions.AnityaPluginException,
            utilities.check_project_release,
            project,
            self.session,
        )
        self.assertEqual(project.error_counter, 1)

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions", return_value=["1.0.0"]
    )
    def test_check_project_release_no_new_version(self, mock_method):
        """Test the check_project_release function for Project."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        project.latest_version = "1.0.0"
        version = models.ProjectVersion(version="1.0.0", project_id=project.id)
        self.session.add(version)
        self.session.commit()

        utilities.check_project_release(project, self.session)

        self.assertEqual(project.latest_version, "1.0.0")
        self.assertEqual(project.logs, "No new version found")

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0", "0.9.9", "0.9.8"],
    )
    def test_check_project_release_new_version(self, mock_method):
        """Test the check_project_release function for Project."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                version_scheme="RPM",
            )
        with fml_testing.mock_sends(
            anitya_schema.ProjectVersionUpdated, anitya_schema.ProjectVersionUpdatedV2
        ):
            utilities.check_project_release(project, self.session)
        versions = project.get_sorted_version_objects()
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].version, "1.0.0")

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["v1.0.0", "v0.9.9", "v0.9.8"],
    )
    def test_check_project_release_prefix_remove(self, mock_method):
        """Test the check_project_release function for Project."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                version_scheme="RPM",
            )
        with fml_testing.mock_sends(
            anitya_schema.ProjectVersionUpdated, anitya_schema.ProjectVersionUpdatedV2
        ):
            utilities.check_project_release(project, self.session)

        versions = project.get_sorted_version_objects()
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].version, "v1.0.0")
        self.assertEqual(project.latest_version, "1.0.0")

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["v1.0.0", "v0.9.9", ""],
    )
    def test_check_project_release_empty_version(self, mock_method):
        """Test the check_project_release function with empty version."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                version_scheme="RPM",
            )
        with fml_testing.mock_sends(
            anitya_schema.ProjectVersionUpdated, anitya_schema.ProjectVersionUpdatedV2
        ):
            utilities.check_project_release(project, self.session)

        versions = project.get_sorted_version_objects()
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version, "v1.0.0")
        self.assertEqual(project.latest_version, "1.0.0")

    @mock.patch(
        "anitya.lib.backends.github.GithubBackend.get_versions",
        return_value=[
            {"version": "1.0.0", "commit_url": "https://example.com/tags/1.0.0"},
            {"version": "0.9.9", "commit_url": "https://example.com/tags/0.9.9"},
            {"version": "0.9.8", "commit_url": "https://example.com/tags/0.9.8"},
        ],
    )
    def test_check_project_release_with_versions_with_urls(self, mock_method):
        """Test check_project_release() with versions with URLs."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="project_name",
                homepage="https://not-a-real-homepage.com",
                backend="GitHub",
                user_id="noreply@fedoraproject.org",
            )
        with fml_testing.mock_sends(
            anitya_schema.ProjectVersionUpdated, anitya_schema.ProjectVersionUpdatedV2
        ):
            utilities.check_project_release(project, self.session)

        for vo in project.versions_obj:
            self.assertEqual(vo.commit_url, "https://example.com/tags/" + vo.version)

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0", "0.9.9", "0.9.8"],
    )
    def test_check_project_check_times(self, mock_method):
        """Test if check times are set."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        last_check_orig = project.last_check

        with fml_testing.mock_sends(
            anitya_schema.ProjectVersionUpdated, anitya_schema.ProjectVersionUpdatedV2
        ):
            utilities.check_project_release(project, self.session)
        next_check = (
            plugins.get_plugin(project.backend).check_interval + project.last_check
        )
        self.assertTrue(last_check_orig < project.last_check)
        self.assertEqual(next_check, project.next_check)

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0", "0.9.9", "0.9.8"],
    )
    def test_check_project_check_times_test(self, mock_method):
        """Test if check times aren't set in test mode."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        last_check_orig = project.last_check
        next_check_orig = project.next_check

        with fml_testing.mock_sends():
            versions = utilities.check_project_release(project, self.session, test=True)
        self.assertEqual(last_check_orig, project.last_check)
        self.assertEqual(next_check_orig, project.next_check)
        self.assertEqual(versions, ["1.0.0", "0.9.9", "0.9.8"])

    def test_check_project_check_times_exception(self):
        """Test if check times are set if `exceptions.RateLimitException` is raised."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        last_check_orig = project.last_check
        next_check = arrow.get("2008-09-03T20:56:35.450686").naive

        with mock.patch(
            "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
            return_value=["1.0.0"],
        ) as mock_object:
            mock_object.side_effect = exceptions.RateLimitException(
                "2008-09-03T20:56:35.450686"
            )
            with fml_testing.mock_sends():
                self.assertRaises(
                    exceptions.RateLimitException,
                    utilities.check_project_release,
                    project,
                    self.session,
                )
            self.assertTrue(last_check_orig < project.last_check)
            self.assertEqual(next_check, project.next_check)

    @mock.patch.dict("anitya.config.config", {"GITHUB_ACCESS_TOKEN": "foobar"})
    def test_check_project_version_too_long(self):
        """
        Regression test for https://github.com/fedora-infra/anitya/issues/674
        Crash when version is too long
        """
        project = models.Project(
            name="daiquiri",
            homepage="https://github.com/jd/daiquiri",
            backend="GitHub",
            version_scheme="RPM",
            version_url="jd/daiquiri",
        )
        self.session.add(project)
        self.session.commit()

        with fml_testing.mock_sends(
            anitya_schema.ProjectVersionUpdated, anitya_schema.ProjectVersionUpdatedV2
        ):
            utilities.check_project_release(project, self.session)

        versions = project.versions
        self.assertEqual(len(versions), 18)
        self.assertFalse(
            "remove-circular-dependency-ad4f7bc7-2ab4-43b8-afac-36ff0e2ee796"
            in versions
        )
        self.assertFalse(
            "remove-circular-dependency-7bbe4a64-3514-4f6e-9c03-9dc8bcf4def7"
            in versions
        )

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions", return_value=["1.0.0"]
    )
    def test_check_project_release_error_counter_reset(self, mock_method):
        """Test if error_counter reset to 0, when successful check is done."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        project.error_counter = 30
        self.session.add(project)
        self.session.commit()

        utilities.check_project_release(project, self.session)

        self.assertEqual(project.error_counter, 0)

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["0.9.9"],
    )
    def test_check_project_release_old_version(self, mock_method):
        """
        Test the check_project_release function for Project.
        This test will test if the fedora message is sent even if
        the version is not the newest.
        """
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                version_scheme="RPM",
            )
        # Create version
        version = models.ProjectVersion(project_id=project.id, version="1.0.0")
        self.session.add(version)
        self.session.commit()

        with fml_testing.mock_sends(
            anitya_schema.ProjectVersionUpdated, anitya_schema.ProjectVersionUpdatedV2
        ):
            utilities.check_project_release(project, self.session)
        versions = project.get_sorted_version_objects()
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version, "1.0.0")
        self.assertEqual(versions[1].version, "0.9.9")


class MapProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.map_project` function."""

    def test_map_project(self):
        """Test the map_project function of Distro."""
        create_distro(self.session)
        create_project(self.session)

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 0)

        # Map `geany` project to CentOS
        with fml_testing.mock_sends(
            anitya_schema.DistroCreated, anitya_schema.ProjectMapCreated
        ):
            utilities.map_project(
                self.session,
                project=project_obj,
                package_name="geany",
                distribution="CentOS",
                user_id="noreply@fedoraproject.org",
                old_package_name=None,
            )
        self.session.commit()

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 1)
        self.assertEqual(project_obj.packages[0].package_name, "geany")
        self.assertEqual(project_obj.packages[0].distro_name, "CentOS")

        # Map `geany` project to CentOS, exactly the same way
        with fml_testing.mock_sends(anitya_schema.ProjectMapCreated):
            utilities.map_project(
                self.session,
                project=project_obj,
                package_name="geany2",
                distribution="CentOS",
                user_id="noreply@fedoraproject.org",
                old_package_name=None,
            )
        self.session.commit()

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 2)
        self.assertEqual(project_obj.packages[0].package_name, "geany")
        self.assertEqual(project_obj.packages[0].distro_name, "CentOS")
        self.assertEqual(project_obj.packages[1].package_name, "geany2")
        self.assertEqual(project_obj.packages[1].distro_name, "CentOS")

        # Edit the mapping of the `geany` project to Fedora
        with fml_testing.mock_sends(anitya_schema.ProjectMapEdited):
            utilities.map_project(
                self.session,
                project=project_obj,
                package_name="geany3",
                distribution="Fedora",
                user_id="noreply@fedoraproject.org",
                old_package_name="geany",
                old_distro_name="CentOS",
            )
        self.session.commit()

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 2)
        pkgs = sorted(project_obj.packages, key=lambda x: x.package_name)
        self.assertEqual(pkgs[0].package_name, "geany2")
        self.assertEqual(pkgs[0].distro_name, "CentOS")
        self.assertEqual(pkgs[1].package_name, "geany3")
        self.assertEqual(pkgs[1].distro_name, "Fedora")

        # Edit the mapping of the `geany` project to Fedora
        project_obj = models.Project.get(self.session, 2)
        self.assertEqual(project_obj.name, "subsurface")
        self.assertEqual(len(project_obj.packages), 0)

        with fml_testing.mock_sends():
            self.assertRaises(
                exceptions.AnityaInvalidMappingException,
                utilities.map_project,
                self.session,
                project=project_obj,
                package_name="geany2",
                distribution="CentOS",
                user_id="noreply@fedoraproject.org",
            )

    def test_map_project_no_project_for_package(self):
        """Test package duplicity when package is not associated to project"""
        create_distro(self.session)
        create_project(self.session)

        pkg = models.Packages(
            distro_name="Fedora", project_id=None, package_name="geany"
        )
        self.session.add(pkg)
        self.session.commit()

        distro_objs = self.session.query(models.Distro).all()
        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 0)
        self.assertEqual(distro_objs[0].name, "Fedora")

        with fml_testing.mock_sends(anitya_schema.ProjectMapCreated):
            utilities.map_project(
                self.session,
                project=project_obj,
                package_name="geany",
                distribution="Fedora",
                user_id="noreply@fedoraproject.org",
                old_package_name=None,
            )
        self.session.commit()

        project_obj = models.Project.get(self.session, 1)
        packages = self.session.query(models.Packages).all()
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 1)
        self.assertEqual(len(packages), 1)
        self.assertEqual(project_obj.packages[0].package_name, "geany")
        self.assertEqual(project_obj.packages[0].distro_name, "Fedora")

    def test_map_project_session_error_no_distro(self):
        """Test SQLAlchemy session error"""
        create_project(self.session)

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 0)

        with mock.patch.object(
            self.session, "flush", mock.Mock(side_effect=[SQLAlchemyError(), None])
        ):
            # Without existing Distro object
            with fml_testing.mock_sends():
                self.assertRaises(
                    exceptions.AnityaException,
                    utilities.map_project,
                    self.session,
                    project=project_obj,
                    package_name="geany",
                    distribution="Fedora",
                    user_id="noreply@fedoraproject.org",
                    old_package_name=None,
                )

    def test_map_project_session_error(self):
        """Test SQLAlchemy session error"""
        create_project(self.session)
        create_distro(self.session)

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(project_obj.name, "geany")
        self.assertEqual(len(project_obj.packages), 0)

        with mock.patch.object(
            self.session, "flush", mock.Mock(side_effect=[SQLAlchemyError(), None])
        ):
            # With Distro object
            with fml_testing.mock_sends():
                self.assertRaises(
                    exceptions.AnityaException,
                    utilities.map_project,
                    self.session,
                    project=project_obj,
                    package_name="geany",
                    distribution="Fedora",
                    user_id="noreply@fedoraproject.org",
                    old_package_name=None,
                )


class FlagProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.flag_project` function."""

    def test_flag_project(self):
        """Test flag creation"""
        create_project(self.session)

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(len(project_obj.flags), 0)

        with fml_testing.mock_sends(anitya_schema.ProjectFlag):
            utilities.flag_project(
                self.session,
                project=project_obj,
                reason="reason",
                user_email="noreply@fedoraproject.org",
                user_id="noreply@fedoraproject.org",
            )

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(len(project_obj.flags), 1)
        self.assertEqual(project_obj.flags[0].reason, "reason")

    def test_flag_project_session_error(self):
        """Test SQLAlchemy session error"""
        create_project(self.session)

        project_obj = models.Project.get(self.session, 1)

        with mock.patch.object(
            self.session, "flush", mock.Mock(side_effect=[SQLAlchemyError(), None])
        ):
            with fml_testing.mock_sends():
                self.assertRaises(
                    exceptions.AnityaException,
                    utilities.flag_project,
                    self.session,
                    project=project_obj,
                    reason="reason",
                    user_email="noreply@fedoraproject.org",
                    user_id="noreply@fedoraproject.org",
                )


class SetFlagStateTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.set_flag_state` function."""

    def test_set_flag_state(self):
        """Test set state"""
        flag = create_flagged_project(self.session)

        with fml_testing.mock_sends(anitya_schema.ProjectFlagSet):
            utilities.set_flag_state(
                self.session,
                flag=flag,
                state="closed",
                user_id="noreply@fedoraproject.org",
            )

        project_obj = models.Project.get(self.session, 1)
        self.assertEqual(len(project_obj.flags), 1)
        self.assertEqual(project_obj.flags[0].state, "closed")

    def test_set_flag_state_no_change(self):
        """Test set state"""
        flag = create_flagged_project(self.session)

        with fml_testing.mock_sends():
            self.assertRaises(
                exceptions.AnityaException,
                utilities.set_flag_state,
                self.session,
                flag=flag,
                state="open",
                user_id="noreply@fedoraproject.org",
            )

    def test_set_flag_project_session_error(self):
        """Test SQLAlchemy session error"""
        flag = create_flagged_project(self.session)

        with mock.patch.object(
            self.session, "flush", mock.Mock(side_effect=[SQLAlchemyError(), None])
        ):
            with fml_testing.mock_sends():
                self.assertRaises(
                    exceptions.AnityaException,
                    utilities.set_flag_state,
                    self.session,
                    flag=flag,
                    state="closed",
                    user_id="noreply@fedoraproject.org",
                )


class RemoveSuffixTests(unittest.TestCase):
    """Tests for the :func:`anitya.lib.utilities.remove_suffix` function."""

    def test_remove_suffix_no_change(self):
        url = "https://github.com/baresip/re"
        self.assertEqual(
            utilities.remove_suffix(url, "/releases"), "https://github.com/baresip/re"
        )
        self.assertEqual(
            utilities.remove_suffix(url, "/tags"), "https://github.com/baresip/re"
        )

        url = "https://github.com/libexpat/libexpat"
        self.assertEqual(
            utilities.remove_suffix(url, "/releases"),
            "https://github.com/libexpat/libexpat",
        )
        self.assertEqual(
            utilities.remove_suffix(url, "/tags"),
            "https://github.com/libexpat/libexpat",
        )

    def test_remove_suffix_remove_releases(self):
        url = "https://github.com/baresip/re/releases"
        self.assertEqual(
            utilities.remove_suffix(url, "/releases"), "https://github.com/baresip/re"
        )
        self.assertEqual(
            utilities.remove_suffix(url, "/tags"),
            "https://github.com/baresip/re/releases",
        )

        url = "https://github.com/libexpat/libexpat/releases"
        self.assertEqual(
            utilities.remove_suffix(url, "/releases"),
            "https://github.com/libexpat/libexpat",
        )
        self.assertEqual(
            utilities.remove_suffix(url, "/tags"),
            "https://github.com/libexpat/libexpat/releases",
        )

    def test_remove_suffix_remove_tags(self):
        url = "https://github.com/baresip/re/tags"
        self.assertEqual(
            utilities.remove_suffix(url, "/releases"),
            "https://github.com/baresip/re/tags",
        )
        self.assertEqual(
            utilities.remove_suffix(url, "/tags"), "https://github.com/baresip/re"
        )

        url = "https://github.com/libexpat/libexpat/tags"
        self.assertEqual(
            utilities.remove_suffix(url, "/releases"),
            "https://github.com/libexpat/libexpat/tags",
        )
        self.assertEqual(
            utilities.remove_suffix(url, "/tags"),
            "https://github.com/libexpat/libexpat",
        )
