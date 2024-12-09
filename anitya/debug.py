# -*- coding: utf-8 -*-

"""
This module contains blueprints that are only included
 when application is running in debug mode.
"""
import flask
import flask_login

from anitya.db import Session, User

debug_blueprint = flask.Blueprint(
    "anitya_debug", __name__, static_folder="static", template_folder="templates"
)


@debug_blueprint.route("/login/debug/<name>")
def login(name: str):
    """
    Debug login for prepared users.

    Params:
      name: User to log as in.
    """
    user = User.query.filter(User.username == name).first()

    # Create user if it doesn't exist yet
    if not user:
        user = User(
            username=name, email=(name + "@example.com"), admin=(name == "admin")
        )
        Session.add(user)
        Session.commit()

    flask_login.login_user(user)
    if flask.session["next_url"]:
        return flask.redirect(flask.session["next_url"])
    return flask.redirect("/")
