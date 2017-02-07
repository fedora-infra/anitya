#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""Helper to request live OIDC access permissions from FAS"""
import json
import os.path
import webbrowser
from threading import Thread
try:
    # Default to Python 3
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs
except ImportError:
    # Handle running on Python 2 (otherwise we'd just use asyncio)
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from urlparse import urlparse, parse_qs

import requests
from requests_oauthlib import OAuth2Session

AUTH_TIMEOUT = 300
_this_dir = os.path.dirname(__file__)
SECRETS_FILE = os.path.join(_this_dir, "client_secrets.json")
CREDENTIALS_FILE = os.path.join(_this_dir, "tests", "oidc_credentials.json")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Callback handler to log the details of received OAuth callbacks"""
    def do_GET(self):
        self.server.oauth_callbacks.append(self.path)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Auth details passed back to command line app")


class OAuthCallbackServer(HTTPServer):
    """Local HTTP server to handle OAuth authentication callbacks"""
    def __init__(self, server_address):
        self.oauth_callbacks = []
        HTTPServer.__init__(self, server_address, OAuthCallbackHandler)


def receive_oauth_callback(timeout):
    """Blocking call to wait for a single OAuth authentication callback"""
    server_address = ('', 5000)
    oauthd = OAuthCallbackServer(server_address)
    oauthd.timeout = timeout
    try:
        oauthd.handle_request()
    finally:
        oauthd.server_close()
    callback_path = oauthd.oauth_callbacks.pop()
    parsed_response = urlparse(callback_path)
    query_details = parse_qs(parsed_response.query)
    print(query_details)
    return query_details["code"][0], query_details["state"][0]


def main():
    with open(SECRETS_FILE) as f:
        client_details = json.load(f)["web"]
    client_id = client_details["client_id"]
    client_secret = client_details["client_secret"]
    redirect_uri = client_details["redirect_uris"][0]
    auth_uri = client_details["auth_uri"]
    token_uri = client_details["token_uri"]
    scopes = ("https://release-monitoring.org/oidc/upstream",)
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)
    authorization_url, state = oauth.authorization_url(auth_uri)
    wait_msg = "Waiting {0} seconds for browser-based authentication..."
    print(wait_msg.format(AUTH_TIMEOUT))
    webbrowser.open(authorization_url)
    # Technically a race condition, but should be faster than the OIDC
    # redirect flow even when the client has already been authenticated
    authorization_code, cb_state = receive_oauth_callback(AUTH_TIMEOUT)
    if cb_state != state:
        msg = "Callback state {0!r} didn't match request state {1!r}"
        raise RuntimeError(msg.format(cb_state, state))
    client_token = oauth.fetch_token(token_uri,
                                     code=authorization_code,
                                     client_secret=client_secret)
    oidc_credentials = {
        "client_details": client_details,
        "client_token": client_token
    }
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(oidc_credentials, f)
    print("OIDC client access details saved as " + CREDENTIALS_FILE)

if __name__ == "__main__":
    main()
