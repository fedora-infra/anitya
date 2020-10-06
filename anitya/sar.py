#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2018  Red Hat, Inc.
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
This script is used for GDPR SAR (General Data Protection Regulation
Subject Access Requests).
It returns information about specific user saved by Anitya.
It reads SAR_USERNAME and SAR_EMAIL environment variables as keys for
getting data from database.

 Authors:
   Michal Konecny <mkonecny@redhat.com>
"""

import logging
import os
import json
import sys

from anitya.config import config
from anitya import db

_log = logging.getLogger("anitya")


def main():
    """
    Retrieve database entry for user.
    """
    db.initialize(config)
    sar_username = os.getenv("SAR_USERNAME")
    sar_email = os.getenv("SAR_EMAIL")

    users = []

    if sar_email:
        _log.debug("Find users by e-mail {}".format(sar_email))
        users = users + db.User.query.filter_by(email=sar_email).all()

    if sar_username:
        _log.debug("Find users by username {}".format(sar_username))
        users = users + db.User.query.filter_by(username=sar_username).all()

    users_list = []
    for user in users:
        user_dict = user.to_dict()
        user_social_auths = db.Session.execute(
            "SELECT provider,extra_data,uid FROM social_auth_usersocialauth WHERE user_id = :val",
            {"val": str(user.id)},
        )
        user_dict["user_social_auths"] = []
        # This part is working in postgresql, but in tests we are using sqlite
        # which doesn't know the UUID type
        for user_social_auth in user_social_auths:  # pragma: no cover
            user_dict["user_social_auths"].append(
                {
                    "provider": user_social_auth["provider"],
                    "extra_data": user_social_auth["extra_data"],
                    "uid": user_social_auth["uid"],
                }
            )
        users_list.append(user_dict)

    json.dump(users_list, sys.stdout)


if __name__ == "__main__":
    _log.debug("SAR script start")
    main()
    _log.debug("SAR script end")
