#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anitya.config import config
from anitya.lib import utilities

utilities.init(
    config['DB_URL'],
    None,
    debug=True,
    create=True)
