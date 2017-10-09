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
"""Tests for the :mod:`anitya.config` module."""
from __future__ import unicode_literals

from datetime import timedelta
import unittest

import mock

from anitya import config as anitya_config

full_config = """
secret_key = "very_secret"
permanent_session_lifetime = 3600
db_url = "sqlite:////var/tmp/anitya-dev.sqlite"
anitya_web_admins = ["http://pingou.id.fedoraproject.org"]
admin_email = "admin@fedoraproject.org"
smtp_server = "smtp.example.com"
email_errors = false
blacklisted_users = ["http://sometroublemaker.id.fedoraproject.org"]

social_auth_authentication_backends = [
    "social_core.backends.fedora.FedoraOpenId",
    "social_core.backends.yahoo.YahooOpenId",
    "social_core.backends.open_id.OpenIdAuth",
    "social_core.backends.google_openidconnect.GoogleOpenIdConnect",
    "social_core.backends.github.GithubOAuth2",
]
# Force the application to require HTTPS on authentication redirects.
social_auth_redirect_is_https = true
social_auth_login_url = "/login/"
social_auth_login_redirect_url = "/"
social_auth_login_error_url = "/login-error/"

[anitya_log_config]
    version = 1
    disable_existing_loggers = true

    [anitya_log_config.formatters]
        [anitya_log_config.formatters.simple]
            format = "[%(name)s %(levelname)s] %(message)s"

    [anitya_log_config.handlers]
        [anitya_log_config.handlers.console]
            class = "logging.StreamHandler"
            formatter = "simple"
            stream = "ext://sys.stdout"

    [anitya_log_config.loggers]
        [anitya_log_config.loggers.anitya]
            level = "WARNING"
            propagate = false
            handlers = ["console"]

    [anitya_log_config.root]
        level = "ERROR"
        handlers = ["console"]
"""

empty_config = '# secret_key = "muchsecretverysafe"'
partial_config = 'secret_key = "muchsecretverysafe"'


