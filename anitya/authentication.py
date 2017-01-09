# -*- coding: utf-8 -*-

"""
Helper for configuring OpenID and OpenID Connect based authentication,
as well as a dummy helper for running with only anonymous API access
configured
"""
from functools import wraps
import json

import flask
from flask.ext.openid import OpenID
from flask_oidc import OpenIDConnect

import mock

APP = None

def configure_openid(app):
    """Set up OpenID, OpenIDConnect, and the module's Flask app reference"""
    global APP
    app.oid = OpenID(app)
    try:
        app.oidc = OpenIDConnect(app, credentials_store=flask.session)
    except Exception as exc:
        # Handle running with only anonymous API access enabled
        app.logger.debug(str(exc))
        app.oidc = None
    APP = app

##################################################################
# Decorator for APIs that parse API tokens, but don't require them
##################################################################
def parse_api_token(f):
    """Make OIDC token information available, but allow anonymous access"""
    if APP.oidc is not None:
        return APP.oidc.accept_token(require_token=False)(f)

    # OIDC is not configured, so just allow anonymous access
    return f

#####################################################
# Decorator for APIs that *require* a valid API token
#####################################################
def require_api_token(f):
    """Require a valid OIDC token for access to the API endpoint"""
    if APP.oidc is not None:
        validated = APP.oidc.accept_token(require_token=True)(f)
    else:
        # OIDC is not configured, so disallow APIs that require authentication
        validated = _report_oidc_not_configured

    @wraps(f)
    def _authenticated_api_access(api_resource, *args, **kwds):
        return _validate_api_token(validated, f, api_resource, *args, **kwds)
    return _authenticated_api_access


def _report_oidc_not_configured(api_resource, *args, **kwds):
    error_details = json.dumps({
        'error': 'oidc_not_configured',
        'error_description': 'OpenID Connect is not configured on the server'
    })
    return (error_details, 401, {'WWW-Authenticate': 'Bearer'})

def _validate_api_token(validated_api, raw_api, *args, **kwds):
    """Hook to allow token validation to be overridden for testing purposes"""
    return validated_api(*args, **kwds)
