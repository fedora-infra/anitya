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
"""This module contains functions that are triggered by SQLAlchemy events."""
import logging

from sqlalchemy import event

from anitya.lib import plugins
from .models import Project


_log = logging.getLogger(__name__)


def _set_ecosystem(project, backend, homepage):
    """
    Set ecosystem to correct value. Priority is as follows:
        1. Ecosystem is set to backend if backend is associated with ecosystem
        2. Ecosystem is set to homepage

    Args:
        project (models.Project): Instance of project
        backend (str): value of backend
        homepage (str): value of homepage
    """
    ecosystems = [
        e
        for e in plugins.ECOSYSTEM_PLUGINS.get_plugins()
        if e.default_backend == backend
    ]
    if ecosystems:
        project.ecosystem_name = ecosystems[0].name
    else:
        project.ecosystem_name = homepage
    _log.info(
        "Settings the ecosystem on %r to %s", project.name, project.ecosystem_name
    )


@event.listens_for(Project.backend, "set", raw=True)
def set_ecosystem_backend(target, value, old, initiator):
    """
    An SQLAlchemy event listener that sets the ecosystem for a project if backend is changed.

    Args:
        target (sqlalchemy.orm.state.InstanceStace): Instance of the object where
                change is happening.
        value (str): The new value of backend.
        old (str): The old value of backend.
        initiator (sqlalchemy.orm.attributes.Event): The event object that is initiating this
                transition.
    """
    if value != old:
        project = target.object
        _set_ecosystem(project, value, project.homepage)


@event.listens_for(Project.homepage, "set", raw=True)
def set_ecosystem_homepage(target, value, old, initiator):
    """
    An SQLAlchemy event listener that sets the ecosystem for a project if homepage is changed.

    Args:
        target (sqlalchemy.orm.state.InstanceStace): Instance of the object where
                change is happening.
        value (str): The new value of homepage.
        old (str): The old value of homepage.
        initiator (sqlalchemy.orm.attributes.Event): The event object that is initiating this
                transition.
    """
    if value != old:
        project = target.object
        _set_ecosystem(project, project.backend, value)
