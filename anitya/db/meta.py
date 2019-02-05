# -*- coding: utf-8 -*-
# This file is a part of the Anitya project.
#
# Copyright © 2018 Red Hat, Inc.
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
This module sets up the basic database objects that all our other modules will
rely on. This includes the declarative base class and global scoped session.

This is in its own module to avoid circular imports from forming. Models and
events need to be imported by ``__init__.py``, but  they also need access to
the :class:`Base` model and :class:`Session`.
"""
from __future__ import unicode_literals

import collections

from sqlalchemy import create_engine, event
from sqlalchemy.ext import declarative
from sqlalchemy.orm import sessionmaker, scoped_session, query as sa_query


#: This is a configured scoped session. It creates thread-local sessions. This
#: means that ``Session() is Session()`` is ``True``. This is a convenient way
#: to avoid passing a session instance around. Consult SQLAlchemy's documentation
#: for details.
#:
#: Before you can use this, you must call :func:`initialize`.
Session = scoped_session(sessionmaker())


def initialize(config):
    """
    Initialize the database.

    This creates a database engine from the provided configuration and
    configures the scoped session to use the engine.

    Args:
        config (dict): A dictionary that contains the configuration necessary
            to initialize the database.

    Returns:
        sqlalchemy.engine: The database engine created from the configuration.
    """
    #: The SQLAlchemy database engine. This is constructed using the value of
    #: ``DB_URL`` in :mod:`anitya.config``.
    engine = create_engine(config["DB_URL"], echo=config.get("SQL_DEBUG", False))
    # Source: https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#foreign-key-support
    if config["DB_URL"].startswith("sqlite:"):
        event.listen(
            engine,
            "connect",
            lambda db_con, con_record: db_con.execute("PRAGMA foreign_keys=ON"),
        )
    Session.configure(bind=engine)
    return engine


_Page = collections.namedtuple(
    "_Page", ("items", "page", "items_per_page", "total_items")
)


class Page(_Page):
    """
    A sub-class of namedtuple that represents a page.

    Attributes:
        items (object): The database objects from the query.
        page (int): The page number used for the query.
        items_per_page (int): The number of items per page.
        total_items (int): The total number of items in the database.
    """

    def as_dict(self):
        """
        Return a dictionary representing the page.

        Returns:
            dict: A dictionary representation of the page and its items, using
                the ``__json__`` method defined on the item objects.
        """
        return {
            "items": [item.__json__() for item in self.items],
            "page": self.page,
            "items_per_page": self.items_per_page,
            "total_items": self.total_items,
        }


class BaseQuery(sa_query.Query):
    """A base Query object that provides queries."""

    def paginate(self, page=None, items_per_page=None, order_by=None):
        """
        Retrieve a page of items.

        Args:
            page (int): the page number to retrieve. This page is 1-indexed and
                        defaults to 1.
            items_per_page (int): The number of items per page. This defaults
                                  to 25.
            order_by (sa.Column or tuple): One or more criterion by which to order
                                           the pages.

        Returns:
            Page: A namedtuple of the items.

        Raises:
            ValueError: If the page or items_per_page values are less than 1.
        """

        if page is None:
            page = 1
        if items_per_page is None:
            items_per_page = 25

        if page < 1:
            raise ValueError("page must be 1 or greater.")
        if items_per_page < 1:
            raise ValueError("items_per_page must be 1 or greater.")

        if not isinstance(order_by, tuple):
            order_by = (order_by,)

        q = self.order_by(*order_by)
        total_items = q.count()
        items = q.limit(items_per_page).offset(items_per_page * (page - 1)).all()
        return Page(
            items=items,
            page=page,
            total_items=total_items,
            items_per_page=items_per_page,
        )


class _AnityaBase(object):
    """
    Base class for the SQLAlchemy model base class.

    Attributes:
        query (sqlalchemy.orm.query.Query): a class property which produces a
            :class:`BaseQuery` object against the class and the current Session
            when called. Classes that want a customized Query class should
            sub-class :class:`BaseQuery` and explicitly set the query property
            on the model.
    """

    query = Session.query_property(query_cls=BaseQuery)


#: The SQLAlchemy declarative base class all models must sub-class.
Base = declarative.declarative_base(cls=_AnityaBase)
metadata = Base.metadata
