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
from anitya.lib.backends import BaseBackend
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

    def test_create_project_duplicate_github_version_url(self):
        """Assert duplicate GitHub repository by version_url is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="fedocal",
                homepage="https://fedora-infra.github.io/fedocal",
                backend="GitHub",
                version_url="fedora-infra/fedocal",
                user_id="user@example.com",
            )

        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="fedora-calendar",
                homepage="https://github.com/fedora-infra/fedocal",
                backend="GitHub",
                version_url="fedora-infra/fedocal",
                user_id="user@example.com",
            )

    def test_create_project_duplicate_github_homepage(self):
        """Assert duplicate GitHub repository via homepage is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="pkgdb2",
                homepage="https://admin.fedoraproject.org/pkgdb",
                backend="GitHub",
                version_url="fedora-infra/pkgdb2",
                user_id="user@example.com",
            )

        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="fedora-pkgdb",
                homepage="https://github.com/fedora-infra/pkgdb2.git/",
                backend="GitHub",
                user_id="user@example.com",
            )

    def test_create_project_duplicate_gitlab_subgroup(self):
        """Assert duplicate GitLab repository with subgroup is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="glib",
                homepage="https://developer.gnome.org/glib",
                backend="GitLab",
                version_url="https://gitlab.gnome.org/GNOME/glib",
                user_id="user@example.com",
            )

        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="gnome-glib",
                homepage="https://gitlab.gnome.org/GNOME/glib/-/tags",
                backend="GitLab",
                user_id="user@example.com",
            )

    def test_create_project_gitlab_different_instances_allowed(self):
        """Assert same subgroup and repo on different GitLab instances are allowed."""
        with fml_testing.mock_sends(
            anitya_schema.ProjectCreated, anitya_schema.ProjectCreated
        ):
            utilities.create_project(
                self.session,
                name="glib-gnome",
                homepage="https://developer.gnome.org/glib",
                backend="GitLab",
                version_url="https://gitlab.gnome.org/GNOME/glib",
                user_id="user@example.com",
            )
            utilities.create_project(
                self.session,
                name="glib-gitlab-com",
                homepage="https://gitlab.com/GNOME/glib",
                backend="GitLab",
                version_url="https://gitlab.com/GNOME/glib",
                user_id="user@example.com",
            )
        self.assertEqual(len(models.Project.all(self.session)), 2)

    def test_create_project_packagist_vendor_and_duplicates(self):
        """
        Assert Packagist allows different packages from same vendor but rejects duplicate.
        """
        with fml_testing.mock_sends(
            anitya_schema.ProjectCreated, anitya_schema.ProjectCreated
        ):
            utilities.create_project(
                self.session,
                name="console",
                homepage="https://symfony.com",
                backend="Packagist",
                version_url="symfony",
                user_id="user@example.com",
            )
            utilities.create_project(
                self.session,
                name="http-kernel",
                homepage="https://symfony.com",
                backend="Packagist",
                version_url="symfony",
                user_id="user@example.com",
            )
        self.assertEqual(len(models.Project.all(self.session)), 2)

        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="Console",
                homepage="https://symfony.com/console",
                backend="Packagist",
                version_url="symfony",
                user_id="user@example.com",
            )

    def test_create_project_repo_named_releases(self):
        """Assert repositories named 'releases' or 'tags' do not collide with others from owner."""
        with fml_testing.mock_sends(
            anitya_schema.ProjectCreated, anitya_schema.ProjectCreated
        ):
            utilities.create_project(
                self.session,
                name="cockpit-releases",
                homepage="https://cockpit-project.org",
                backend="GitHub",
                version_url="cockpit-project/releases",
                user_id="user@example.com",
            )
            utilities.create_project(
                self.session,
                name="cockpit-bots",
                homepage="https://cockpit-project.org",
                backend="GitHub",
                version_url="cockpit-project/bots",
                user_id="user@example.com",
            )
        self.assertEqual(len(models.Project.all(self.session)), 2)

    def test_create_project_duplicate_custom_trailing_slash(self):
        """Assert duplicate custom backend with trailing slash is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="geany",
                homepage="https://www.geany.org",
                backend="custom",
                version_url="https://download.geany.org/releases",
                user_id="user@example.com",
            )

        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="geany-editor",
                homepage="https://geany.org",
                backend="custom",
                version_url="https://download.geany.org/releases/",
                user_id="user@example.com",
            )

    def test_create_project_duplicate_pypi(self):
        """Assert duplicate PyPI project with case variance and different homepage is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="urllib3",
                homepage="https://urllib3.readthedocs.io/",
                backend="PyPI",
                user_id="user@example.com",
            )

        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="Urllib3",
                homepage="https://pypi.org/project/urllib3/",
                backend="PyPI",
                user_id="user@example.com",
            )

    def test_create_project_different_backend_not_duplicate(self):
        """Assert same package name or repo on different backends is allowed."""
        with fml_testing.mock_sends(
            anitya_schema.ProjectCreated, anitya_schema.ProjectCreated
        ):
            utilities.create_project(
                self.session,
                name="requests",
                homepage="https://requests.readthedocs.io",
                backend="GitHub",
                version_url="psf/requests",
                user_id="user@example.com",
            )
            utilities.create_project(
                self.session,
                name="requests",
                homepage="https://pypi.org/project/requests",
                backend="PyPI",
                user_id="user@example.com",
            )
        self.assertEqual(len(models.Project.all(self.session)), 2)

    def test_find_duplicate_project_no_backend(self):
        """Assert find_duplicate_project returns None if project has no backend."""
        project = mock.MagicMock(backend=None)
        self.assertIsNone(utilities.find_duplicate_project(self.session, project))

    def test_find_duplicate_project_unknown_backend(self):
        """Assert find_duplicate_project returns None if backend plugin is not found."""
        project = mock.MagicMock(backend="nonexistent")
        self.assertIsNone(utilities.find_duplicate_project(self.session, project))

    def test_create_project_duplicate_cgit(self):
        """Assert duplicate Cgit repository is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="cgit-repo",
                homepage="https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git",
                backend="Cgit",
                version_url="https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git",
                user_id="user@example.com",
            )
        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="cgit-repo-dup",
                homepage="https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/",
                backend="Cgit",
                version_url="https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/",
                user_id="user@example.com",
            )

    def test_create_project_duplicate_sourceforge(self):
        """Assert duplicate SourceForge project is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="pidgin",
                homepage="https://pidgin.im",
                backend="Sourceforge",
                version_url="pidgin",
                user_id="user@example.com",
            )
        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="pidgin-dup",
                homepage="https://sourceforge.net/projects/pidgin/",
                backend="Sourceforge",
                version_url="pidgin",
                user_id="user@example.com",
            )

    def test_create_project_duplicate_maven_central(self):
        """Assert duplicate Maven Central coordinate is rejected."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="commons-lang3",
                homepage="https://commons.apache.org/proper/commons-lang/",
                backend="Maven Central",
                version_url="org.apache.commons:commons-lang3",
                user_id="user@example.com",
            )
        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.create_project,
                self.session,
                name="apache-commons-lang3",
                homepage="https://repo1.maven.org/maven2/org/apache/commons/commons-lang3/",
                backend="Maven Central",
                version_url="org.apache.commons:commons-lang3",
                user_id="user@example.com",
            )

    def test_extract_repo_identifier_relative_version_url(self):
        """Assert relative version_url in multi-host backend inherits domain from homepage."""
        proj = models.Project(
            name="test",
            homepage="https://gitlab.example.org/group/project",
            version_url="group/project",
            backend="GitLab",
        )
        self.assertEqual(
            BaseBackend._extract_repo_identifier(proj, multi_host=True),
            "gitlab.example.org/group/project",
        )

    def test_extract_repo_identifier_empty(self):
        """Assert _extract_repo_identifier returns None when url is empty."""
        proj = models.Project(
            name="test",
            homepage="",
            version_url="",
            backend="GitHub",
        )
        self.assertIsNone(BaseBackend._extract_repo_identifier(proj))

    def test_check_duplicate_base_empty_name(self):
        """Assert BaseBackend.check_duplicate returns None when project name is empty."""
        proj = models.Project(name="", backend="PyPI")
        self.assertIsNone(BaseBackend.check_duplicate(self.session, proj))

    def test_check_repo_duplicate_empty_url(self):
        """Assert BaseBackend._check_repo_duplicate returns None when url is empty."""
        proj = models.Project(
            name="test", backend="GitHub", homepage="", version_url=""
        )
        self.assertIsNone(BaseBackend._check_repo_duplicate(self.session, proj))

    def test_cgit_check_duplicate_empty_and_self(self):
        """Test Cgit duplicate check edge cases."""
        cgit_backend = plugins.get_plugin("Cgit")
        proj = models.Project(name="test", backend="Cgit", version_url="", homepage="")
        self.assertIsNone(cgit_backend.check_duplicate(self.session, proj))

        proj_existing = models.Project(
            name="test-cgit",
            backend="Cgit",
            version_url="https://git.example.org/repo.git",
            homepage="https://example.org",
        )
        self.session.add(proj_existing)
        self.session.commit()
        self.assertIsNone(cgit_backend.check_duplicate(self.session, proj_existing))

    def test_folder_check_duplicate(self):
        """Test Folder duplicate check with empty version_url, matching duplicate, and self."""
        folder_backend = plugins.get_plugin("folder")
        proj = models.Project(name="test", backend="folder", version_url="")
        self.assertIsNone(folder_backend.check_duplicate(self.session, proj))

        proj_existing = models.Project(
            name="test-folder",
            backend="folder",
            version_url="https://ftp.gnu.org/pub/gnu/gnash/",
            homepage="https://ftp.gnu.org/pub/gnu/gnash/",
        )
        self.session.add(proj_existing)
        self.session.commit()

        proj_dup = models.Project(
            name="test-folder-dup",
            backend="folder",
            version_url="https://ftp.gnu.org/pub/gnu/gnash",
            homepage="https://example.org",
        )
        self.assertEqual(
            folder_backend.check_duplicate(self.session, proj_dup),
            proj_existing,
        )
        self.assertIsNone(folder_backend.check_duplicate(self.session, proj_existing))

    def test_maven_check_duplicate_empty_and_self(self):
        """Test Maven duplicate check edge cases."""
        maven_backend = plugins.get_plugin("Maven Central")
        proj = models.Project(name="", backend="Maven Central", version_url="")
        self.assertIsNone(maven_backend.check_duplicate(self.session, proj))

        proj_existing = models.Project(
            name="test-maven",
            backend="Maven Central",
            version_url="org.test:test",
            homepage="https://example.org",
        )
        self.session.add(proj_existing)
        self.session.commit()
        self.assertIsNone(maven_backend.check_duplicate(self.session, proj_existing))

    def test_packagist_check_duplicate_empty_and_self(self):
        """Test Packagist duplicate check edge cases."""
        packagist_backend = plugins.get_plugin("Packagist")
        proj = models.Project(name="", backend="Packagist", version_url="")
        self.assertIsNone(packagist_backend.check_duplicate(self.session, proj))
        proj_no_vurl = models.Project(name="foo", backend="Packagist", version_url="")
        self.assertIsNone(packagist_backend.check_duplicate(self.session, proj_no_vurl))

        proj_existing = models.Project(
            name="bar",
            backend="Packagist",
            version_url="vendor",
            homepage="https://example.org",
        )
        self.session.add(proj_existing)
        self.session.commit()
        self.assertIsNone(
            packagist_backend.check_duplicate(self.session, proj_existing)
        )

    def test_sourceforge_check_duplicate_empty_and_self(self):
        """Test SourceForge duplicate check edge cases."""
        sf_backend = plugins.get_plugin("Sourceforge")
        proj = models.Project(name="", backend="Sourceforge", version_url="")
        self.assertIsNone(sf_backend.check_duplicate(self.session, proj))

        proj_existing = models.Project(
            name="sf-test",
            backend="Sourceforge",
            version_url="sf-test",
            homepage="https://sourceforge.net/projects/sf-test",
        )
        self.session.add(proj_existing)
        self.session.commit()
        self.assertIsNone(sf_backend.check_duplicate(self.session, proj_existing))

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

    def test_edit_project_duplicate_rejected(self):
        """Assert editing project to match an existing project's target raises ProjectExists."""
        create_project(self.session)
        project_objs = models.Project.all(self.session)

        with fml_testing.mock_sends():
            self.assertRaises(
                ProjectExists,
                utilities.edit_project,
                self.session,
                project=project_objs[1],
                name="subsurface-renamed",
                homepage="https://subsurface-divelog.org/",
                backend="custom",
                version_scheme="RPM",
                version_pattern=None,
                version_url="https://www.geany.org/Download/Releases/",
                version_prefix=None,
                pre_release_filter=None,
                version_filter=None,
                regex="DEFAULT",
                insecure=False,
                user_id="noreply@fedoraproject.org",
                releases_only=False,
            )

    def test_edit_project_self_update_allowed(self):
        """Assert editing project attributes without colliding with another project succeeds."""
        create_project(self.session)
        project_objs = models.Project.all(self.session)

        with fml_testing.mock_sends(anitya_schema.ProjectEdited):
            utilities.edit_project(
                self.session,
                project=project_objs[0],
                name="geany-updated",
                homepage="https://www.geany.org/updated",
                backend="custom",
                version_scheme="RPM",
                version_pattern=None,
                version_url="https://www.geany.org/Download/Releases",
                version_prefix=None,
                pre_release_filter=None,
                version_filter=None,
                regex="DEFAULT",
                insecure=False,
                user_id="noreply@fedoraproject.org",
                releases_only=False,
            )

        self.assertEqual(project_objs[0].name, "geany-updated")


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
        """Test remove suffix no change"""
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
        """Test remove suffix remove releases"""
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
        """Test remove suffix remove tags"""
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