class LoadTests(unittest.TestCase):
    """Unit tests for the :func:`anitya.config.load` function."""

    maxDiff = None

    @mock.patch('anitya.config.open', mock.mock_open(read_data='Ni!'))
    @mock.patch('anitya.config._log', autospec=True)
    @mock.patch('anitya.config.os.path.exists', return_value=True)
    def test_bad_config_file(self, mock_exists, mock_log):
        config = anitya_config.load()
        self.assertEqual(anitya_config.DEFAULTS, config)
        mock_exists.assert_called_once_with('/etc/anitya/anitya.toml')
        mock_log.info.assert_called_once_with(
            'Loading Anitya configuration from /etc/anitya/anitya.toml')
        error = 'Failed to parse /etc/anitya/anitya.toml: <string>(1, 1): msg'
        self.assertEqual(error, mock_log.error.call_args_list[0][0][0])

    @mock.patch('anitya.config.open', mock.mock_open(read_data=partial_config))
    @mock.patch('anitya.config._log', autospec=True)
    @mock.patch('anitya.config.os.path.exists', return_value=True)
    def test_partial_config_file(self, mock_exists, mock_log):
        config = anitya_config.load()
        self.assertNotEqual('muchsecretverysafe', anitya_config.DEFAULTS['SECRET_KEY'])
        self.assertEqual('muchsecretverysafe', config['SECRET_KEY'])
        mock_exists.assert_called_once_with('/etc/anitya/anitya.toml')
        mock_log.info.assert_called_once_with(
            'Loading Anitya configuration from /etc/anitya/anitya.toml')
        self.assertEqual(0, mock_log.warning.call_count)

    @mock.patch('anitya.config.open', mock.mock_open(read_data=full_config))
    @mock.patch('anitya.config._log', autospec=True)
    @mock.patch('anitya.config.os.path.exists', return_value=True)
    def test_full_config_file(self, mock_exists, mock_log):
        expected_config = {
            'SECRET_KEY': 'very_secret',
            'PERMANENT_SESSION_LIFETIME': timedelta(seconds=3600),
            'DB_URL': 'sqlite:////var/tmp/anitya-dev.sqlite',
            'ANITYA_WEB_ADMINS': ['http://pingou.id.fedoraproject.org'],
            'ADMIN_EMAIL': 'admin@fedoraproject.org',
            'ANITYA_LOG_CONFIG': {
                'version': 1,
                'disable_existing_loggers': True,
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
                        'level': 'WARNING',
                        'propagate': False,
                        'handlers': ['console'],
                    },
                },
                'root': {
                    'level': 'ERROR',
                    'handlers': ['console'],
                },
            },
            'SMTP_SERVER': 'smtp.example.com',
            'EMAIL_ERRORS': False,
            'BLACKLISTED_USERS': ['http://sometroublemaker.id.fedoraproject.org'],
            'SESSION_PROTECTION': 'strong',
            'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': [
                'social_core.backends.fedora.FedoraOpenId',
                'social_core.backends.yahoo.YahooOpenId',
                'social_core.backends.open_id.OpenIdAuth',
                'social_core.backends.google_openidconnect.GoogleOpenIdConnect',
                'social_core.backends.github.GithubOAuth2',
            ],
            'SOCIAL_AUTH_STORAGE': 'social_flask_sqlalchemy.models.FlaskStorage',
            'SOCIAL_AUTH_USER_MODEL': 'anitya.lib.model.User',
            # Force the application to require HTTPS on authentication redirects.
            'SOCIAL_AUTH_REDIRECT_IS_HTTPS': True,
            'SOCIAL_AUTH_LOGIN_URL': '/login/',
            'SOCIAL_AUTH_LOGIN_REDIRECT_URL': '/',
            'SOCIAL_AUTH_LOGIN_ERROR_URL': '/login-error/',
        }
        config = anitya_config.load()
        self.assertEqual(sorted(expected_config.keys()), sorted(config.keys()))
        for key in expected_config:
            self.assertEqual(expected_config[key], config[key])
        mock_exists.assert_called_once_with('/etc/anitya/anitya.toml')
        mock_log.info.assert_called_once_with(
            'Loading Anitya configuration from /etc/anitya/anitya.toml')
        self.assertEqual(0, mock_log.warning.call_count)

    @mock.patch('anitya.config.open', mock.mock_open(read_data=partial_config))
    @mock.patch.dict('anitya.config.os.environ', {'ANITYA_WEB_CONFIG': '/my/config'})
    @mock.patch('anitya.config._log', autospec=True)
    @mock.patch('anitya.config.os.path.exists', return_value=True)
    def test_custom_config_file(self, mock_exists, mock_log):
        config = anitya_config.load()
        self.assertNotEqual('muchsecretverysafe', anitya_config.DEFAULTS['SECRET_KEY'])
        self.assertEqual('muchsecretverysafe', config['SECRET_KEY'])
        mock_exists.assert_called_once_with('/my/config')
        mock_log.info.assert_called_once_with(
            'Loading Anitya configuration from /my/config')
        self.assertEqual(0, mock_log.warning.call_count)

    @mock.patch('anitya.config.open', mock.mock_open(read_data=empty_config))
    @mock.patch('anitya.config._log', autospec=True)
    @mock.patch('anitya.config.os.path.exists', return_value=True)
    def test_empty_config_file(self, mock_exists, mock_log):
        """Assert loading the config with an empty file that exists works."""
        config = anitya_config.load()
        self.assertEqual(anitya_config.DEFAULTS, config)
        mock_exists.assert_called_once_with('/etc/anitya/anitya.toml')
        mock_log.info.assert_called_once_with(
            'Loading Anitya configuration from /etc/anitya/anitya.toml')
        mock_log.warning.assert_called_once_with(
            'SECRET_KEY is not configured, falling back to the default. '
            'This is NOT safe for production deployments!')

    @mock.patch('anitya.config._log', autospec=True)
    @mock.patch('anitya.config.os.path.exists', return_value=False)
    def test_missing_config_file(self, mock_exists, mock_log):
        """Assert loading the config with a missing file works."""
        config = anitya_config.load()
        self.assertEqual(anitya_config.DEFAULTS, config)
        mock_exists.assert_called_once_with('/etc/anitya/anitya.toml')
        mock_log.info.assert_called_once_with(
            'The Anitya configuration file, /etc/anitya/anitya.toml, does not exist.')
        mock_log.warning.assert_called_once_with(
            'SECRET_KEY is not configured, falling back to the default. '
            'This is NOT safe for production deployments!')


if __name__ == '__main__':
    unittest.main(verbosity=2)
