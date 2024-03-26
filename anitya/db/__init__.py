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
This package contains all the database-related code, including SQLAlchemy models,
Alembic migrations, and a scoped session object configured from :mod:`anitya.config`
"""

# You need to import the events to register them with application
# If they are not imported, there wouldn't be triggered
from . import events  # noqa: F401
from .meta import Base, BaseQuery, Page, Session, initialize  # noqa: F401
from .models import Project  # noqa: F401
from .models import (  # noqa: F401
    ApiToken,
    Distro,
    Packages,
    ProjectFlag,
    ProjectVersion,
    Run,
    User,
)
