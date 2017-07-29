# -*- coding: utf-8 -*-
#
# Copyright © 2017  Red Hat, Inc.
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
"""This module is responsible for loading the application configuration."""

from datetime import timedelta
import logging
import logging.config
import os

import pytoml


_log = logging.getLogger(__name__)


#: A dictionary of application configuration defaults.
DEFAULTS = dict(
    # Set the time after which the session expires
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=3600),
    # Secret key used to generate the csrf token in the forms
    SECRET_KEY='changeme please',
    # URL to the database
    DB_URL='sqlite:////var/tmp/anitya-dev.sqlite',
    # List of admins based on their openid
    ANITYA_WEB_ADMINS=[],
    ANITYA_WEB_FEDORA_OPENID='https://id.fedoraproject.org',
    ANITYA_WEB_ALLOW_FAS_OPENID=True,
    ANITYA_WEB_ALLOW_GOOGLE_OPENID=True,
    ANITYA_WEB_ALLOW_YAHOO_OPENID=True,
    ANITYA_WEB_ALLOW_GENERIC_OPENID=True,
    ADMIN_EMAIL='admin@fedoraproject.org',
    ANITYA_LOG_CONFIG={
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[%(name)s %(levelname)s] %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout',
            }
        },
        'loggers': {
            'anitya': {
                'level': 'INFO',
                'propagate': False,
                'handlers': ['console'],
            },
        },
        # The root logger configuration; this is a catch-all configuration
        # that applies to all log messages not handled by a different logger
        'root': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    },
    # The SMTP server to send mail through
    SMTP_SERVER='127.0.0.1',
    # Whether or not to send emails to MAIL_ADMIN via SMTP_SERVER when HTTP 500
    # errors occur.
    EMAIL_ERRORS=False,
    BLACKLISTED_USERS=[],
    OIDC_CLIENT_SECRETS=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'client_secrets.json'
    ),
    GITHUB_ACCESS_TOKEN=None,
    # Force the application to require HTTPS to save the cookie. This should only
    # be `False` in a development environment running on the local host!
    OIDC_ID_TOKEN_COOKIE_SECURE=True,
    OIDC_REQUIRE_VERIFIED_EMAIL=True,
    OIDC_OPENID_REALM='http://localhost:5000/oidc_callback',
    OIDC_SCOPES=[
        'https://release-monitoring.org/oidc/upstream',
        'https://release-monitoring.org/oidc/downstream',
    ],
)

# Start with a basic logging configuration, which will be replaced by any user-
# specified logging configuration when the configuration is loaded.
logging.config.dictConfig(DEFAULTS['ANITYA_LOG_CONFIG'])


def load():
    """
    Load application configuration from a file and merge it with the default
    configuration.

    If the ``ANITYA_WEB_CONFIG`` environment variable is set to a filesystem
    path, the configuration will be loaded from that location. Otherwise, the
    path defaults to ``/etc/anitya/anitya.toml``.
    """
    config = DEFAULTS.copy()

    if 'ANITYA_WEB_CONFIG' in os.environ:
        config_path = os.environ['ANITYA_WEB_CONFIG']
    else:
        config_path = '/etc/anitya/anitya.toml'

    if os.path.exists(config_path):
        _log.info('Loading Anitya configuration from {}'.format(config_path))
        with open(config_path) as fd:
            try:
                file_config = pytoml.loads(fd.read())
                for key in file_config:
                    config[key.upper()] = file_config[key]
            except pytoml.core.TomlError as e:
                _log.error('Failed to parse {}: {}'.format(config_path, str(e)))
    else:
        _log.info('The Anitya configuration file, {}, does not exist.'.format(config_path))

    if not isinstance(config['PERMANENT_SESSION_LIFETIME'], timedelta):
        config['PERMANENT_SESSION_LIFETIME'] = timedelta(
            seconds=config['PERMANENT_SESSION_LIFETIME'])

    if config['SECRET_KEY'] == DEFAULTS['SECRET_KEY']:
        _log.warning('SECRET_KEY is not configured, falling back to the default. '
                     'This is NOT safe for production deployments!')
    return config


#: The application configuration dictionary.
config = load()

# With the full configuration loaded, we can now configure logging properly.
logging.config.dictConfig(config['ANITYA_LOG_CONFIG'])
