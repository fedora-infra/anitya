# -*- coding: utf-8 -*-
#
# Copyright © 2018  Red Hat, Inc.
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
#

"""
anitya tests for GDPR SAR script.
"""

import pytest
import mock
import json

import anitya.sar as sar
from anitya.db import models
from anitya.tests.base import DatabaseTestCase


class SARTests(DatabaseTestCase):
    """SAR script tests."""

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        """Use capsys fixture as part of this class."""
        self.capsys = capsys

    @mock.patch.dict("os.environ", {"SAR_EMAIL": "user@fedoraproject.org"})
    def test_main_email(self):
        """
        Assert that correct user data are dumped when providing
        e-mail.
        """
        user = models.User(email="user@fedoraproject.org", username="user", active=True)

        self.session.add(user)

        user2 = models.User(email="user2@email.org", username="user2", active=True)

        self.session.add(user2)
        self.session.commit()

        exp = [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "active": user.active,
                "user_social_auths": [],
            }
        ]

        sar.main()

        out, err = self.capsys.readouterr()

        obs = json.loads(out)

        self.assertEqual(exp, obs)

    @mock.patch.dict("os.environ", {"SAR_USERNAME": "user"})
    def test_main_username(self):
        """
        Assert that correct user data are dumped when providing
        username.
        """
        user = models.User(email="user@fedoraproject.org", username="user", active=True)

        self.session.add(user)

        user2 = models.User(email="user2@email.org", username="user2", active=True)

        self.session.add(user2)
        self.session.commit()

        exp = [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "active": user.active,
                "user_social_auths": [],
            }
        ]

        sar.main()

        out, err = self.capsys.readouterr()

        obs = json.loads(out)

        self.assertEqual(exp, obs)

    def test_main_no_env_set(self):
        """
        Assert that correct user data are dumped when nothing is provided.
        """
        user = models.User(email="user@fedoraproject.org", username="user", active=True)

        self.session.add(user)

        user2 = models.User(email="user2@email.org", username="user2", active=True)

        self.session.add(user2)
        self.session.commit()

        sar.main()

        out, err = self.capsys.readouterr()

        self.assertEqual("[]", out)
