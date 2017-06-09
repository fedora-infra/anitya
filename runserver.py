#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" The flask application """

import argparse
import os

from anitya.app import APP


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
parser.add_argument(
    '--host', default='127.0.0.1',
    help='IP address for the flask application to bind to.'
)

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


APP.debug = True
APP.run(port=int(args.port), host=args.host)
