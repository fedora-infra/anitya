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

import mock

import arrow
from sqlalchemy.exc import SQLAlchemyError
from fedora_messaging import testing as fml_testing

import anitya_schema
from anitya.db import models
from anitya.lib import utilities, exceptions, plugins
from anitya.lib.exceptions import AnityaException, ProjectExists
from anitya.tests.base import (
    DatabaseTestCase,
    create_distro,
    create_project,
    create_flagged_project,
)


class CreateProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.create_project` function."""

    def test_create_project(self):
        """ Test the create_project function of Distro. """
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


class EditProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.edit_project` function."""

    def test_edit_project(self):
        """ Test the edit_project function of Distro. """
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
                regex=None,
                insecure=False,
                user_id="noreply@fedoraproject.org",
                releases_only=True,
            )

        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 3)
        self.assertEqual(project_objs[0].name, "geany")
        self.assertEqual(project_objs[0].homepage, "https://www.geany.org")
        self.assertEqual(project_objs[0].backend, "PyPI")
        self.assertTrue(project_objs[0].releases_only)

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
                regex=project_objs[0].regex,
                insecure=True,
                user_id="noreply@fedoraproject.org",
                releases_only=False,
            )

        project_objs = models.Project.all(self.session)
        self.assertTrue(project_objs[0].insecure)


class CheckProjectReleaseTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.check_project_release` function."""

    @mock.patch("anitya.db.models.Project")
    def test_check_project_release_no_backend(self, mock_project):
        """ Test the check_project_release function for Project. """
        m_project = mock_project.return_value
        m_project.backend.return_value = "dummy"
        self.assertRaises(
            AnityaException, utilities.check_project_release, m_project, self.session
        )

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0", "0.9.9", "0.9.8"],
    )
    def test_check_project_release_backend(self, mock_method):
        """ Test the check_project_release function for Project. """
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        versions = utilities.check_project_release(project, self.session, test=True)
        self.assertEqual(versions, ["0.9.8", "0.9.9", "1.0.0"])

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        mock.Mock(side_effect=exceptions.AnityaPluginException("")),
    )
    def test_check_project_release_plugin_exception(self):
        """ Test the check_project_release function for Project. """
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
        """ Test the check_project_release function for Project. """
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
        """ Test the check_project_release function for Project. """
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                version_scheme="RPM",
            )
        with fml_testing.mock_sends(anitya_schema.ProjectVersionUpdated):
            utilities.check_project_release(project, self.session)
        versions = project.get_sorted_version_objects()
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].version, "1.0.0")

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["v1.0.0", "v0.9.9", "v0.9.8"],
    )
    def test_check_project_release_prefix_remove(self, mock_method):
        """ Test the check_project_release function for Project. """
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                version_scheme="RPM",
            )
        with fml_testing.mock_sends(anitya_schema.ProjectVersionUpdated):
            utilities.check_project_release(project, self.session)

        versions = project.get_sorted_version_objects()
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].version, "v1.0.0")
        self.assertEqual(project.latest_version, "1.0.0")

    @mock.patch(
        "anitya.lib.backends.github.GithubBackend.get_versions",
        return_value=[
            {"version": "1.0.0", "cursor": "Hbgf"},
            {"version": "0.9.9", "cursor": "Hbge"},
            {"version": "0.9.8", "cursor": "Hbgd"},
        ],
    )
    def test_check_project_release_versions_with_cursor(self, mock_method):
        """Test check_project_release() with versions with cursor."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="project_name",
                homepage="https://not-a-real-homepage.com",
                backend="GitHub",
                user_id="noreply@fedoraproject.org",
            )
        with fml_testing.mock_sends(anitya_schema.ProjectVersionUpdated):
            utilities.check_project_release(project, self.session)

        self.assertEqual(project.latest_version_cursor, "Hbgf")

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0", "0.9.9", "0.9.8"],
    )
    def test_check_project_check_times(self, mock_method):
        """ Test if check times are set. """
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="pypi_and_npm",
                homepage="https://example.com/not-a-real-npmjs-project",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        last_check_orig = project.last_check

        with fml_testing.mock_sends(anitya_schema.ProjectVersionUpdated):
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
        """ Test if check times aren't set in test mode. """
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
            utilities.check_project_release(project, self.session, test=True)
        self.assertEqual(last_check_orig, project.last_check)
        self.assertEqual(next_check_orig, project.next_check)

    def test_check_project_check_times_exception(self):
        """ Test if check times are set if `exceptions.RateLimitException` is raised. """
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
        Regression test for https://github.com/release-monitoring/anitya/issues/674
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

        with fml_testing.mock_sends(anitya_schema.ProjectVersionUpdated):
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
        """ Test if error_counter reset to 0, when successful check is done. """
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


