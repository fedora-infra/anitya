# -*- coding: utf-8 -*-

"""
This module is responsible for creating and configuring the flask application
object. This includes loading any provided configuration and merging it with
the default configuration, loading and configuring Flask extensions, and
configuring logging.

User-facing Flask routes should be placed in the ``anitya.ui`` module and API
routes should be placed in ``anitya.api_v2``.
"""

import functools
import logging
import logging.config
import logging.handlers

import flask
from bunch import Bunch
from flask_restful import Api

from anitya.config import config as anitya_config
from anitya.lib import utilities
from anitya.lib.model import Session as SESSION, initialize as initialize_db
import anitya.lib
import anitya.authentication
import anitya.mail_logging


__version__ = '0.11.0'


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
    anitya.authentication.configure_openid(app)
    app.api = Api(app)

    if app.config.get('EMAIL_ERRORS'):
        # If email logging is configured, set up the anitya logger with an email
        # handler for any ERROR-level logs.
        _anitya_log = logging.getLogger('anitya')
        _anitya_log.addHandler(anitya.mail_logging.get_mail_handler(
            smtp_server=app.config.get('SMTP_SERVER'),
            mail_admin=app.config.get('ADMIN_EMAIL')
        ))

    return app


APP = create()


@APP.template_filter('format_examples')
def format_examples(examples):
    ''' Return the plugins examples as HTML links. '''
    output = ''
    if examples:
        for cnt, example in enumerate(examples):
            if cnt > 0:
                output += " <br /> "
            output += "<a href='%(url)s'>%(url)s</a> " % ({'url': example})

    return output


@APP.template_filter('context_class')
def context_class(category):
    ''' Return bootstrap context class for a given category. '''
    values = {
        'message': 'default',
        'error': 'danger',
        'info': 'info',
    }
    return values.get(category, 'warning')


@APP.before_request
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


@APP.oid.after_login
def after_openid_login(resp):
    ''' This function saved the information about the user right after the
    login was successful on the OpenID server.
    '''
    default = flask.url_for('index')
    blacklist = APP.config['BLACKLISTED_USERS']
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


@APP.teardown_request
def shutdown_session(exception=None):
    ''' Remove the DB session at the end of each request. '''
    SESSION.remove()


def is_admin(user=None):
    ''' Check if the provided user, or the user logged in are recognized
    as being admins.
    '''
    if not user and flask.g.auth.logged_in:
        user = flask.g.auth.openid
    return user in APP.config.get('ANITYA_WEB_ADMINS', [])


def login_required(function):
    ''' Flask decorator to retrict access to logged-in users. '''
    @functools.wraps(function)
    def decorated_function(*args, **kwargs):
        """ Decorated function, actually does the work. """
        if not flask.g.auth.logged_in:
            flask.flash('Login required', 'errors')
            return flask.redirect(
                flask.url_for('login', next=flask.request.url))

        return function(*args, **kwargs)
    return decorated_function


@APP.context_processor
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
        is_admin=is_admin(),
        justedit=justedit,
        cron_status=cron_status,
    )


# Finalize the import of other controllers
from . import api  # NOQA
from . import api_v2  # NOQA
from . import ui  # NOQA
from . import admin  # NOQA
