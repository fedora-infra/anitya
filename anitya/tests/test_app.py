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
"""Tests for the :mod:`anitya.app` module."""

import logging
import unittest

from social_flask_sqlalchemy import models as social_models
from sqlalchemy.exc import UnboundExecutionError, IntegrityError

from anitya import app
from anitya.config import config as anitya_config
from anitya.db import Session, models
from anitya.tests import base


class CreateTests(unittest.TestCase):
    """Tests for the :func:`anitya.app.create` function."""

    def setUp(self):
        # Make sure each test starts with a clean session
        Session.remove()
        Session.configure(bind=None)

    def test_default_config(self):
        """Assert when no configuration is provided, :data:`anitya.config.config` is used."""
        application = app.create()
        for key in anitya_config:
            self.assertEqual(anitya_config[key], application.config[key])

    def test_email_config(self):
        """Assert a SMTPHandler is added to the anitya logger when ``EMAIL_ERRORS=True``."""
        config = {
            'DB_URL': 'sqlite://',
            'SOCIAL_AUTH_USER_MODEL': 'anitya.db.models.User',
            'EMAIL_ERRORS': True,
            'SMTP_SERVER': 'smtp.example.com',
            'ADMIN_EMAIL': 'admin@example.com',
        }
        anitya_logger = logging.getLogger('anitya')
        anitya_logger.handlers = []

        app.create(config)

        self.assertEqual(1, len(anitya_logger.handlers))
        self.assertEqual('smtp.example.com', anitya_logger.handlers[0].mailhost)
        self.assertEqual(['admin@example.com'], anitya_logger.handlers[0].toaddrs)

    def test_db_config(self):
        """Assert creating the application configures the scoped session."""
        # Assert the scoped session is not bound.
        self.assertRaises(UnboundExecutionError, Session.get_bind)
        Session.remove()

        app.create({
            'DB_URL': 'sqlite://',
            'SOCIAL_AUTH_USER_MODEL': 'anitya.db.models.User',
        })
        self.assertEqual('sqlite://', str(Session().get_bind().url))


class IntegrityErrorHandlerTests(base.DatabaseTestCase):

    def setUp(self):
        super(IntegrityErrorHandlerTests, self).setUp()
        session = Session()
        user = models.User(email='user@example.com', username='user')
        social_auth_user = social_models.UserSocialAuth(provider='Demo Provider', user=user)
        session.add(social_auth_user)
        session.add(user)
        session.commit()

    def test_not_email(self):
        """Assert an IntegrityError without the email key results in a 500 error"""
        err = IntegrityError('SQL Statement', {}, None)

        msg, errno = app.integrity_error_handler(err)

        self.assertEqual(500, errno)
        self.assertEqual('The server encountered an unexpected error', msg)

    def test_email(self):
        """Assert an HTTP 400 is generated from an email IntegrityError."""

        err = IntegrityError('SQL Statement', {'email': 'user@example.com'}, None)
        expected_msg = ("Error: There's already an account associated with your email, "
                        "authenticate with Demo Provider.")

        msg, errno = app.integrity_error_handler(err)

        self.assertEqual(400, errno)
        self.assertEqual(expected_msg, msg)
