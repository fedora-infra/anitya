"""
This module handles the authentication using authlib.

It provides login route as well as callback for OAuth2 calls.
"""

import flask
import flask_login

from anitya.db import Session, User


def create_auth_blueprint(oauth):
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
            flask.abort(400)
        redirect_uri = flask.url_for(".auth", name=name, _external=True)
        return client.authorize_redirect(redirect_uri)

    @auth_blueprint.route("/auth/<name>")
    def auth(name):
        """
        Callback function for OAuth backends.

        Params:
        name: Name of the authentication backend to login with
        """
        client = oauth.create_client(name)
        if client is None:
            flask.abort(404)
        token = client.authorize_access_token()
        user_info = token.get("userinfo")
        if not user_info:
            user_info = client.userinfo()

        # Check if the user exists
        user = User.query.filter(User.email == user_info["email"]).first()
        if not user:
            new_user = User(email=user_info["email"], username=user_info["email"])
            Session.add(new_user)
            Session.commit()
            user = new_user
        flask_login.login_user(user)

        if flask.session["next_url"]:
            return flask.redirect(flask.session["next_url"])
        return flask.redirect("/")

    return auth_blueprint
