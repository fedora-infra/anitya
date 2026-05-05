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
"""

from sqlalchemy import func, select
from sqlalchemy_helpers.flask_ext import DatabaseExtension

# Integrate sqlalchemy_helpers
db = DatabaseExtension()


def paginate(query, page=1, items_per_page=25) -> dict:
    """
    Retrieve a page of items.

    Args:
        page (int): the page number to retrieve. This page is 1-indexed and
                    defaults to 1.
        items_per_page (int): The number of items per page. This defaults
                              to 25.

    Returns:
        Page: A dict with result.

    Raises:
        ValueError: If the page or items_per_page values are less than 1.
    """

    if page < 1:
        raise ValueError("page must be 1 or greater.")
    if items_per_page < 1:
        raise ValueError("items_per_page must be 1 or greater.")

    total_items = db.session.scalar(select(func.count()).select_from(query.subquery()))
    paginated_query = query.limit(items_per_page).offset(items_per_page * (page - 1))
    items = db.session.execute(paginated_query).scalars().all()
    return {
        "items": items,
        "page": page,
        "total_items": total_items,
        "items_per_page": items_per_page,
    }
