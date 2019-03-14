# -*- coding: utf-8 -*-
#
# Copyright © 2019  Red Hat, Inc.
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
Anitya tests for check service.
"""

import unittest
from unittest import mock
from datetime import timedelta

import arrow

from anitya.db import models
from anitya.tests.base import DatabaseTestCase
from anitya.check_service import Checker
from anitya.lib import exceptions


class CheckerTests(DatabaseTestCase):
    """ Checker class tests. """

    def setUp(self):
        """
        Prepare the Checker object.
        """
        super(CheckerTests, self).setUp()
        self.checker = Checker()

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_update_project_backend_blacklist(self, mock_check_project_release):
        """
        Assert that project next_check is set to correct_time when backend
        is blacklisted.
        """
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=arrow.utcnow().datetime,
        )
        self.session.add(project)
        self.session.commit()
        reset_time = project.next_check + timedelta(hours=1)

        with mock.patch.dict(self.checker.blacklist_dict, {"GitHub": reset_time}):
            self.checker.update_project(project.id)

        self.assertEqual(project.next_check, reset_time)
        self.assertEqual(self.checker.ratelimit_counter, 1)
        self.assertEqual(self.checker.success_counter, 0)
        self.assertEqual(self.checker.error_counter, 0)
        self.assertEqual(self.checker.ratelimit_queue["GitHub"][0], project.id)

    @mock.patch(
        "anitya.lib.utilities.check_project_release",
        mock.Mock(side_effect=exceptions.AnityaException("")),
    )
    def test_update_project_anitya_plugin_exception(self):
        """
        Assert that error counter is incremented when `exceptions.AnityaException`
        happens.
        """
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=arrow.utcnow().datetime,
        )
        self.session.add(project)
        self.session.commit()

        self.checker.update_project(project.id)

        self.assertEqual(self.checker.ratelimit_counter, 0)
        self.assertEqual(self.checker.success_counter, 0)
        self.assertEqual(self.checker.error_counter, 1)

    @mock.patch(
        "anitya.lib.utilities.check_project_release",
        mock.Mock(
            side_effect=exceptions.RateLimitException("2008-09-03T20:56:35.450686")
        ),
    )
    def test_update_project_ratelimit_exception(self):
        """
        Assert that project is blacklisted when `exceptions.RatelimitException`
        happens.
        """
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=arrow.utcnow().datetime,
        )
        self.session.add(project)
        self.session.commit()

        reset_time = arrow.get("2008-09-03T20:56:35.450686").datetime

        self.checker.update_project(project.id)

        self.assertEqual(self.checker.ratelimit_counter, 1)
        self.assertEqual(self.checker.success_counter, 0)
        self.assertEqual(self.checker.error_counter, 0)
        self.assertEqual(self.checker.blacklist_dict["GitHub"], reset_time)
        self.assertEqual(self.checker.ratelimit_queue["GitHub"][0], project.id)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_update_project_success(self, mock_check_project_release):
        """
        Assert that correct counter is increased when the project is successfully
        checked.
        """
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=arrow.utcnow().datetime,
        )
        self.session.add(project)
        self.session.commit()

        self.checker.update_project(project.id)

        self.assertEqual(self.checker.ratelimit_counter, 0)
        self.assertEqual(self.checker.success_counter, 1)
        self.assertEqual(self.checker.error_counter, 0)

    def test_blacklist_project(self):
        """
        Assert that project is correctly blacklisted.
        """
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=arrow.utcnow().datetime,
        )
        self.session.add(project)
        self.session.commit()
        reset_time = arrow.get(project.next_check + timedelta(hours=1))

        self.checker.blacklist_project(project, reset_time)

        self.assertEqual(self.checker.blacklist_dict["GitHub"], reset_time)
        self.assertEqual(self.checker.ratelimit_counter, 1)
        self.assertEqual(self.checker.success_counter, 0)
        self.assertEqual(self.checker.error_counter, 0)
        self.assertEqual(self.checker.ratelimit_queue["GitHub"][0], project.id)

    @mock.patch("anitya.check_service.Checker.update_project")
    def test_run(self, mock_update_project):
        """
        Assert that `db.Run` is created at the end of run.
        """
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=arrow.utcnow().datetime,
        )
        self.session.add(project)
        self.session.commit()

        self.checker.run()

        run_objects = models.Run.query.all()

        self.assertEqual(len(run_objects), 1)
        self.assertEqual(run_objects[0].total_count, 1)
        self.assertEqual(run_objects[0].error_count, 0)
        self.assertEqual(run_objects[0].ratelimit_count, 0)
        self.assertEqual(run_objects[0].success_count, 0)
        mock_update_project.called_once_with(project.id)

    @mock.patch("anitya.lib.utilities.check_project_release")
    def test_run_nothing_to_check(self, mock_check_project_release):
        """
        Assert that nothing is done if no project is ready to check.
        """
        self.checker.run()

        run_objects = models.Run.query.all()

        self.assertEqual(len(run_objects), 0)
        mock_check_project_release.assert_not_called()

    def test_clear_counters(self):
        """
        Assert that counters are cleared.
        """
        self.checker.error_counter = 10
        self.checker.ratelimit_counter = 10
        self.checker.success_counter = 10

        self.checker.clear_counters()

        self.assertEqual(self.checker.error_counter, 0)
        self.assertEqual(self.checker.ratelimit_counter, 0)
        self.assertEqual(self.checker.success_counter, 0)

    def test_construct_queue_not_ready(self):
        """
        Assert that no project is added to queue when no project
        is ready.
        """
        time = arrow.utcnow().datetime
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=time + timedelta(hours=1),
        )
        self.session.add(project)
        self.session.commit()

        queue = self.checker.construct_queue(time)

        self.assertEqual(len(queue), 0)

    def test_construct_queue_duplicates(self):
        """
        Assert that duplicate projects aren't added to queue.
        """
        time = arrow.utcnow().datetime
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=time,
        )
        self.session.add(project)
        self.session.commit()

        self.checker.ratelimit_queue = {"Github": [project.id]}
        self.checker.blacklist_dict = {"Github": time}

        queue = self.checker.construct_queue(time + timedelta(hours=1))

        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0], project.id)

    def test_construct_queue_order(self):
        """
        Assert that order of projects is kept in the queue.
        """
        time = arrow.utcnow().datetime
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=time,
        )
        self.session.add(project)

        project2 = models.Project(
            name="Foobar2",
            backend="GitHub",
            homepage="www.fakeproject2.com",
            next_check=time,
        )
        self.session.add(project2)
        self.session.commit()

        self.checker.ratelimit_queue = {"Github": [project.id]}
        self.checker.blacklist_dict = {"Github": time}

        queue = self.checker.construct_queue(time + timedelta(hours=1))

        self.assertEqual(len(queue), 2)
        self.assertEqual(queue[0], project.id)
        self.assertEqual(queue[1], project2.id)

    def test_construct_ratelimit_clean(self):
        """
        Assert that ratelimit queue and dictionary is correctly cleared.
        """
        time = arrow.utcnow().datetime
        project = models.Project(
            name="Foobar",
            backend="GitHub",
            homepage="www.fakeproject.com",
            next_check=time,
        )
        self.session.add(project)
        self.session.commit()

        self.checker.ratelimit_queue = {"Github": [project.id]}
        self.checker.blacklist_dict = {"Github": time}

        self.checker.construct_queue(time + timedelta(hours=1))

        self.assertEqual(self.checker.ratelimit_queue.get("Github", None), None)
        self.assertEqual(self.checker.blacklist_dict.get("Github", None), None)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(CheckerTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
