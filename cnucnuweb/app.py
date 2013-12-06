#-*- coding: utf-8 -*-

import codecs
import functools
import os
from collections import OrderedDict
from datetime import datetime
from math import ceil

import docutils
import docutils.examples
import flask
import jinja2
import markupsafe
import sqlalchemy
from bunch import Bunch
from flask.ext.openid import OpenID

from cnucnu.package_list import Package

import cnucnuweb.model
import cnucnuweb.forms


__version__ = '0.1.0'

# Create the application.
APP = flask.Flask(__name__)

APP.config.from_object('cnucnuweb.default_config')
if 'CNUCNU_WEB_CONFIG' in os.environ:  # pragma: no cover
    app.config.from_envvar('CNUCNU_WEB_CONFIG')

# Set up OpenID
OID = OpenID(APP)

SESSION = cnucnuweb.model.init(
    APP.config['DB_URL'], debug=False, create=False)

URL_ALIASES = OrderedDict({
    '': 'Specific version page',
    'SF-DEFAULT': 'SourceForge project',
    'FM-DEFAULT': 'FreshMeat project',
    'GNU-DEFAULT': 'GNU project',
    'CPAN-DEFAULT': 'CPAN project',
    'HACKAGE-DEFAULT': 'Hackage project',
    'DEBIAN-DEFAULT': 'Debian project',
    'GOOGLE-DEFAULT': 'Google code project',
    'PYPI-DEFAULT': 'PYPI project',
    'PEAR-DEFAULT': 'PHP pear project',
    'PECL-DEFAULT': 'PHP pecl project',
    'LP-DEFAULT': 'LaunchPad project',
    'GNOME-DEFAULT': 'GNOME project',
    'RUBYGEMS-DEFAULT': 'Rubygems project',
})

REGEX_ALIASES = OrderedDict({
    '': 'Specific regex',
    'DEFAULT': 'Default regex',
    'CPAN-DEFAULT': 'Default CPAN regex',
    'PEAR-DEFAULT': 'Default PEAR regex',
    'PECL-DEFAULT': 'Default PECL regex',
    'FM-DEFAULT': 'Default FreshMeat regex',
    'HACKAGE-DEFAULT': 'Default Hackage regex',
    'RUBYGEMS-DEFAULT': 'Default Rubygems regex',
})


@APP.before_request
def check_auth():
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


@OID.after_login
def after_openid_login(resp):
    default = flask.url_for('index')
    if resp.identity_url:
        openid_url = resp.identity_url
        flask.session['openid'] = openid_url
        flask.session['fullname'] = resp.fullname
        flask.session['nickname'] = resp.nickname or resp.fullname
        flask.session['email'] = resp.email
        next_url = flask.request.args.get('next', default)
        return flask.redirect(next_url)
    else:
        return flask.redirect(default)


@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()


def admin(user=None):
    if not user and flask.g.auth.logged_in:
        user = flask.g.auth.openid
    return user in APP.config.get('CNUCNU_WEB_ADMINS', [])


def login_required(function):
    """ Flask decorator to retrict access to logged-in users. """
    @functools.wraps(function)
    def decorated_function(*args, **kwargs):
        """ Decorated function, actually does the work. """
        if not flask.g.auth.logged_in:
            flask.flash('Login required', 'errors')
            return flask.redirect(
                flask.url_for('login', next=flask.request.url))

        return function(*args, **kwargs)
    return decorated_function


def api_method(function):
    """ A decorator to handle common API output stuff. """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
        except APIError as e:
            app.logger.exception(e)
            response = flask.jsonify(e.errors)
            response.status_code = e.status_code
        else:
            # Redirect browsers to the object.
            # otherwise, return json response to api clients.
            if 'url' in result and request_wants_html():
                response = flask.redirect(result['url'])
            else:
                response = flask.jsonify(result)
                response.status_code = 200
        return response

    return wrapper


@APP.context_processor
def inject_variable():
    """ Inject into all templates variables that we would like to have all
    the time.
    """
    return dict(version=__version__,
                is_admin=admin())


@APP.route('/')
def index():
    total = cnucnuweb.model.Project.all(SESSION, count=True)
    return flask.render_template(
        'index.html',
        current='index',
        total=total,
    )


