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
from flask_login import LoginManager, current_user
from social_core.backends.utils import load_backends
from social_flask.routes import social_auth
from social_flask_sqlalchemy import models as social_models

from anitya.config import config as anitya_config
from anitya.db import Session, initialize as initialize_db
from anitya.lib import utilities
from . import ui, admin, api, api_v2, authentication
import anitya.lib
import anitya.mail_logging


__version__ = '0.12.0'


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
    login_manager.login_view = '/login/'
    login_manager.init_app(app)

    # Register the v2 API resources
    app.api = Api(app)
    app.api.add_resource(api_v2.ProjectsResource, '/api/v2/projects/')
    app.api.add_resource(api_v2.PackagesResource, '/api/v2/packages/')

    # Register all the view blueprints
    app.register_blueprint(ui.ui_blueprint)
    app.register_blueprint(api.api_blueprint)

    app.before_request(global_user)
    app.teardown_request(shutdown_session)

    app.context_processor(inject_variable)

    if app.config.get('EMAIL_ERRORS'):
        # If email logging is configured, set up the anitya logger with an email
        # handler for any ERROR-level logs.
        _anitya_log = logging.getLogger('anitya')
        _anitya_log.addHandler(anitya.mail_logging.get_mail_handler(
            smtp_server=app.config.get('SMTP_SERVER'),
            mail_admin=app.config.get('ADMIN_EMAIL')
        ))

    return app


def global_user():
    """Set the flask.g variables using the session information if the user is logged in."""
    flask.g.user = current_user._get_current_object()


def shutdown_session(exception=None):
    ''' Remove the DB session at the end of each request. '''
    Session.remove()


def inject_variable():
    ''' Inject into all templates variables that we would like to have all
    the time.
    '''
    justedit = flask.session.get('justedit', False)
    if justedit:  # pragma: no cover
        flask.session['justedit'] = None

    cron_status = utilities.get_last_cron(Session)

    return dict(
        version=__version__,
        is_admin=admin.is_admin(),
        justedit=justedit,
        cron_status=cron_status,
        user=current_user,
        available_backends=load_backends(anitya_config['SOCIAL_AUTH_AUTHENTICATION_BACKENDS']),
    )
