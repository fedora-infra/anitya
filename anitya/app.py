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
from bunch import Bunch
from flask_restful import Api

from anitya.config import config as anitya_config
from anitya.lib import utilities
from anitya.lib.model import Session as SESSION, initialize as initialize_db
from . import ui, admin, api, api_v2, authentication  # noqa: F401
import anitya.lib
import anitya.mail_logging


__version__ = '0.11.0'


# For API compatibility
login_required = ui.login_required


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

    # Set up the Flask extensions
    authentication.configure_openid(app)

    # Register the v2 API resources
    app.api = Api(app)
    app.api.add_resource(api_v2.ProjectsResource, '/api/v2/projects/')

    # Register all the view blueprints
    app.register_blueprint(ui.ui_blueprint)
    app.register_blueprint(api.api_blueprint)

    app.before_request(check_auth)
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


def check_auth():
    ''' Set the flask.g variables using the session information if the user
    is logged in.
    '''

    flask.g.auth = Bunch(
        logged_in=False,
        method=None,
        id=None,
    )
    if 'openid' in flask.session:
        flask.g.auth.logged_in = True
        flask.g.auth.method = u'openid'
        flask.g.auth.openid = flask.session.get('openid')
        flask.g.auth.fullname = flask.session.get('fullname', None)
        flask.g.auth.nickname = flask.session.get('nickname', None)
        flask.g.auth.email = flask.session.get('email', None)


def shutdown_session(exception=None):
    ''' Remove the DB session at the end of each request. '''
    SESSION.remove()


def inject_variable():
    ''' Inject into all templates variables that we would like to have all
    the time.
    '''
    justedit = flask.session.get('justedit', False)
    if justedit:  # pragma: no cover
        flask.session['justedit'] = None

    cron_status = utilities.get_last_cron(SESSION)

    return dict(
        version=__version__,
        is_admin=admin.is_admin(),
        justedit=justedit,
        cron_status=cron_status,
    )


@authentication.oid.after_login
def after_openid_login(resp):
    ''' This function saved the information about the user right after the
    login was successful on the OpenID server.
    '''
    default = flask.url_for('anitya_ui.index')
    blacklist = flask.current_app.config['BLACKLISTED_USERS']
    if resp.identity_url:
        next_url = flask.request.args.get('next', default)
        openid_url = resp.identity_url
        if openid_url in blacklist or resp.email in blacklist:
            flask.flash(
                'We are very sorry but your account has been blocked from '
                'logging in to this service.', 'error')
            return flask.redirect(next_url)

        flask.session['openid'] = openid_url
        flask.session['fullname'] = resp.fullname
        flask.session['nickname'] = resp.nickname or resp.fullname
        flask.session['email'] = resp.email
        return flask.redirect(next_url)
    else:
        return flask.redirect(default)


APP = create()
