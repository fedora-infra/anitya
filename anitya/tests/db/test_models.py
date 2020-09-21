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
#

"""
anitya tests of the models.
"""

from uuid import uuid4, UUID
import unittest
import time
import mock
import datetime

from fedora_messaging import testing as fml_testing
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.types import CHAR
from sqlalchemy.exc import IntegrityError
from social_flask_sqlalchemy import models as social_models
import six
import arrow

from anitya.db import models
from anitya.lib import versions
from anitya.tests.base import (
    DatabaseTestCase,
    create_distro,
    create_project,
    create_package,
    create_flagged_project,
)
from anitya.lib import utilities
import anitya_schema


class ProjectTests(DatabaseTestCase):
    """Tests for the Project models."""

    def test_init_project(self):
        """ Test the __init__ function of Project. """
        create_project(self.session)
        self.assertEqual(3, models.Project.all(self.session, count=True))

        projects = models.Project.all(self.session)
        self.assertEqual(projects[0].name, "geany")
        self.assertEqual(projects[1].name, "R2spec")
        self.assertEqual(projects[2].name, "subsurface")

    def test_validate_backend(self):
        project = models.Project(
            name="test", homepage="https://example.com", backend="custom"
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(models.Project).count())
        self.assertEqual("custom", self.session.query(models.Project).one().backend)

    def test_validate_backend_bad(self):
        self.assertRaises(
            ValueError,
            models.Project,
            name="test",
            homepage="https://example.com",
            backend="Nope",
        )

    def test_validate_ecosystem_good(self):
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(models.Project).count())
        self.assertEqual(
            "pypi", self.session.query(models.Project).one().ecosystem_name
        )

    def test_ecosystem_in_json(self):
        """Assert the ecosystem is included in the dict returned from ``__json__``"""
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
        )
        self.assertEqual("pypi", project.__json__()["ecosystem"])

    def test_create_version_objects_RPM(self):
        """
        Assert that the correct version objects list is returned (RPM version scheme).
        """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            version_scheme="RPM",
            version_prefix="test-",
        )
        self.session.add(project)
        self.session.commit()

        versions_list = ["test-0.1.0", "test-0.2.0", "test-0.3.0"]

        versions = project.create_version_objects(versions_list)

        self.assertEqual(len(versions), 3)
        self.assertEqual(str(versions[0]), "0.1.0")
        self.assertEqual(str(versions[1]), "0.2.0")
        self.assertEqual(str(versions[2]), "0.3.0")

    def test_create_version_objects_empty(self):
        """
        Assert that the `create_version_objects` method returns nothing on empty list.
        """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            version_scheme="RPM",
            version_prefix="test-",
        )
        self.session.add(project)
        self.session.commit()

        versions_list = []

        versions = project.create_version_objects(versions_list)

        self.assertEqual(len(versions), 0)

    def test_get_version_url_no_backend(self):
        """ Assert that empty string is returned when backend is not specified. """
        project = models.Project(
            name="test", homepage="https://example.com", ecosystem_name="pypi"
        )
        self.assertEqual("", project.get_version_url())

    def test_get_version_url(self):
        """ Assert that correct url is returned. """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            version_url="https://example.com/releases",
            ecosystem_name="pypi",
        )
        self.assertEqual(project.version_url, project.get_version_url())

    def test_stable_versions(self):
        """
        Assert that only stable versions are retrieved.
        """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            ecosystem_name="pypi",
            version_scheme="Semantic",
        )
        self.session.add(project)
        self.session.commit()

        version_stable = models.ProjectVersion(project_id=project.id, version="1.0.0")
        version_pre_release = models.ProjectVersion(
            project_id=project.id, version="1.0.0-alpha"
        )
        self.session.add(version_stable)
        self.session.add(version_pre_release)
        self.session.commit()

        versions = project.stable_versions

        self.assertEqual([str(version) for version in versions], ["1.0.0"])

    def test_get_last_created_version(self):
        """
        Assert that last retrieved version is returned.
        """
        project = models.Project(
            name="test", homepage="https://example.com", ecosystem_name="pypi"
        )
        self.session.add(project)
        self.session.commit()

        version_first = models.ProjectVersion(project_id=project.id, version="1.0")
        version_second = models.ProjectVersion(project_id=project.id, version="0.8")
        self.session.add(version_first)
        self.session.add(version_second)
        self.session.commit()

        version = project.get_last_created_version()

        self.assertEqual(version, version_second)

    def test_get_last_created_version_no_date_one_version(self):
        """
        Assert that last retrieved version is returned,
        when one of the versions doesn't have date filled.
        """
        project = models.Project(
            name="test", homepage="https://example.com", ecosystem_name="pypi"
        )
        self.session.add(project)
        self.session.commit()

        version_first = models.ProjectVersion(project_id=project.id, version="1.0")
        version_second = models.ProjectVersion(project_id=project.id, version="0.8")
        self.session.add(version_first)
        self.session.add(version_second)
        self.session.commit()
        version_first.created_on = None

        version = project.get_last_created_version()

        self.assertEqual(version, version_second)

    def test_get_last_created_version_no_date_all_versions(self):
        """
        Assert that None is returned,
        when every version doesn't have date filled.
        """
        project = models.Project(
            name="test", homepage="https://example.com", ecosystem_name="pypi"
        )
        self.session.add(project)
        self.session.commit()

        version_first = models.ProjectVersion(project_id=project.id, version="1.0")
        version_second = models.ProjectVersion(project_id=project.id, version="0.8")
        self.session.add(version_first)
        self.session.add(version_second)
        self.session.commit()
        version_first.created_on = None
        version_second.created_on = None

        version = project.get_last_created_version()

        self.assertEqual(version, None)

    def test_get_time_last_created_version(self):
        """
        Assert that time of last retrieved version is returned.
        """
        project = models.Project(
            name="test", homepage="https://example.com", ecosystem_name="pypi"
        )
        self.session.add(project)
        self.session.commit()

        time_now = arrow.utcnow()
        version = models.ProjectVersion(
            project_id=project.id, created_on=time_now.datetime, version="1.0"
        )
        self.session.add(version)
        self.session.commit()

        last_version_time = project.get_time_last_created_version()

        self.assertEqual(last_version_time, time_now)

    def test_get_sorted_version_objects(self):
        """Assert that sorted versions are included in the list returned from
        :data:`Project.get_sorted_version_objects`.
        """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="RPM",
        )
        self.session.add(project)
        self.session.commit()

        version_first = models.ProjectVersion(project_id=project.id, version="0.8")
        version_second = models.ProjectVersion(project_id=project.id, version="1.0")
        self.session.add(version_first)
        self.session.add(version_second)
        self.session.commit()

        versions = project.get_sorted_version_objects()

        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version, version_second.version)
        self.assertEqual(versions[1].version, version_first.version)

    def test_latest_version_object_with_versions(self):
        """Test the latest_version_object property with versions."""
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="RPM",
        )
        self.session.add(project)
        self.session.flush()

        version_first = models.ProjectVersion(project_id=project.id, version="0.8")
        version_second = models.ProjectVersion(project_id=project.id, version="1.0")
        self.session.add(version_first)
        self.session.add(version_second)
        self.session.flush()

        self.assertEqual(project.latest_version_object.version, version_second.version)

    def test_latest_version_object_without_versions(self):
        """Test the latest_version_object property without versions."""
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="RPM",
        )
        self.session.add(project)
        self.session.flush()

        self.assertIsNone(project.latest_version_object)

    def test_get_version_class(self):
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="RPM",
        )
        version_class = project.get_version_class()
        self.assertEqual(version_class, versions.RpmVersion)

    def test_get_version_class_missing(self):
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="Invalid",
        )
        version_class = project.get_version_class()
        self.assertEqual(version_class, None)

    def test_project_all(self):
        """ Test the Project.all function. """
        create_project(self.session)

        projects = models.Project.all(self.session, count=True)
        self.assertEqual(projects, 3)

        projects = models.Project.all(self.session, page=2)
        self.assertEqual(len(projects), 0)

        projects = models.Project.all(self.session, page="asd")
        self.assertEqual(len(projects), 3)

    def test_project_search(self):
        """ Test the Project.search function. """
        create_project(self.session)
        create_package(self.session)

        projects = models.Project.search(self.session, "*", count=True)
        self.assertEqual(projects, 3)

        projects = models.Project.search(self.session, "*", page=2)
        self.assertEqual(len(projects), 0)

        projects = models.Project.search(self.session, "*", page="asd")
        self.assertEqual(len(projects), 3)

    def test_project_search_no_pattern(self):
        """
        Assert that all projects are returned when
        no pattern is provided.
        """
        create_project(self.session)

        projects = models.Project.search(self.session, "")
        self.assertEqual(len(projects), 3)

    def test_project_search_by_distro(self):
        """
        Assert that only projects with mappings to specific distro
        are returned when distro is provided.
        """
        create_project(self.session)
        create_package(self.session)
        # Create mapping for another distro to be sure that only Fedora mappings
        # are taken into account
        package = models.Packages(distro_name="Debian", project_id=3)
        self.session.add(package)
        self.session.commit()

        projects = models.Project.search(self.session, "*", distro="Fedora")
        self.assertEqual(len(projects), 2)

    def test_project_get_or_create(self):
        """ Test the Project.get_or_create function. """
        project = models.Project.get_or_create(
            self.session, name="test", homepage="https://test.org", backend="custom"
        )
        self.assertEqual(project.name, "test")
        self.assertEqual(project.homepage, "https://test.org")
        self.assertEqual(project.backend, "custom")

    def test_project_get_or_create_exception(self):
        """
        Assert that exception is raised when incorrect
        backend is provided.
        """
        self.assertRaises(
            ValueError,
            models.Project.get_or_create,
            self.session,
            name="test_project",
            homepage="https://project.test.org",
            backend="foobar",
        )

    def test_project_delete_cascade(self):
        """ Assert deletion of mapped packages when project is deleted """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="Invalid",
        )
        self.session.add(project)

        package = models.Packages(
            project_id=1, distro_name="Fedora", package_name="test"
        )
        self.session.add(package)
        self.session.commit()

        projects = self.session.query(models.Project).all()
        self.assertEqual(len(projects), 1)
        self.assertEqual(len(projects[0].package), 1)

        self.session.delete(projects[0])
        self.session.commit()

        projects = self.session.query(models.Project).all()
        packages = self.session.query(models.Packages).all()
        self.assertEqual(len(projects), 0)
        self.assertEqual(len(packages), 0)

        create_flagged_project(self.session)
        projects = self.session.query(models.Project).all()
        self.assertEqual(len(projects), 1)
        self.assertEqual(len(projects[0].flags), 1)

        self.session.delete(projects[0])
        self.session.commit()

        projects = self.session.query(models.Project).all()
        packages = self.session.query(models.ProjectFlag).all()
        self.assertEqual(len(projects), 0)
        self.assertEqual(len(packages), 0)

    def test_project_get_or_create_get(self):
        """
        Assert that project is only returned when existing name
        is provided.
        """
        create_project(self.session)
        pre_projects = models.Project.search(self.session, "*", count=True)
        project = models.Project.get_or_create(
            self.session, name="geany", homepage="https://www.geany.org/"
        )
        post_projects = models.Project.search(self.session, "*", count=True)
        self.assertEqual(project.name, "geany")
        self.assertEqual(project.homepage, "https://www.geany.org/")
        self.assertEqual(pre_projects, post_projects)

    def test_project_updated_new(self):
        """
        Assert that only new projects are returned when status is
        set to 'new'.
        """
        create_project(self.session)

        projects = models.Project.updated(self.session, status="new")
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].logs, None)

    def test_project_updated_newer_updated(self):
        """
        Assert that only not updated projects are returned when status is
        set to 'newer_updated'.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).all():
            project.logs = "something"
            project.latest_version = None
        self.session.commit()

        projects = models.Project.updated(self.session, status="never_updated")
        self.assertEqual(len(projects), 3)
        self.assertEqual(projects[0].logs, "something")

    def test_project_updated_failed(self):
        """
        Assert that only update failed projects are returned when status is
        set to 'failed'.
        """
        create_project(self.session)
        error_counter = 0
        for project in self.session.query(models.Project).all():
            project.check_successful = False
            project.error_counter = error_counter
            error_counter += 1
        self.session.commit()

        projects = models.Project.updated(self.session, status="failed")
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0].error_counter, 2)
        self.assertEqual(projects[1].error_counter, 1)

    def test_project_updated_odd(self):
        """
        Assert that only odd updated projects are returned when status is
        set to 'odd'.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Something strange occured"
        self.session.commit()

        projects = models.Project.updated(self.session, status="odd")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].logs, "Something strange occured")

    def test_project_updated_updated(self):
        """
        Assert that only updated projects are returned when status is
        set to 'updated'.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        projects = models.Project.updated(self.session, status="updated")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].logs, "Version retrieved correctly")

    def test_project_updated_incorrect_status(self):
        """
        Assert that all projects are returned when incorrect status is used.
        """
        create_project(self.session)
        projects = models.Project.updated(self.session, status="incorrect")
        self.assertEqual(len(projects), 3)

    def test_project_updated_name_pattern(self):
        """
        Assert that correct project is returned when pattern as name is used.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        projects = models.Project.updated(self.session, name="gean*")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].name, "geany")

    def test_project_updated_name(self):
        """
        Assert that correct project is returned when exact name is used.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        projects = models.Project.updated(self.session, name="geany")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].name, "geany")

    def test_project_updated_log_pattern(self):
        """
        Assert that correct project is returned when log pattern is used.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        projects = models.Project.updated(self.session, log="*retrieved*")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].name, "geany")

    def test_project_updated_log(self):
        """
        Assert that log argument is automatically changed to pattern.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()

        projects = models.Project.updated(self.session, log="retrieved")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].name, "geany")

    def test_project_updated_count(self):
        """
        Assert that correct count is returned.
        """
        create_project(self.session)
        for project in self.session.query(models.Project).filter(
            models.Project.id == 1
        ):
            project.logs = "Version retrieved correctly"
        self.session.commit()
        projects = models.Project.updated(self.session, count=True)
        self.assertEqual(projects, 1)


class DistroTestCase(DatabaseTestCase):
    """ Tests for Distro model. """

    def test_init_distro(self):
        """ Test the __init__ function of Distro. """
        create_distro(self.session)
        self.assertEqual(2, models.Distro.all(self.session, count=True))

        distros = models.Distro.all(self.session)
        self.assertEqual(distros[0].name, "Debian")
        self.assertEqual(distros[1].name, "Fedora")

    def test_distro_delete_cascade(self):
        """ Assert deletion of mapped packages when project is deleted """
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="Invalid",
        )
        self.session.add(project)

        distro = models.Distro(name="Fedora")
        self.session.add(distro)

        package = models.Packages(
            project_id=1, distro_name="Fedora", package_name="test"
        )
        self.session.add(package)
        self.session.commit()

        distros = self.session.query(models.Distro).all()

        self.assertEqual(len(distros), 1)
        self.assertEqual(len(distros[0].package), 1)

        self.session.delete(distros[0])
        self.session.commit()

        distros = self.session.query(models.Distro).all()
        packages = self.session.query(models.Packages).all()

        self.assertEqual(len(distros), 0)
        self.assertEqual(len(packages), 0)

    def test_distro_search_count(self):
        """ Assert that `Distro.search` returns correct count. """
        create_distro(self.session)

        logs = models.Distro.search(self.session, "*", count=True)
        self.assertEqual(logs, 2)

    def test_distro_search_pattern(self):
        """
        Assert that `Distro.search` returns correct distribution,
        when pattern is used.
        """
        create_distro(self.session)

        logs = models.Distro.search(self.session, "Fed*")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, "Fedora")

    def test_distro_search_page(self):
        """
        Assert that pagination is working in `Distro.search`.
        """
        create_distro(self.session)

        logs = models.Distro.search(self.session, "Fed*", page=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, "Fedora")

    def test_distro_search_incorrect_page(self):
        """
        Assert that pagination is automatically adjusted if incorrect value is used
        in `Distro.search`.
        """
        create_distro(self.session)

        logs = models.Distro.search(self.session, "Fed*", page="as")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].name, "Fedora")


class ProjectVersion(DatabaseTestCase):
    """ Tests for ProjectVersion model. """

    def test_pre_release(self):
        """Test the pre_release property on version."""
        project = models.Project(
            name="test",
            homepage="https://example.com",
            backend="custom",
            ecosystem_name="pypi",
            version_scheme="Semantic",
        )
        self.session.add(project)
        self.session.flush()

        version = models.ProjectVersion(
            project_id=project.id,
            version="v0.8.0-alpha",
            project=project,
        )
        self.session.add(version)
        self.session.flush()

        self.assertTrue(version.pre_release)


class PackageTestCase(DatabaseTestCase):
    """ Tests for Package model. """

    def test_packages_by_id(self):
        """ Test the Packages.by_id function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = models.Packages.by_id(self.session, 1)
        self.assertEqual(pkg.package_name, "geany")
        self.assertEqual(pkg.distro_name, "Fedora")

    def test_packages__repr__(self):
        """ Test the Packages.__repr__ function. """
        create_project(self.session)
        create_distro(self.session)
        create_package(self.session)

        pkg = models.Packages.by_id(self.session, 1)
        self.assertEqual(str(pkg), "<Packages(1, Fedora: geany)>")


