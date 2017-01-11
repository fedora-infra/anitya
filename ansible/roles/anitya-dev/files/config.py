# -*- coding: utf-8 -*-

# URL to the database
DB_URL = 'postgresql://postgres:anypasswordworkslocally@localhost/anitya'

# List of admins based on their openid
# ANITYA_WEB_ADMINS = ['http://<FAS>.id.fedoraproject.org/']

# Fedora OpenID endpoint
ANITYA_WEB_FEDORA_OPENID = 'https://id.fedoraproject.org'

# Booleans to activate or not OpenID providers
ANITYA_WEB_ALLOW_FAS_OPENID = True
ANITYA_WEB_ALLOW_GOOGLE_OPENID = True
ANITYA_WEB_ALLOW_YAHOO_OPENID = True
ANITYA_WEB_ALLOW_GENERIC_OPENID = True

ADMIN_EMAIL = 'admin@fedoraproject.org'

BLACKLISTED_USERS = []
