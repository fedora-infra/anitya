import flask
import flask_login

from anitya.db import User, Session


def create_oauth_blueprint(oauth):
    oauth_blueprint = flask.Blueprint('oauth', __name__)

    @oauth_blueprint.route("/oauthlogin/<name>")
    def oauthlogin(name):
        client = oauth.create_client(name)
        if client is None:
            flask.abort(400)
        redirect_uri = flask.url_for('.auth', name=name, _external=True)
        return client.authorize_redirect(redirect_uri)


    @oauth_blueprint.route("/auth/<name>")
    def auth(name):
        client = oauth.create_client(name)
        if client is None:
            flask.abort(400)
        id_token = flask.request.values.get('id_token')
        if flask.request.values.get('code'):
            token = client.authorize_access_token()
            if id_token:
                token['id_token'] = id_token
        elif id_token:
            token = {'id_token': id_token}

        # for Google
        if 'id_token' in token:
            user_info = client.parse_id_token(token)
        # for Github
        else:
            client.response = client.get('user', token=token)
            user_info = client.response.json()
            if user_info['email'] is None:
                resp = client.get('user/emails', token=token)
                resp.raise_for_status()
                data = resp.json()
                user_info['email'] = next(email['email'] for email in data if email['primary'])

        # Check if the user exists
        user = User.query.filter(User.email == user_info['email']).first()
        if not user:

            # TODO: Should create the user (and openid connections) if it does not exist
            new_user = User(email=user_info['email'], username=user_info['email'])
            Session.add(new_user)
            Session.commit()
            user = new_user
        flask_login.login_user(user)

        # TODO: Process next not to just redirect with the main page
        return flask.redirect('/')

    return oauth_blueprint
