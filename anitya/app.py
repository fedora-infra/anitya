# -*- coding: utf-8 -*-

"""
This module is responsible for creating and configuring the flask application
object. This includes loading any provided configuration and merging it with
the default configuration, loading and configuring Flask extensions, and
configuring logging.

User-facing Flask routes should be placed in the ``anitya.ui`` module and API
routes should be placed in ``anitya.api_v2``.
"""

import logging
import logging.config
import logging.handlers

import flask
from flask_restful import Api
from flask_login import LoginManager, current_user, user_logged_in
from social_core.backends.utils import load_backends
from social_core.exceptions import AuthException
from social_flask.routes import social_auth
from social_flask_sqlalchemy import models as social_models
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from anitya.config import config as anitya_config
from anitya.db import Session, initialize as initialize_db, models
from anitya.lib import utilities
from . import ui, admin, api, api_v2, authentication
import anitya.lib
import anitya.mail_logging
from anitya import __version__


def create(config=None):
    """
    Create and configure a Flask application object.

    Args:
        config (dict): The configuration to use when creating the application.
            If no configuration is provided, :data:`anitya.config.config` is
            used.

    Returns:
        flask.Flask: The configured Flask application.
    """
    app = flask.Flask(__name__)

    if config is None:
        config = anitya_config
    app.config.update(config)
    initialize_db(config)

    app.register_blueprint(social_auth)
    if len(social_models.UserSocialAuth.__table_args__) == 0:
        # This is a bit of a hack - this initialization call sets up the SQLAlchemy
        # models with our own models and multiple calls to this function will cause
        # SQLAlchemy to fail with sqlalchemy.exc.InvalidRequestError. Only calling it
        # when there are no table arguments should ensure we only call it one time.
        #
        # Be aware that altering the configuration values this function uses, namely
        # the SOCIAL_AUTH_USER_MODEL, after the first time ``create`` has been called
        # will *not* cause the new configuration to be used for subsequent calls to
        # ``create``.
        social_models.init_social(app, Session)

    login_manager = LoginManager()
    login_manager.user_loader(authentication.load_user_from_session)
    login_manager.request_loader(authentication.load_user_from_request)
    login_manager.login_view = "/login/"
    login_manager.init_app(app)

    # Register the v2 API resources
    app.api = Api(app)
    app.api.add_resource(
        api_v2.ProjectsResource, "/api/v2/projects/", endpoint="apiv2.projects"
    )
    app.api.add_resource(
        api_v2.PackagesResource, "/api/v2/packages/", endpoint="apiv2.packages"
    )
    app.api.add_resource(
        api_v2.VersionsResource, "/api/v2/versions/", endpoint="apiv2.versions"
    )

    # Register all the view blueprints
    app.register_blueprint(ui.ui_blueprint)
    app.register_blueprint(api.api_blueprint)

    app.before_request(global_user)
    app.teardown_request(shutdown_session)
    app.register_error_handler(IntegrityError, integrity_error_handler)
    app.register_error_handler(AuthException, auth_error_handler)

    app.context_processor(inject_variable)

    # subscribe to signals
    user_logged_in.connect(when_user_log_in, app)

    if app.config.get("EMAIL_ERRORS"):
        # If email logging is configured, set up the anitya logger with an email
        # handler for any ERROR-level logs.
        _anitya_log = logging.getLogger("anitya")
        _anitya_log.addHandler(
            anitya.mail_logging.get_mail_handler(
                smtp_server=app.config.get("SMTP_SERVER"),
                mail_admin=app.config.get("ADMIN_EMAIL"),
            )
        )

    return app


def global_user():
    """Set the flask.g variables using the session information if the user is logged in."""
    flask.g.user = current_user._get_current_object()


def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    Session.remove()


def inject_variable():
    """Inject into all templates variables that we would like to have all
    the time.
    """
    justedit = flask.session.get("justedit", False)
    if justedit:  # pragma: no cover
        flask.session["justedit"] = None

    cron_status = utilities.get_last_cron(Session)

    return dict(
        version=__version__,
        is_admin=admin.is_admin(),
        justedit=justedit,
        cron_status=cron_status,
        user=current_user,
        available_backends=load_backends(
            anitya_config["SOCIAL_AUTH_AUTHENTICATION_BACKENDS"]
        ),
    )


def integrity_error_handler(error):
    """
    Flask error handler for unhandled IntegrityErrors.

    Args:
        error (IntegrityError): The exception to be handled.

    Returns:
        tuple: A tuple of (message, HTTP error code).
    """
    # Because social auth provides the route and raises the exception, this is
    # the simplest way to turn the error into a nicely formatted error message
    # for the user.
    if "email" in error.params:
        Session.rollback()
        other_user = models.User.query.filter_by(email=error.params["email"]).one()
        try:
            social_auth_user = other_user.social_auth.filter_by(
                user_id=other_user.id
            ).one()
            msg = (
                "Error: There's already an account associated with your email, "
                "authenticate with {}.".format(social_auth_user.provider)
            )
            return msg, 400
        # This error happens only if there is account without provider info
        except NoResultFound:
            Session.delete(other_user)
            Session.commit()
            msg = (
                "Error: There was already an existing account with missing provider. "
                "So we removed it. "
                "Please try to log in again."
            )
            return msg, 500

    return "The server encountered an unexpected error", 500


def auth_error_handler(error):
    """
    Flask error handler for unhandled AuthException errors.

    Args:
        error (AuthException): The exception to be handled.

    Returns:
        tuple: A tuple of (message, HTTP error code).
    """
    # Because social auth openId backend provides route and raises the exceptions,
    # this is the simplest way to turn error into nicely formatted error message.
    msg = (
        "Error: There was an error during authentication '{}', "
        "please check the provided url.".format(error)
    )
    return msg, 400


def when_user_log_in(sender, user):
    """
    This catches the signal when user is logged in.
    It checks if the user has associated entry in user_social_auth.

    Args:
        sender (flask.Flask): Current app object that emitted signal.
            Not used by this method.
        user (models.User): User that is logging in.

    Raises:
        sqlalchemy.exc.IntegrityError: When user_social_auth table entry is
        missing.
    """
    if user.social_auth.count() == 0:
        raise IntegrityError(
            "Missing social_auth table",
            {"social_auth": None, "email": user.email},
            None,
        )