class ProjectFlagTestCase(DatabaseTestCase):
    """ Tests for ProjectFlag model. """

    def test_project_flag__repr__(self):
        """ Test the ProjectFlag.__repr__ function. """
        flag = create_flagged_project(self.session)

        self.assertEqual(repr(flag), "<ProjectFlag(geany, dgay@redhat.com, open)>")

    def test_project_flag__json__(self):
        """ Test the ProjectFlag.__json__ function. """
        flag = create_flagged_project(self.session)
        data = {
            "created_on": time.mktime(flag.created_on.timetuple()),
            "user": "dgay@redhat.com",
            "state": "open",
            "project": "geany",
            "updated_on": time.mktime(flag.updated_on.timetuple()),
            "id": 1,
        }

        self.assertEqual(flag.__json__(), data)

        data["reason"] = "this is a duplicate."
        self.assertEqual(flag.__json__(detailed=True), data)

    def test_project_flag_all(self):
        """ Test the ProjectFlag.all function. """
        create_flagged_project(self.session)

        flags = models.ProjectFlag.all(self.session)
        self.assertEqual(len(flags), 1)

    def test_project_flag_search_by_name(self):
        """
        Assert that 'ProjectFlag.search' returns correct project
        if project name is provided.
        """
        flag = create_flagged_project(self.session)
        with fml_testing.mock_sends(anitya_schema.ProjectFlag):
            flag_add = utilities.flag_project(
                self.session,
                flag.project,
                "This is a duplicate.",
                "cthulhu@redhat.com",
                "user_openid_id",
            )
        flag_add.state = "closed"

        self.session.add(flag_add)

        self.session.commit()

        flags = models.ProjectFlag.search(self.session, project_name="geany")
        self.assertEqual(len(flags), 2)

    def test_project_flag_search_by_date(self):
        """
        Assert that 'ProjectFlag.search' returns correct project
        if from date is provided.
        """
        create_flagged_project(self.session)

        from_date = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
        flags = models.ProjectFlag.search(self.session, from_date=from_date)
        self.assertEqual(len(flags), 1)

    def test_project_flag_search_by_user(self):
        """
        Assert that 'ProjectFlag.search' returns correct project
        if from date is provided.
        """
        flag = create_flagged_project(self.session)
        with fml_testing.mock_sends(anitya_schema.ProjectFlag):
            flag_add = utilities.flag_project(
                self.session,
                flag.project,
                "This is a duplicate.",
                "cthulhu@redhat.com",
                "user_openid_id",
            )
        flag_add.state = "closed"
        self.session.add(flag_add)
        self.session.commit()
        user = flag.user

        flags = models.ProjectFlag.search(self.session, user=user)
        self.assertEqual(len(flags), 1)

    def test_project_flag_search_by_state(self):
        """
        Assert that 'ProjectFlag.search' returns correct project
        if state is provided.
        """
        flag = create_flagged_project(self.session)
        with fml_testing.mock_sends(anitya_schema.ProjectFlag):
            flag_add = utilities.flag_project(
                self.session,
                flag.project,
                "This is a duplicate.",
                "cthulhu@redhat.com",
                "user_openid_id",
            )
        flag_add.state = "closed"
        self.session.add(flag_add)
        self.session.commit()

        flags = models.ProjectFlag.search(self.session, state="open")
        self.assertEqual(len(flags), 1)

    def test_project_flag_search_offset(self):
        """
        Assert that 'ProjectFlag.search' returns correct project
        if offset is set.
        """
        flag = create_flagged_project(self.session)
        with fml_testing.mock_sends(anitya_schema.ProjectFlag):
            flag_add = utilities.flag_project(
                self.session,
                flag.project,
                "This is a duplicate.",
                "cthulhu@redhat.com",
                "user_openid_id",
            )
        flag_add.state = "closed"
        self.session.add(flag_add)
        self.session.commit()

        flags = models.ProjectFlag.search(self.session, offset=1)
        self.assertEqual(len(flags), 1)

    def test_project_flag_search_limit(self):
        """
        Assert that 'ProjectFlag.search' returns correct project
        if limit is set.
        """
        flag = create_flagged_project(self.session)
        with fml_testing.mock_sends(anitya_schema.ProjectFlag):
            flag_add = utilities.flag_project(
                self.session,
                flag.project,
                "This is a duplicate.",
                "cthulhu@redhat.com",
                "user_openid_id",
            )
        flag_add.state = "closed"
        self.session.add(flag_add)
        self.session.commit()

        flags = models.ProjectFlag.search(self.session, limit=1)
        self.assertEqual(len(flags), 1)

    def test_project_flag_search_count(self):
        """
        Assert that 'ProjectFlag.search' returns correct project
        if count is set.
        """
        flag = create_flagged_project(self.session)
        with fml_testing.mock_sends(anitya_schema.ProjectFlag):
            flag_add = utilities.flag_project(
                self.session,
                flag.project,
                "This is a duplicate.",
                "cthulhu@redhat.com",
                "user_openid_id",
            )
        flag_add.state = "closed"
        self.session.add(flag_add)
        self.session.commit()

        flags = models.ProjectFlag.search(self.session, count=True)
        self.assertEqual(flags, 2)