@APP.route('/about')
def about():
    return flask.render_template(
        'docs.html',
        current='about',
        docs=load_docs(flask.request),
    )


@APP.route('/project/<project_name>')
@APP.route('/project/<project_name>/')
def project(project_name):

    project = cnucnuweb.model.Project.by_name(SESSION, project_name)

    if not project:
        flask.abort(404)

    return flask.render_template(
        'project.html',
        current='project',
        project=project)


@APP.route('/api/projects')
@APP.route('/api/projects/')
def api_projects():

    project_objs = cnucnuweb.model.Project.all(SESSION)

    projects = []
    for project in project_objs:
        tmp = '* {name} {regex} {version_url}'.format(
            name=project.name,
            regex=project.regex,
            version_url=project.version_url)
        projects.append(tmp)

    return flask.Response(
        "\n".join(projects),
        content_type="text/plain;charset=UTF-8"
    )


@APP.route('/api/version/', methods=['POST'])
def api_get_version():

    name = flask.request.form.get('name', None)
    url = flask.request.form.get('url', None)
    regex = flask.request.form.get('regex', None)
    httpcode = 200

    if not name or not url or not regex:
        errors = []
        if not name:
            errors.append('No name specified')
        if not url:
            errors.append('No url specified')
        if not regex:
            errors.append('No regex specified')
        output = {'output': 'notok', 'error': errors}
        httpcode = 400
    else:
        try:
            pkg = Package(name=name, url=url, regex=regex)
            versions = pkg.upstream_versions
            latest_version = pkg.latest_upstream
        except Exception as err:
            output = {'output': 'notok', 'error': err.message}
            httpcode = 400
        else:
            output = {
                'name': pkg.name,
                'url': pkg.url,
                'regex': pkg.regex,
                'raw_url': pkg.raw_url,
                'raw_regex': pkg.raw_regex,
                'versions': versions,
                'latest_version': latest_version,
            }

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@APP.route('/projects')
@APP.route('/projects/')
def projects():

    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = cnucnuweb.model.Project.all(SESSION, page=page)
    projects_count = cnucnuweb.model.Project.all(SESSION, count=True)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'projects.html',
        current='projects',
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page)


@APP.route('/distros')
@APP.route('/distros/')
def distros():

    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    distros = cnucnuweb.model.Distro.all(SESSION, page=page)
    distros_count = cnucnuweb.model.Distro.all(SESSION, count=True)

    total_page = int(ceil(distros_count / float(50)))

    return flask.render_template(
        'distros.html',
        current='distros',
        distros=distros,
        total_page=total_page,
        distros_count=distros_count,
        page=page)


@APP.route('/projects/search')
@APP.route('/projects/search/<pattern>')
def projects_search(pattern=None):

    pattern = flask.request.args.get('pattern', pattern) or '*'
    page = flask.request.args.get('page', 1)

    if not '*' in pattern:
        pattern += '*'

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = cnucnuweb.model.Project.search(
        SESSION, pattern=pattern, page=page)
    projects_count = cnucnuweb.model.Project.search(
        SESSION, pattern=pattern, count=True)

    if projects_count == 1 and projects[0].name == pattern.replace('*', ''):
        flask.flash(
            'Only one result matching with an exact match, redirecting')
        return flask.redirect(
            flask.url_for('project', project_name=projects[0].name))

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'search.html',
        current='projects',
        pattern=pattern,
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page)


@APP.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():

    form = cnucnuweb.forms.ProjectForm()

    if form.validate_on_submit():
        name = form.name.data
        homepage = form.homepage.data
        version_url = form.version_url.data
        regex = form.regex.data

        project = cnucnuweb.model.Project.get_or_create(
            SESSION,
            name=name,
            homepage=homepage,
            version_url=version_url,
            regex=regex,
        )
        cnucnuweb.log(
                SESSION,
                distro=distro,
                topic='project.add',
                message=dict(
                    agent=flask.g.auth.email,
                    project=project,
                )
            )
        SESSION.commit()
        if project.created_on.date() == datetime.today():
            message = 'Project created'
        else:
            message = 'Project existed already'
        flask.flash(message)
        return flask.redirect(
            flask.url_for('project', project_name=name)
        )

    return flask.render_template(
        'project_new.html',
        context='Add',
        current='Add projects',
        form=form,
        url_aliases=URL_ALIASES,
        regex_aliases=REGEX_ALIASES)


