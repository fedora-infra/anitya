"""
This module handles the authentication using authlib.

It provides login route as well as callback for OAuth2 calls.
"""

import logging

import flask
import flask_login

from anitya.db import Session, User

_log = logging.getLogger(__name__)


def create_auth_blueprint(oauth):
    """
    Create authentication blueprint.
    """
    auth_blueprint = flask.Blueprint(
        "anitya_auth", __name__, static_folder="static", template_folder="templates"
    )

    @auth_blueprint.route("/login/<name>")
    def login(name):
        """
        Login function for OAuth backends.

        Params:
        name: Name of the authentication backend to login with
        """
        client = oauth.create_client(name)
        if client is None:
            flask.abort(404)
        redirect_uri = flask.url_for(".auth", name=name, _external=True)
        return client.authorize_redirect(redirect_uri)

    @auth_blueprint.route("/auth/<name>")
    def auth(name):  # pragma: no cover
        """
        Callback function for OAuth backends.

        Params:
        name: Name of the authentication backend to login with
        """
        client = oauth.create_client(name)
        if client is None:
            flask.abort(404)
        token = client.authorize_access_token()
        # Fedora specifics
        if name == "fedora":
            user_info = client.userinfo(token=token)
            user_info["username"] = user_info["preferred_username"]
            user_info["email"] = user_info["username"] + "@fedoraproject.org"
        # GitHub specifics
        elif name == "github":
            resp = client.get("user", token=token)
            user_info = resp.json()
            user_info["username"] = user_info["login"]
            if not user_info["email"]:
                resp = client.get("user/emails", token=token)
                emails = resp.json()
                for email in emails:
                    if email["primary"]:
                        user_info["email"] = email["email"]
        # Google specifics
        elif name == "google":
            user_info = token.get("userinfo")
            user_info["username"] = user_info["email"]
        else:
            user_info = token.get("userinfo")
            if not user_info:
                user_info = client.userinfo()

        _log.debug("Obtained user_info from %s: %s", name, user_info)

        # Check if the user exists
        _log.debug("Looking for the user %s in database...", user_info["email"])
        user = User.query.filter(User.email == user_info["email"]).first()
        if not user:
            _log.debug("User not found. Creating new user...")
            new_user = User(email=user_info["email"], username=user_info["username"])
            Session.add(new_user)
            Session.commit()
            user = new_user
        elif user.username != user_info["username"]:
            user.username = user_info["username"]
            Session.add(user)
            Session.commit()
        _log.debug("Logging as user %s", user.email)
        flask_login.login_user(user)

        if flask.session["next_url"]:
            return flask.redirect(flask.session["next_url"])
        return flask.redirect("/")

    return auth_blueprint
