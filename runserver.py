#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" The flask application """

## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import argparse
import sys
import os


parser = argparse.ArgumentParser(
    description='Run the anitya app')
parser.add_argument(
    '--config', '-c', dest='config',
    help='Configuration file to use for anitya.')
parser.add_argument(
    '--debug', dest='debug', action='store_true',
    default=False,
    help='Expand the level of data returned.')
parser.add_argument(
    '--profile', dest='profile', action='store_true',
    default=False,
    help='Profile the anitya application.')
parser.add_argument(
    '--port', '-p', default=5000,
    help='Port for the flask application.')

args = parser.parse_args()


if args.profile:
    from werkzeug.contrib.profiler import ProfilerMiddleware
    APP.config['PROFILE'] = True
    APP.wsgi_app = ProfilerMiddleware(APP.wsgi_app, restrictions=[30])


if args.config:
    config = args.config
    if not config.startswith('/'):
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        config = os.path.join(here, config)
    os.environ['ANITYA_WEB_CONFIG'] = config


from anitya.app import APP
APP.debug = True
APP.run(port=int(args.port))
