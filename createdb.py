#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from argparse import ArgumentParser
from pathlib import Path

from alembic import command
from alembic.config import Config
from social_flask_sqlalchemy import models as social_models

from anitya.app import create
from anitya.config import load
from anitya.db import Base, Session

parser = ArgumentParser()

script_dir = Path(__file__).parent.absolute()

parser.add_argument("--debug", action="store_true", default=False, dest="verbose")
parser.add_argument("--alembic-config", default=None)
parser.add_argument(
    "--db-uri",
    default=None,
    help="This will override the URLs specified in alembic and anitya",
)

args = parser.parse_args()

alembic_config = args.alembic_config
anitya_config = load()

anitya_config["SQL_DEBUG"] = args.verbose

if args.db_uri:
    anitya_config["DB_URL"] = args.db_uri

# An app object is required for social_auth tables to be created properly
anitya_app = create(config=anitya_config)
engine = Session.get_bind()

Base.metadata.create_all(engine)

# This call depends on app.create calling init_social which defines
# necessary column information in the social_auth_usersocialauth table
social_models.PSABase.metadata.create_all(engine)

# Set the alembic_version based on the current migrations available.
# This presupposes the models haven't changed outside of a migration.
#
# Default to the side-by-side alembic.ini.
if alembic_config is None:
    alembic_config = os.path.join(script_dir, "alembic.ini")
    if args.verbose and os.path.isfile(alembic_config):
        print("No alembic config specified, defaulting to: {}".format(alembic_config))

if alembic_config and os.path.isfile(alembic_config):
    alembic_cfg = Config(alembic_config)
    alembic_cfg.set_main_option("sqlalchemy.url", anitya_config["DB_URL"])
    command.stamp(alembic_cfg, "head")
