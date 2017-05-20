#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anitya.app import APP
import anitya.lib

anitya.lib.init(
    APP.config['DB_URL'],
    None,
    debug=True,
    create=True)