class GuidTests(unittest.TestCase):
    """Tests for the :class:`anitya.db.models.GUID` class."""

    def test_load_dialect_impl_postgres(self):
        """Assert with PostgreSQL, a UUID type is used."""
        guid = models.GUID()
        dialect = postgresql.dialect()

        result = guid.load_dialect_impl(dialect)

        self.assertTrue(isinstance(result, postgresql.UUID))

    def test_load_dialect_impl_other(self):
        """Assert with dialects other than PostgreSQL, a CHAR type is used."""
        guid = models.GUID()
        dialect = sqlite.dialect()

        result = guid.load_dialect_impl(dialect)

        self.assertTrue(isinstance(result, CHAR))

    def test_process_bind_param_uuid_postgres(self):
        """Assert UUIDs with PostgreSQL are normal string representations of UUIDs."""
        guid = models.GUID()
        uuid = uuid4()
        dialect = postgresql.dialect()

        result = guid.process_bind_param(uuid, dialect)

        self.assertEqual(str(uuid), result)

    def test_process_bind_param_uuid_other(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = models.GUID()
        uuid = uuid4()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(uuid, dialect)

        self.assertEqual(32, len(result))
        self.assertEqual(str(uuid).replace("-", ""), result)

    def test_process_bind_param_str_other(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = models.GUID()
        uuid = uuid4()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(str(uuid), dialect)

        self.assertEqual(32, len(result))
        self.assertEqual(str(uuid).replace("-", ""), result)

    def test_process_bind_param_none(self):
        """Assert UUIDs with other dialects are hex-encoded strings of length 32."""
        guid = models.GUID()
        dialect = sqlite.dialect()

        result = guid.process_bind_param(None, dialect)

        self.assertTrue(result is None)

    def test_process_result_value_none(self):
        """Assert when the result value is None, None is returned."""
        guid = models.GUID()

        self.assertTrue(guid.process_result_value(None, sqlite.dialect()) is None)

    def test_process_result_string(self):
        """Assert when the result value is a string, a native UUID is returned."""
        guid = models.GUID()
        uuid = uuid4()

        result = guid.process_result_value(str(uuid), sqlite.dialect())

        self.assertTrue(isinstance(result, UUID))
        self.assertEqual(uuid, result)

    def test_process_result_short_string(self):
        """Assert when the result value is a short string, a native UUID is returned."""
        guid = models.GUID()
        uuid = uuid4()

        result = guid.process_result_value(str(uuid).replace("-", ""), sqlite.dialect())

        self.assertTrue(isinstance(result, UUID))
        self.assertEqual(uuid, result)


class UserTests(DatabaseTestCase):
    def test_user_id(self):
        """Assert Users have a UUID id assigned to them."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertTrue(isinstance(user.id, UUID))

    def test_user_get_id(self):
        """Assert Users implements the Flask-Login API for getting user IDs."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertEqual(six.text_type(user.id), user.get_id())

    def test_user_email_unique(self):
        """Assert User emails have a uniqueness constraint on them."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        user = models.User(email="user@fedoraproject.org", username="user2")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)
        self.session.add(user)
        self.session.add(user_social_auth)
        self.assertRaises(IntegrityError, self.session.commit)

    def test_username_unique(self):
        """Assert User usernames have a uniqueness constraint on them."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        user = models.User(email="user2@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)
        self.session.add(user)
        self.session.add(user_social_auth)
        self.assertRaises(IntegrityError, self.session.commit)

    def test_default_active(self):
        """Assert User usernames have a uniqueness constraint on them."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertTrue(user.active)
        self.assertTrue(user.is_active)

    def test_not_anonymous(self):
        """Assert User implements the Flask-Login API for authenticated users."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertFalse(user.is_anonymous)
        self.assertTrue(user.is_authenticated)

    def test_default_admin(self):
        """Assert default value for admin flag."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        self.assertFalse(user.admin)
        self.assertFalse(user.is_admin)

    def test_is_admin_configured(self):
        """Assert default value for admin flag."""
        user = models.User(email="user@fedoraproject.org", username="user", admin=False)
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)
        self.session.add(user)
        self.session.add(user_social_auth)
        self.session.commit()

        mock_dict = mock.patch.dict(
            "anitya.config.config", {"ANITYA_WEB_ADMINS": [six.text_type(user.id)]}
        )

        with mock_dict:
            self.assertFalse(user.admin)
            self.assertTrue(user.is_admin)
            self.assertTrue(user.admin)

    def test_to_dict(self):
        """ Assert the correct dictionary is returned. """
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=user.id, user=user, provider="FAS"
        )
        user_social_auth.set_extra_data({"wookie": "too hairy"})
        self.session.add(user_social_auth)
        self.session.add(user)
        self.session.commit()

        expected = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "active": user.active,
            "social_auth": [
                {
                    "provider": user_social_auth.provider,
                    "extra_data": user_social_auth.extra_data,
                    "uid": user_social_auth.uid,
                }
            ],
        }

        json = user.to_dict()
        self.assertEqual(json, expected)


class ApiTokenTests(DatabaseTestCase):
    def test_token_default(self):
        """Assert creating an ApiToken generates a random token."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)

        token = models.ApiToken(user=user)
        self.session.add(token)
        self.session.commit()

        self.assertEqual(40, len(token.token))

    def test_user_relationship(self):
        """Assert users have a reference to their tokens."""
        user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(user_id=user.id, user=user)

        self.session.add(user)
        self.session.add(user_social_auth)

        token = models.ApiToken(user=user)
        self.session.add(token)
        self.session.commit()

        self.assertEqual(user.api_tokens, [token])


if __name__ == "__main__":
    unittest.main(verbosity=2)
