# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2017  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""
Helper module for configuring OpenID Connect based authentication
"""
from functools import wraps
import json

import flask
from flask_openid import OpenID
from flask_oidc import OpenIDConnect

APP = None


####################################
# Set up core OpenID Connect support
####################################

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
    app.route("/oidc_callback")(register_oidc_client)
    APP = app


def register_oidc_client(code, state):
    """Accept OpenIDConnect callback from authentication server"""
    # TODO: Actually handle online token generation properly
    #       https://github.com/release-monitoring/anitya/issues/442
    token_data = {}
    result = flask.jsonify(token_data)
    result.status_code = 200
    return result


##################################################
# Helpers for declaring OIDC enabled API endpoints
##################################################

def parse_api_token(f):
    """Decorator for APIs that parse API tokens, but don't require them

    Makes OIDC token information available, but allows anonymous access
    """
    if APP.oidc is not None:
        return APP.oidc.accept_token(require_token=False)(f)

    # OIDC is not configured, so just allow anonymous access
    return f


# Note: the scopes listed in _DEFINED_SCOPES must match those listed in
# https://fedoraproject.org/wiki/Infrastructure/Authentication#release-monitoring.org
#
# To add new entries this list:
# * request changes as per https://fedoraproject.org/wiki/Infrastructure/Authentication#Registering_new_scopes
# * amend _DEFINED_SCOPES below
# * amend anitya.default_config.OIDC_SCOPES
_BASE_SCOPE_URL = "https://release-monitoring.org/oidc/"

_DEFINED_SCOPES = {
    "upstream": "Register upstream projects for monitoring",
    "downstream": "Register downstreams & upstream/downstream mappings"
}


def require_api_token(*scopes):
    """Decorator factory for APIs that *require* a valid OIDC API token

    Anonymous access attempts will be automatically declined.
    """
    if not scopes:
        # Project policy requirement - no unscoped access allowed
        msg = "Authenticated APIs must specify at least one scope"
        raise RuntimeError(msg)

    url_scopes = []
    for scope in scopes:
        # Project policy requirement - nominal scopes must be listed above
        if scope not in _DEFINED_SCOPES:
            msg = "Unknown authentication scope: {0}"
            raise RuntimeError(msg.format(scope))
        url_scopes.append(_BASE_SCOPE_URL + scope)

    if APP.oidc is not None:
        # OIDC is configured, check supplied token has relevant permissions
        validator = APP.oidc.accept_token(require_token=True,
                                          scopes_required=url_scopes)
    else:
        # OIDC is not configured, so disallow APIs that require authentication
        def validator(f):
            return _report_oidc_not_configured

    # Return a decorator that wraps the API endpoint in _validate_api_token
    def _make_validated_wrapper(f):
        @wraps(f)
        def _authenticated_api_access(api_resource, *args, **kwds):
            return _validate_api_token(validator(f), f, api_resource,
                                       *args, **kwds)
        return _authenticated_api_access

    return _make_validated_wrapper


def _report_oidc_not_configured(*args, **kwds):
    # TODO: Avoid double-rendering to JSON when used with Flask-RESTful
    #       https://github.com/release-monitoring/anitya/issues/443
    error_details = json.dumps({
        'error': 'oidc_not_configured',
        'error_description': 'OpenID Connect is not configured on the server'
    })
    return (error_details, 401, {'WWW-Authenticate': 'Bearer'})


def _validate_api_token(validated_api, raw_api, *args, **kwds):
    """Hook to allow token validation to be overridden for testing purposes"""
    return validated_api(*args, **kwds)
