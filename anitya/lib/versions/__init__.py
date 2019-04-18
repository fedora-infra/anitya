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
This package defines a set of version scheme plugins.

Anitya attempts to determine the newest version for a project. To do this, it
must be able to both parse and compare all the major version schemes, and handle
unknown version schemes in a reasonable way.

The general approach is as follows:

1. If a project has its ``version_scheme`` column defined in the database, that
   version scheme is used.

2. If the project does not have ``version_scheme`` set, but is in an ecosystem
   with a default version scheme, the ecosystem default is used.

2. If the project is not a part of an ecosystem or if the ecosystem has no
   default scheme, but the backend it uses has a default version scheme defined,
   the backend default is used.

4. If all else fails, Anitya uses the value of :data:`GLOBAL_DEFAULT`.
"""
from __future__ import unicode_literals

from .base import Version, v_prefix  # noqa: F401
from .rpm import RpmVersion  # noqa: F401
from .calver import CalendarVersion  # noqa: F401
from .semver import SemanticVersion  # noqa: F401


#: The default version scheme to use when the project itself, its ecosystem,
#: and its backend all have no version scheme set.
GLOBAL_DEFAULT = "RPM"
