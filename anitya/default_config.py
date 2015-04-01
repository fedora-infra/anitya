#-*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

anitya default configuration.
"""

from datetime import timedelta

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
