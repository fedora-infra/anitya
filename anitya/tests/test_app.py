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

from sqlalchemy.exc import UnboundExecutionError

from anitya import app
from anitya.config import config as anitya_config
from anitya.lib.model import Session


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

        app.create({'DB_URL': 'sqlite://'})
        self.assertEqual('sqlite://', str(Session().get_bind().url))
