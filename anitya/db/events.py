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
from .meta import Session
from .models import Project


_log = logging.getLogger(__name__)


@event.listens_for(Session, "before_flush")
def set_ecosystem(session, flush_context, instances):
    """
    An SQLAlchemy event listener that sets the ecosystem for a project if it's null.

    Args:
        session (sqlalchemy.orm.session.Session): The session that is about to be committed.
        flush_context (sqlalchemy.orm.session.UOWTransaction): Unused.
        instances (object): deprecated and unused

    Raises:
        ValueError: If the ecosystem_name isn't valid.
    """
    for new_obj in session.new:
        if isinstance(new_obj, Project):
            if new_obj.ecosystem_name is None:
                ecosystems = [
                    e
                    for e in plugins.ECOSYSTEM_PLUGINS.get_plugins()
                    if e.default_backend == new_obj.backend
                ]
                if ecosystems:
                    new_obj.ecosystem_name = ecosystems[0].name
                else:
                    new_obj.ecosystem_name = new_obj.homepage
                _log.info(
                    "Settings the ecosystem on %r to %s by default",
                    new_obj,
                    new_obj.ecosystem_name,
                )
            else:
                # Validate the field
                valid_names = [e.name for e in plugins.ECOSYSTEM_PLUGINS.get_plugins()]
                valid_names.append(new_obj.homepage)
                if new_obj.ecosystem_name not in valid_names:
                    raise ValueError(
                        'Invalid ecosystem_name "{}", must be one of {}'.format(
                            new_obj.ecosystem_name, valid_names
                        )
                    )