class MapProjectTests(DatabaseTestCase):
    """Tests for the :func:`anitya.lib.utilities.map_project` function."""

    def test_map_project(self):
        """ Test the map_project function of Distro. """
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
        """ Test package duplicity when package is not associated to project """
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
        """ Test SQLAlchemy session error """
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
        """ Test SQLAlchemy session error """
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
        """ Test flag creation """
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
        """ Test SQLAlchemy session error """
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
        """ Test set state """
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
        """ Test set state """
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
        """ Test SQLAlchemy session error """
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


class LogTests(DatabaseTestCase):
    """ Tests for `anitya.lib.utilities.log` function. """

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_distro_add(self, mock_method):
        """ Assert that 'distro.add' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya added the distro named: Fedora"
        message = {"agent": "anitya", "distro": "Fedora"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="distro.add",
            message=message,
        )

        mock_method.assert_called_with(
            topic="distro.add",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_distro_edit(self, mock_method):
        """ Assert that 'distro.edit' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya edited distro name from: Dummy to: Fedora"
        message = {"agent": "anitya", "old": "Dummy", "new": "Fedora"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="distro.edit",
            message=message,
        )

        mock_method.assert_called_with(
            topic="distro.edit",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_distro_remove(self, mock_method):
        """ Assert that 'distro.remove' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya deleted the distro named: Fedora"
        message = {"agent": "anitya", "distro": "Fedora"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="distro.remove",
            message=message,
        )

        mock_method.assert_called_with(
            topic="distro.remove",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_add(self, mock_method):
        """ Assert that 'project.add' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya added project: test"
        message = {"agent": "anitya", "project": "test"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.add",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.add",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_add_tried(self, mock_method):
        """ Assert that 'project.add.tried' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya tried to add an already existing project: test"
        message = {"agent": "anitya", "project": "test"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.add.tried",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.add.tried",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_edit(self, mock_method):
        """ Assert that 'project.edit' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        message = {
            "agent": "anitya",
            "project": "test",
            "changes": {"name": {"old": "dummy", "new": "test"}},
        }
        exp = "anitya edited the project: test fields: " "{}".format(message["changes"])
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.edit",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.edit",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_flag(self, mock_method):
        """ Assert that 'project.flag' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya flagged the project: test with reason: reason"
        message = {"agent": "anitya", "project": "test", "reason": "reason"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.flag",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.flag",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_flag_set(self, mock_method):
        """ Assert that 'project.flag.set' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya set flag test to open"
        message = {"agent": "anitya", "flag": "test", "state": "open"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.flag.set",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.flag.set",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_remove(self, mock_method):
        """ Assert that 'project.remove' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya removed the project: test"
        message = {"agent": "anitya", "project": "test"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.remove",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.remove",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_map_new(self, mock_method):
        """ Assert that 'project.map.new' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya mapped the name of test in Fedora as test_package"
        message = {
            "agent": "anitya",
            "project": "test",
            "distro": "Fedora",
            "new": "test_package",
        }
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.map.new",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.map.new",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_map_update(self, mock_method):
        """ Assert that 'project.map.update' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya updated the name of test in Fedora from: test_old" " to: test_new"
        message = {
            "agent": "anitya",
            "project": "test",
            "distro": "Fedora",
            "prev": "test_old",
            "new": "test_new",
        }
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.map.update",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.map.update",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_map_remove(self, mock_method):
        """ Assert that 'project.map.remove' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya removed the mapping of test in Fedora"
        message = {"agent": "anitya", "project": "test", "distro": "Fedora"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.map.remove",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.map.remove",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_version_remove(self, mock_method):
        """ Assert that 'project.version.remove' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = "anitya removed the version 1.0.0 of test"
        message = {"agent": "anitya", "project": "test", "version": "1.0.0"}
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.version.remove",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.version.remove",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)

    @mock.patch("anitya.lib.utilities.fedmsg_publish")
    def test_log_project_version_update(self, mock_method):
        """ Assert that 'project.version.update' topic is handled correctly. """
        project = models.Project(name="test")
        distro = models.Distro(name="Fedora")
        exp = (
            "new version: 1.0.0 found for project test "
            "in ecosystem pypi (project id: 1)."
        )
        message = {
            "agent": "anitya",
            "upstream_version": "1.0.0",
            "ecosystem": "pypi",
            "project": {"name": "test", "id": "1"},
        }
        final_msg = utilities.log(
            self.session,
            project=project,
            distro=distro,
            topic="project.version.update",
            message=message,
        )

        mock_method.assert_called_with(
            topic="project.version.update",
            msg=dict(project=project, distro=distro, message=message),
        )
        self.assertEqual(final_msg, exp)