@APP.route('/project/<project_name>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_name):

    project = cnucnuweb.model.Project.by_name(SESSION, project_name)
    if not project:
        flask.abort(404)

    form = cnucnuweb.forms.ProjectForm()

    if form.validate_on_submit():
        name = form.name.data
        homepage = form.homepage.data
        version_url = form.version_url.data
        regex = form.regex.data

        edit = []
        if name != project.name:
            project.name = name
            edit = 'name'
        if homepage != project.homepage:
            project.homepage = homepage
            edit = 'homepage'
        if version_url != project.version_url:
            project.version_url = version_url
            edit = 'version_url'
        if regex != project.regex:
            project.regex = regex
            edit = 'regex'

        if edit:
            cnucnuweb.log(
                SESSION,
                distro=distro,
                topic='project.edit',
                message=dict(
                    agent=flask.g.auth.email,
                    project=project,
                    fields=', '.join(edit)
                )
            )

            SESSION.add(project)
            SESSION.commit()
            message = 'Project edited'
            flask.flash(message)
        return flask.redirect(
            flask.url_for('project', project_name=name)
        )
    else:
        form = cnucnuweb.forms.ProjectForm(project=project)

    return flask.render_template(
        'project_new.html',
        context='Edit',
        current='projects',
        form=form,
        url_aliases=URL_ALIASES,
        regex_aliases=REGEX_ALIASES)


@APP.route('/distro/<distro_name>/edit', methods=['GET', 'POST'])
@login_required
def edit_distro(distro_name):

    distro = cnucnuweb.model.Distro.by_name(SESSION, distro_name)
    if not distro:
        flask.abort(404)

    if not admin():
        flask.abort(405)

    form = cnucnuweb.forms.DistroForm()

    if form.validate_on_submit():
        name = form.name.data

        if name != distro.name:
            cnucnuweb.log(
                SESSION,
                distro=distro,
                topic='distro.edit',
                message=dict(
                    agent=flask.g.auth.email,
                    old=distro.name,
                    new=name,
                )
            )

            distro.name = name

            SESSION.add(distro)
            SESSION.commit()
            message = 'Distribution edited'
            flask.flash(message)
        return flask.redirect(
            flask.url_for('distros')
        )
    else:
        form = cnucnuweb.forms.DistroForm(distro=distro)

    return flask.render_template(
        'distro_edit.html',
        current='distros',
        distro=distro,
        form=form)


@APP.route('/project/<project_name>/delete', methods=['GET', 'POST'])
@login_required
def delete_project(project_name):

    if not admin():
        flask.abort(403)

    project = cnucnuweb.model.Project.by_name(SESSION, project_name)
    if not project:
        flask.abort(404)

    form = cnucnuweb.forms.ConfirmationForm()
    confirm = flask.request.form.get('confirm', False)

    if form.validate_on_submit():
        if confirm:
            cnucnuweb.log(
                SESSION,
                project=project,
                topic='project.remove',
                message=dict(
                    agent=flask.g.auth.email,
                    project=project.name,
                )
            )

            SESSION.delete(project)
            SESSION.commit()
            flask.flash('Project %s has been removed' % project_name)
            return flask.redirect(flask.url_for('projects'))
        else:
            return flask.redirect(
                flask.url_for('project', project_name=project_name))

    return flask.render_template(
        'project_delete.html',
        current='projects',
        project=project,
        form=form)


@APP.route('/project/<project_name>/map', methods=['GET', 'POST'])
@login_required
def map_project(project_name):

    project = cnucnuweb.model.Project.by_name(SESSION, project_name)
    if not project:
        flask.abort(404)

    form = cnucnuweb.forms.ConfirmationForm()

    if form.validate_on_submit():
        distros = flask.request.form.getlist('distros')
        pkgnames = flask.request.form.getlist('pkgname')

        cnt = 0
        msgs = []
        for distro in distros:
            distro = distro.strip()
            pkgname = pkgnames[cnt].strip()
            if not distro or not pkgname:
                continue
            else:
                pkg = cnucnuweb.model.Packages.get(
                    SESSION, project.name, distro)
                if pkg:
                    if pkg.package_name != pkgname:
                        cnucnuweb.log(
                            SESSION,
                            project=project,
                            topic='project.map.update',
                            message=dict(
                                agent=flask.g.auth.email,
                                project=project.name,
                                distro=distro,
                                prev=pkg.package_name,
                                new=pkgname,
                            )
                        )
                        pkg.package_name = pkgname
                        flask.flash('%s updated' % distro)
                else:
                    pkg = cnucnuweb.model.Packages.get_or_create(
                        SESSION, project.name, distro, pkgname)
                    flask.flash('%s updated' % distro)
                    cnucnuweb.log(
                        SESSION,
                        project=project,
                        topic='project.map.new',
                        message=dict(
                            agent=flask.g.auth.email,
                            project=project.name,
                            distro=distro,
                            new=pkgname,
                        )
                    )
            cnt += 1

        SESSION.commit()
        return flask.redirect(
            flask.url_for('project', project_name=project_name))

    return flask.render_template(
        'package.html',
        current='projects',
        project=project,
        form=form)


@APP.route('/login/', methods=('GET', 'POST'))
@APP.route('/login', methods=('GET', 'POST'))
@OID.loginhandler
def login():
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    if flask.g.auth.logged_in:
        return flask.redirect(next_url)

    openid_server = flask.request.form.get('openid', None)
    if openid_server:
        return OID.try_login(
            openid_server, ask_for=['email', 'fullname', 'nickname'])

    return flask.render_template(
        'login.html', next=OID.get_next_url(), error=OID.fetch_error())


@APP.route('/login/fedora/')
@APP.route('/login/fedora')
@OID.loginhandler
def fedora_login():
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    return OID.try_login(
        APP.config['CNUCNU_WEB_FEDORA_OPENID'],
        ask_for=['email', 'fullname', 'nickname'])


@APP.route('/login/google/')
@APP.route('/login/google')
@OID.loginhandler
def google_login():
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    return OID.try_login(
        "https://www.google.com/accounts/o8/id",
        ask_for=['email', 'fullname'])


@APP.route('/login/yahoo/')
@APP.route('/login/yahoo')
@OID.loginhandler
def yahoo_login():
    default = flask.url_for('index')
    next_url = flask.request.args.get('next', default)
    return OID.try_login(
        "https://me.yahoo.com/",
        ask_for=['email', 'fullname'])


@APP.route('/logout/')
@APP.route('/logout')
def logout():
    flask.session.pop('openid')
    return flask.redirect(flask.url_for('index'))


def modify_rst(rst):
    """ Downgrade some of our rst directives if docutils is too old. """

    try:
        # The rst features we need were introduced in this version
        minimum = [0, 9]
        version = map(int, docutils.__version__.split('.'))

        # If we're at or later than that version, no need to downgrade
        if version >= minimum:
            return rst
    except Exception:
        # If there was some error parsing or comparing versions, run the
        # substitutions just to be safe.
        pass

    # Otherwise, make code-blocks into just literal blocks.
    substitutions = {
        '.. code-block:: javascript': '::',
    }
    for old, new in substitutions.items():
        rst = rst.replace(old, new)

    return rst


def modify_html(html):
    """ Perform style substitutions where docutils doesn't do what we want.
    """

    substitutions = {
        '<tt class="docutils literal">': '<code>',
        '</tt>': '</code>',
    }
    for old, new in substitutions.items():
        html = html.replace(old, new)

    return html


def preload_docs(endpoint):
    """ Utility to load an RST file and turn it into fancy HTML. """

    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'docs', endpoint + '.rst')
    with codecs.open(fname, 'r', 'utf-8') as f:
        rst = f.read()

    rst = modify_rst(rst)
    api_docs = docutils.examples.html_body(rst)
    api_docs = modify_html(api_docs)
    api_docs = markupsafe.Markup(api_docs)
    return api_docs

htmldocs = dict.fromkeys(['about'])
for key in htmldocs:
    htmldocs[key] = preload_docs(key)


def load_docs(request):
    URL = request.url_root
    docs = htmldocs[request.endpoint]
    docs = jinja2.Template(docs).render(URL=URL)
    return markupsafe.Markup(docs)
