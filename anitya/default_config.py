# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

anitya default configuration.
"""

from datetime import timedelta
import os.path


# Set the time after which the session expires
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# Secret key used to generate the csrf token in the forms
SECRET_KEY = 'changeme please'

# URL to the database
DB_URL = 'sqlite:////var/tmp/anitya-dev.sqlite'

# List of admins based on their openid
ANITYA_WEB_ADMINS = [
    'http://ralph.id.fedoraproject.org/',
    'http://pingou.id.fedoraproject.org/',
    'http://oddshocks.id.fedoraproject.org/',
]

# Fedora OpenID endpoint
ANITYA_WEB_FEDORA_OPENID = 'https://id.fedoraproject.org'

# Booleans to activate or not OpenID providers
ANITYA_WEB_ALLOW_FAS_OPENID = True
ANITYA_WEB_ALLOW_GOOGLE_OPENID = True
ANITYA_WEB_ALLOW_YAHOO_OPENID = True
ANITYA_WEB_ALLOW_GENERIC_OPENID = True

ADMIN_EMAIL = 'admin@fedoraproject.org'

ANITYA_LOG_LEVEL = 'INFO'

# The SMTP server to send mail through
SMTP_SERVER = '127.0.0.1'

# Whether or not to send emails to MAIL_ADMIN via SMTP_SERVER when HTTP 500
# errors occur.
EMAIL_ERRORS = False

BLACKLISTED_USERS = []

# The location of the client_secrets.json file used for API authentication
OIDC_CLIENT_SECRETS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'client_secrets.json'
)

# Force the application to require HTTPS to save the cookie. This should only
# be `False` in a development environment running on the local host!
OIDC_ID_TOKEN_COOKIE_SECURE = True
OIDC_REQUIRE_VERIFIED_EMAIL = True
OIDC_OPENID_REALM = 'http://localhost:5000/oidc_callback'
OIDC_SCOPES = ['openid', 'email', 'profile', 'fedora']
