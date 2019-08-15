#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2018  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""
This is a service that is checking for new releases in projects added to Anitya.
"""

import logging
from threading import Lock
from typing import List
from datetime import datetime
from time import sleep
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

import sqlalchemy as sa
import arrow
from ordered_set import OrderedSet

from anitya.config import config
from anitya import db
from anitya.lib import utilities
from anitya.lib.exceptions import AnityaException, RateLimitException

_log = logging.getLogger("anitya")

# Wait time used between runs
WAIT_TIME = 300


class Checker:
    """
    This class is handling the checks for new releases.

    Attributes:
        error_counter (int): Number of errors in current run
        error_counter_lock (`Lock`): Lock for `error_counter`
        ratelimit_counter (int): Number of projects that were not check because
            of the rate limit
        ratelimit_counter_lock (`Lock`): Lock for `ratelimit_counter`
        success_counter (int): Number of projects successfully checked.
        success_counter_lock (`Lock`): Lock for `success_counter`
        ratelimit_queue (dict of str:list(int)): Queue that contains
            every project that wasn't check when ratelimit was reached. The key is
            backend that reached the rate limit and the value is list of projects
        ratelimit_queue_lock (`Lock`): Lock for `ratelimit_queue`
        blacklist_dict (dict of str:`datetime`): Blacklisted backends, key is name of
            the ratelimited backend and value is `datetime` object containing time when
            ratelimit will be reset
        blacklist_dict_lock (`Lock`): Lock for `blacklist_dict`
    """

    def __init__(self):
        """
        Constructor for Checker class.
        """
        self.error_counter_lock = Lock()
        self.error_counter = 0
        self.ratelimit_counter_lock = Lock()
        self.ratelimit_counter = 0
        self.success_counter_lock = Lock()
        self.success_counter = 0
        self.ratelimit_queue_lock = Lock()
        self.ratelimit_queue = {}
        self.blacklist_dict_lock = Lock()
        self.blacklist_dict = {}
        _log.debug("Checker class initialized")

    def update_project(self, project_id: int) -> None:
        """
        Check for updates on the specified project.

        Args:
            project_id: Id of project to check
        """
        session = db.Session()
        project = db.Project.query.filter(db.Project.id == project_id).one()
        if project.backend in self.blacklist_dict:
            self.blacklist_project(project, self.blacklist_dict[project.backend])
            _log.info(
                "Backend is blacklisted. Rescheduling to {}".format(
                    self.blacklist_dict[project.backend]
                )
            )
            project.next_check = self.blacklist_dict[project.backend]
            session.add(project)
            session.commit()
            return
        try:
            utilities.check_project_release(project, session)
        except RateLimitException as err:
            self.blacklist_project(project, err.reset_time)
            return
        except AnityaException as err:
            _log.info(err)
            with self.error_counter_lock:
                self.error_counter += 1
            return

        with self.success_counter_lock:
            self.success_counter += 1

    def blacklist_project(self, project: db.Project, reset_time: arrow.Arrow):
        """
        Add specified project to `self.ratelimit_queue`, add backend to
        `self.blacklist_dict` and increment `self.ratelimit_counter`.

        Args:
            project: Project to blacklist
            reset_time: Time when the ratelimit will be reset
        """
        with self.blacklist_dict_lock:
            if project.backend not in self.blacklist_dict:
                _log.debug(
                    "Rate limit threshold reached. Adding {} to blacklist.".format(
                        project.backend
                    )
                )
                self.blacklist_dict[project.backend] = reset_time.to("utc").datetime
        with self.ratelimit_queue_lock:
            if project.backend not in self.ratelimit_queue:
                self.ratelimit_queue[project.backend] = []

            self.ratelimit_queue[project.backend].append(project.id)

        with self.ratelimit_counter_lock:
            self.ratelimit_counter += 1

    def run(self):
        """
        Start the check run, the run is made of three stages:
        1. Preparation - get current date, clear counters, prepare queue
            of project
        2. Execution - process every project in the queue
        3. Finalize - create `db.Run` entry with counters and time
        """
        # 1. Preparation phase
        # We must convert it to datetime for comparison with sqlalchemy TIMESTAMP column
        session = db.Session()
        time = arrow.utcnow().datetime
        self.clear_counters()
        queue = self.construct_queue(time)
        total_count = len(queue)

        if not queue:
            return

        # 2. Execution
        _log.info(
            "Starting check on {} for total of {} projects".format(time, total_count)
        )
        pool_size = config.get("CRON_POOL", 10)
        pool = ThreadPoolExecutor(pool_size)
        futures = [pool.submit(self.update_project, project) for project in queue]

        # Wait till every project is checked
        wait(futures, return_when=ALL_COMPLETED)

        # 3. Finalize
        _log.info(
            "Check done. Checked ({}): error ({}), success ({}), fail ({})".format(
                total_count,
                self.error_counter,
                self.success_counter,
                self.error_counter,
            )
        )

        run = db.Run(
            created_on=time,
            total_count=total_count,
            error_count=self.error_counter,
            ratelimit_count=self.ratelimit_counter,
            success_count=self.success_counter,
        )
        session.add(run)
        session.commit()

    def clear_counters(self):
        """
        Clear all counters.
        """
        with self.error_counter_lock:
            self.error_counter = 0
        with self.ratelimit_counter_lock:
            self.ratelimit_counter = 0
        with self.success_counter_lock:
            self.success_counter = 0

    def construct_queue(self, time: datetime) -> List[int]:
        """
        Construct queue of projects for current run. This queue will be created from
        every project that is ready to check and those that were blacklisted because
        of ratelimit in previous run.

        Args:
            time: Start of the current run

        Returns:
            Queue of project's ids to check. Blacklisted projects will be on start of
            the queue
        """
        queue = []
        # Add blacklisted items first
        backends = []
        for (backend, reset_time) in self.blacklist_dict.items():
            if reset_time < time:
                with self.ratelimit_queue_lock:
                    queue += self.ratelimit_queue[backend]
                    # Erase project list after adding it to queue
                    del self.ratelimit_queue[backend]

                backends.append(backend)

        # Erase backends that were processed from blacklist dictionary
        for backend in backends:
            del self.blacklist_dict[backend]

        # Get all projects, that are ready for check
        projects = (
            db.Project.query.order_by(sa.func.lower(db.Project.name))
            .filter(db.Project.next_check < time)
            .all()
        )

        queue += [project.id for project in projects]

        # Use ordered set to have the order of the elements, but still have uniqueness
        ord_set = OrderedSet(queue)

        return list(ord_set)


if __name__ == "__main__":
    # Main
    db.initialize(config)
    checker = Checker()
    while True:
        checker.run()
        sleep(WAIT_TIME)
