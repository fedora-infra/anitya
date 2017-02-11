# This file is part of the Anitya project.
#
# Copyright (C) 2017  Red Hat, Inc.
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
Handles compatibility imports for Anitya.
"""
from __future__ import absolute_import, unicode_literals


# flask_wtf.Form was renamed to flask_wtf.FlaskForm
# flask_wtf.Form will be removed in flask_wtf-1.0.
try:
    from flask_wtf import FlaskForm
except ImportError:
    from flask_wtf import Form as FlaskForm  # NOQA
