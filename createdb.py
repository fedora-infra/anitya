#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anitya.app import APP
from anitya.lib import utilities

utilities.init(
    APP.config['DB_URL'],
    None,
    debug=True,
    create=True)
