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
        if name == "fedora":
            user_info = client.userinfo(token=token)
            user_info["email"] = client.get("email", token=token)
        elif name == "github":
            user_info = token.get("user", token=token)
        else:
            user_info = token.get("userinfo")
            if not user_info:
                user_info = client.userinfo()

        _log.debug("Obtained user_info from %s: %s", name, user_info)

        # Check if the user exists
        user = User.query.filter(User.email == user_info["email"]).first()
        if not user:
            new_user = User(
                email=user_info["email"], username=user_info["preferred_username"]
            )
            Session.add(new_user)
            Session.commit()
            user = new_user
        flask_login.login_user(user)

        if flask.session["next_url"]:
            return flask.redirect(flask.session["next_url"])
        return flask.redirect("/")

    return auth_blueprint
