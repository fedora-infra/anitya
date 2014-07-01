#!/usr/bin/env python
#-*- coding: utf-8 -*-

## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from anitya.app import APP
import anitya.lib

anitya.lib.init(
    APP.config['DB_URL'],
    None,
    debug=True,
    create=True)