class CreateProjectValidationTests(DatabaseTestCase):
    """Tests for create_project with validate=True."""

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0", "0.9.9"],
    )
    def test_create_project_validate_success(self, mock_method):
        """Test that a valid project is created when validation passes."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            project = utilities.create_project(
                self.session,
                name="test_project",
                homepage="https://example.com/test",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                validate=True,
            )
        mock_method.assert_called_once()
        self.assertEqual(project.name, "test_project")
        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 1)

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        mock.Mock(
            side_effect=exceptions.AnityaPluginException("Could not contact npmjs")
        ),
    )
    def test_create_project_validate_failure(self):
        """Test that InvalidProjectException is raised and nothing is saved."""
        with self.assertRaises(exceptions.InvalidProjectException) as ctx:
            utilities.create_project(
                self.session,
                name="bad_project",
                homepage="https://example.com/nonexistent",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                validate=True,
            )
        self.assertIn("could not retrieve versions", str(ctx.exception))
        self.assertIn("Could not contact npmjs", str(ctx.exception))

        # Nothing saved
        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 0)

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        mock.Mock(side_effect=exceptions.RateLimitException("2099-01-01T00:00:00Z")),
    )
    def test_create_project_validate_rate_limit(self):
        """Test that rate limiting during validation raises InvalidProjectException."""
        with self.assertRaises(exceptions.InvalidProjectException):
            utilities.create_project(
                self.session,
                name="rate_limited_project",
                homepage="https://example.com/ratelimit",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
                validate=True,
            )

        # Nothing saved
        project_objs = models.Project.all(self.session)
        self.assertEqual(len(project_objs), 0)

    @mock.patch(
        "anitya.lib.backends.npmjs.NpmjsBackend.get_versions",
        return_value=["1.0.0"],
    )
    def test_create_project_without_validate(self, mock_method):
        """Test that validate=False (default) skips the check."""
        with fml_testing.mock_sends(anitya_schema.ProjectCreated):
            utilities.create_project(
                self.session,
                name="no_validate",
                homepage="https://example.com/skip",
                backend="npmjs",
                user_id="noreply@fedoraproject.org",
            )
        # get_versions should NOT be called when validate is not set
        mock_method.assert_not_called()

    def test_create_project_validate_invalid_backend(self):
        """Test that validation fails for a missing backend."""
        with self.assertRaises(exceptions.AnityaException) as ctx:
            utilities.create_project(
                self.session,
                name="bad_backend",
                homepage="https://example.com/bad",
                backend="nonexistent_backend",
                user_id="noreply@fedoraproject.org",
                validate=True,
            )
        self.assertIn(
            'No backend was found for "nonexistent_backend"', str(ctx.exception)
        )
