# -*- coding: utf-8 -*-
#
# Copyright © 2017  Red Hat, Inc.
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
"""
This module contains the `SQLAlchemy event listeners`_ for Anitya.

Anitya uses `SQLAlchemy event listeners`_ to perform tasks based on database
events. For example, when a new project is committed to the database, Anitya
publishes a message using `fedmsg`_.

.. note::
    In the future many events in this module should be accomplished with
    ``SessionEvents.pending_to_persistent``, but unfortunately that's new in
    1.1.0 and for the moment we need to support older versions of SQLAlchemy.

.. _SQLAlchemy event listeners:
    http://docs.sqlalchemy.org/en/latest/core/event.html
.. _fedmsg: http://www.fedmsg.com/
"""
from __future__ import unicode_literals, absolute_import

import logging

from sqlalchemy import event

from anitya.app import SESSION
from anitya.lib import model


_log = logging.getLogger(__name__)


@event.listens_for(SESSION, 'before_flush')
def set_version_types(session, flush_context, instances):
    """
    Set the correct type on ProjectVersion objects when their associated
    project is updated.

    See the SQLAlchemy `before_flush`_ documentation for full API details.

    .. _before_flush:
        http://docs.sqlalchemy.org/en/latest/orm/events.html\
                #sqlalchemy.orm.events.SessionEvents.before_flush

    Args:
        session (sqlalchemy.orm.session.Session): The session being flushed.
        flush_context (sqlalchemy.orm.session.UOWTransaction): Internal
            UOWTransaction object which handles the details of the flush.
        instances: Usually None, this is the collection of objects which can be
            passed to the Session.flush() method (note this usage is deprecated).
    """
    def set_version_type(obj):
        if isinstance(obj, model.Project):
            for version in obj.versions_obj:
                _log.debug('Updating %r version %r to %s', obj, version, obj.version_scheme)
                version.type = obj.version_scheme
                session.add(version)
    for obj in session.dirty:
        set_version_type(obj)
    for obj in session.new:
        set_version_type(obj)
