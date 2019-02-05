# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
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
This module provides functions and classes for authentication and authorization.

Anitya uses `Flask-Login`_ for user session management. It handles logging in,
logging out, and remembering users’ sessions over extended periods of time.

In addition, Anitya uses `Python Social Auth`_ to authenticate users from various
third-party identity providers. It handles logging the user in and creating
:class:`anitya.db.models.User` objects as necessary.

.. _Flask-Login: https://flask-login.readthedocs.io/en/latest/
.. _Python Social Auth:
    https://python-social-auth.readthedocs.io/en/latest/
"""
from functools import wraps
import logging
import uuid

import flask_login
from sqlalchemy.orm.exc import NoResultFound

from anitya.db import User, ApiToken


_log = logging.getLogger(__name__)


def load_user_from_session(user_id):
    """
    Used to reload a :class:`User` object from the session.

    This implements the interface required by :meth:`flask_login.LoginManager.user_loader`.

    Args:
        user_id (str): The user's ID as a unicode string.

    Returns:
        User: The user with the given user ID, if it exists. Otherwise, ``None`` is returned.
    """
    try:
        user = User.query.get(uuid.UUID(user_id))
        _log.debug('Successfully loaded user "%s" from cookie session', user_id)
        return user
    except (TypeError, ValueError) as e:
        # Return None if the type was wrong
        _log.debug('Failed to load user "%s" from cookie session: %r', user_id, e)


def load_user_from_request(request):
    """
    Load a user from a Flask request by examining the ``Authorization`` header.

    This implements the interface required by :meth:`flask_login.LoginManager.request_loader`.

    Args:
        request (flask.Request): The request object to load a user from.

    Returns:
        User: The user associated with the API token, if it exists. Otherwise
            ``None`` is returned.
    """
    api_key = request.headers.get("Authorization")
    if api_key:
        _log.debug(
            'Attempting to authenticate via user-provided "Authorization" header'
        )
        try:
            key_type, key_value = api_key.split()
        except ValueError:
            return
        if key_type.lower() == "token":
            try:
                api_token = ApiToken.query.filter_by(token=key_value).one()
                _log.debug(
                    'Successfully authenticated user "%s" via API token',
                    api_token.user.id,
                )
                return api_token.user
            except NoResultFound:
                _log.debug("Failed to authenticate user via API token")
                return


def require_token(f):
    """
    A decorator for API functions that enforces authentication.

    This differs from :func:`flask_login.login_required` in that it will return
    an HTTP 401 with JSON rather than redirecting the user to the login view.

    Args:
        f (callable): The function to require an authenticated user for.

    Returns:
        callable: A callable that aborts with an HTTP 401 if the current user is
            not authenticated.
    """

    @wraps(f)
    def _authenticated_api_access(*args, **kwds):
        if not flask_login.current_user.is_authenticated:
            error_details = {
                "error": "authentication_required",
                "error_description": "Authentication is required to access this API.",
            }
            return (error_details, 401, {"WWW-Authenticate": "Token"})
        else:
            return f(*args, **kwds)

    return _authenticated_api_access
