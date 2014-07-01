#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" The flask application """

## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from anitya.app import APP

if __name__ == '__main__':
    APP.debug = True
    APP.run()
