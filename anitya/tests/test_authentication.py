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
"""Tests for the :mod:`anitya.authentication` module."""

import uuid

import six
import mock

from social_flask_sqlalchemy import models as social_models

from anitya import authentication
from anitya.db import Session, ApiToken, models
from anitya.tests.base import DatabaseTestCase


class LoadUserFromRequestTests(DatabaseTestCase):
    """Tests for the :class:`anitya.authentication.SessionInterface`` class."""

    def setUp(self):
        super(LoadUserFromRequestTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)

        self.api_token = ApiToken(user=self.user)
        session.add(self.api_token)
        session.commit()

    def test_success(self):
        """Assert that users can authenticate via the 'Authorization' header."""
        mock_request = mock.Mock()
        mock_request.headers = {"Authorization": "token " + self.api_token.token}
        user = authentication.load_user_from_request(mock_request)
        self.assertEqual(self.user, user)

    def test_no_token_in_db(self):
        """Assert that an invalid token results in a User of ``None``."""
        mock_request = mock.Mock()
        mock_request.headers = {"Authorization": "token " "myinvalidtoken"}
        self.assertEqual(None, authentication.load_user_from_request(mock_request))

    def test_no_header(self):
        """Assert that no user is authenticated when the header is absent."""
        mock_request = mock.Mock()
        mock_request.headers = {}
        self.assertEqual(None, authentication.load_user_from_request(mock_request))

    def test_unkown_auth_type(self):
        """Assert that unknown authentication types are rejected."""
        mock_request = mock.Mock(spec="werkzeug.wrappers.Request")
        mock_request.headers = {"Authorization": "Basic " + self.api_token.token}
        self.assertEqual(None, authentication.load_user_from_request(mock_request))


class LoadUserFromSessionTests(DatabaseTestCase):
    """Tests for the :func:`anitya.authentication.load_user_from_session`` functions."""

    def setUp(self):
        super(LoadUserFromSessionTests, self).setUp()

        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        session.commit()

    def test_success(self):
        """Assert users are loaded successfully when a valid ID is provided."""
        loaded_user = authentication.load_user_from_session(six.text_type(self.user.id))
        self.assertEqual(loaded_user, self.user)

    def test_missing_user(self):
        """Assert ``None`` is returned when there is no user with the given ID."""
        loaded_user = authentication.load_user_from_session(six.text_type(uuid.uuid4()))
        self.assertTrue(loaded_user is None)

    def test_incorrect_type(self):
        """Assert ``None`` is returned when the user ID isn't a UUID."""
        loaded_user = authentication.load_user_from_session("Not a UUID")
        self.assertTrue(loaded_user is None)


class RequireTokenTests(DatabaseTestCase):
    """Tests for the :func:`anitya.authentication.require_token` decorator."""

    def setUp(self):
        super(RequireTokenTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = Session()
        self.user = models.User(email="user@fedoraproject.org", username="user")
        user_social_auth = social_models.UserSocialAuth(
            user_id=self.user.id, user=self.user
        )

        session.add(self.user)
        session.add(user_social_auth)
        self.api_token = ApiToken(user=self.user)
        session.add(self.api_token)
        session.commit()

    @mock.patch("flask_login.current_user")
    def test_unauthenticated(self, mock_current_user):
        """Assert decorated functions return HTTP 401 when no user is logged in."""
        mock_current_user.is_authenticated = False
        error_details = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this API.",
        }
        expected_response = (error_details, 401, {"WWW-Authenticate": "Token"})

        @authentication.require_token
        def test_func():
            return "This should not happen!"

        self.assertEqual(expected_response, test_func())

    @mock.patch("flask_login.current_user")
    def test_authenticated(self, mock_current_user):
        """Assert decorated functions return the function's result when a user is logged in."""
        mock_current_user.is_authenticated = True

        @authentication.require_token
        def test_func():
            return "Carry on!"

        self.assertEqual("Carry on!", test_func())
