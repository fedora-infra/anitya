# -*- coding: utf-8 -*-

from math import ceil

import flask
import six.moves.urllib.parse as urlparse

import anitya
import anitya.lib
import anitya.lib.exceptions
import anitya.lib.model

from anitya.app import APP, SESSION, login_required


def get_extended_pattern(pattern):
    ''' For a given pattern `p` return it so that it looks like `*p*`
    adjusting it accordingly.
    '''

    if not pattern.startswith('*'):
        pattern = '*' + pattern
    if not pattern.endswith('*'):
        pattern += '*'
    return pattern


def is_safe_url(target):
    """ Checks that the target url is safe and sending to the current
    website not some other malicious one.
    """
    ref_url = urlparse.urlparse(flask.request.host_url)
    test_url = urlparse.urlparse(
        urlparse.urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


@APP.route('/')
def index():
    total = anitya.lib.model.Project.all(SESSION, count=True)
    return flask.render_template(
        'index.html',
        current='index',
        total=total,
    )


@APP.route('/about')
def about():
    """A backwards-compatibility route for old documentation links"""
    new_path = flask.url_for('static', filename='docs/index.html')
    return flask.redirect(new_path)


@APP.route('/fedmsg')
def fedmsg():
    """A backwards-compatibility route for old documentation links"""
    new_path = flask.url_for('static', filename='docs/user-guide.html')
    return flask.redirect(new_path)


@APP.route('/login/', methods=('GET', 'POST'))
@APP.route('/login', methods=('GET', 'POST'))
@APP.oid.loginhandler
def login():
    ''' Handle the login when no OpenID server have been selected in the
    list.
    '''
    next_url = flask.url_for('index')
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            next_url = flask.request.args['next']

    APP.oid.store_factory = lambda: None
    if flask.g.auth.logged_in:
        return flask.redirect(next_url)

    openid_server = flask.request.form.get('openid', None)
    if openid_server:
        return APP.oid.try_login(
            openid_server, ask_for=['email', 'fullname', 'nickname'])

    return flask.render_template(
        'login.html',
        next=APP.oid.get_next_url(), error=APP.oid.fetch_error())


@APP.route('/login/fedora/', methods=('GET', 'POST'))
@APP.route('/login/fedora', methods=('GET', 'POST'))
@APP.oid.loginhandler
def fedora_login():
    ''' Handles login against the Fedora OpenID server. '''
    error = APP.oid.fetch_error()
    if error:
        flask.flash('Error during login: %s' % error, 'errors')
        return flask.redirect(flask.url_for('index'))

    APP.oid.store_factory = lambda: None
    return APP.oid.try_login(
        APP.config['ANITYA_WEB_FEDORA_OPENID'],
        ask_for=['email', 'nickname'],
        ask_for_optional=['fullname'])


@APP.route('/login/google/', methods=('GET', 'POST'))
@APP.route('/login/google', methods=('GET', 'POST'))
@APP.oid.loginhandler
def google_login():
    ''' Handles login via the Google OpenID. '''
    error = APP.oid.fetch_error()
    if error:
        flask.flash('Error during login: %s' % error, 'errors')
        return flask.redirect(flask.url_for('index'))

    APP.oid.store_factory = lambda: None
    return APP.oid.try_login(
        "https://www.google.com/accounts/o8/id",
        ask_for=['email', 'fullname'])


@APP.route('/login/yahoo/', methods=('GET', 'POST'))
@APP.route('/login/yahoo', methods=('GET', 'POST'))
@APP.oid.loginhandler
def yahoo_login():
    ''' Handles login via the Yahoo OpenID. '''
    error = APP.oid.fetch_error()
    if error:
        flask.flash('Error during login: %s' % error, 'errors')
        return flask.redirect(flask.url_for('index'))

    APP.oid.store_factory = lambda: None
    return APP.oid.try_login(
        "https://me.yahoo.com/",
        ask_for=['email', 'fullname'])


@APP.route('/logout/')
@APP.route('/logout')
def logout():
    ''' Logout the user. '''
    flask.session.pop('openid')
    next_url = flask.url_for('index')
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            next_url = flask.request.args['next']

    return flask.redirect(next_url)


@APP.route('/project/<int:project_id>')
@APP.route('/project/<int:project_id>/')
def project(project_id):

    project = anitya.lib.model.Project.by_id(SESSION, project_id)

    if not project:
        flask.abort(404)

    return flask.render_template(
        'project.html',
        current='project',
        project=project,
    )


@APP.route('/project/<project_name>')
@APP.route('/project/<project_name>/')
def project_name(project_name):

    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = anitya.lib.model.Project.search(
        SESSION, pattern=project_name, page=page)
    projects_count = anitya.lib.model.Project.search(
        SESSION, pattern=project_name, count=True)

    if projects_count == 1:
        return project(projects[0].id)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'search.html',
        current='projects',
        pattern=project_name,
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page)


@APP.route('/projects')
@APP.route('/projects/')
def projects():

    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = anitya.lib.model.Project.all(SESSION, page=page)
    projects_count = anitya.lib.model.Project.all(SESSION, count=True)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'projects.html',
        current='projects',
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page)


@APP.route('/projects/updates')
@APP.route('/projects/updates/')
@APP.route('/projects/updates/<status>')
def projects_updated(status='updated'):

    page = flask.request.args.get('page', 1)
    name = flask.request.args.get('name', None)
    log = flask.request.args.get('log', None)

    try:
        page = int(page)
    except ValueError:
        page = 1

    statuses = ['new', 'updated', 'failed', 'never_updated', 'odd']

    if status not in statuses:
        flask.flash(
            '%s is invalid, you should use one of: %s; using default: '
            '`updated`' % (status, ', '.join(statuses)),
            'errors'
        )
        flask.flash(
            'Returning all the projects regardless of how/if their version '
            'was retrieved correctly')

    projects = anitya.lib.model.Project.updated(
        SESSION, status=status, name=name, log=log, page=page)
    projects_count = anitya.lib.model.Project.updated(
        SESSION, status=status, name=name, log=log, count=True)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'updates.html',
        current='projects',
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page,
        status=status,
        name=name,
        log=log,
    )


@APP.route('/distros')
@APP.route('/distros/')
def distros():

    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    distros = anitya.lib.model.Distro.all(SESSION, page=page)
    distros_count = anitya.lib.model.Distro.all(SESSION, count=True)

    total_page = int(ceil(distros_count / float(50)))

    return flask.render_template(
        'distros.html',
        current='distros',
        distros=distros,
        total_page=total_page,
        distros_count=distros_count,
        page=page)


@APP.route('/distro/<distroname>')
@APP.route('/distro/<distroname>/')
def distro(distroname):

    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = anitya.lib.model.Project.by_distro(
        SESSION, distro=distroname, page=page)
    projects_count = anitya.lib.model.Project.by_distro(
        SESSION, distro=distroname, count=True)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'projects.html',
        current='projects',
        projects=projects,
        distroname=distroname,
        total_page=total_page,
        projects_count=projects_count,
        page=page)


@APP.route('/projects/search')
@APP.route('/projects/search/')
@APP.route('/projects/search/<pattern>')
def projects_search(pattern=None):

    pattern = flask.request.args.get('pattern', pattern) or '*'
    page = flask.request.args.get('page', 1)
    exact = flask.request.args.get('exact', 0)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = anitya.lib.model.Project.search(
        SESSION, pattern=pattern, page=page)

    if not str(exact).lower() in ['1', 'true']:
        # Extends the search
        for proj in anitya.lib.model.Project.search(
                SESSION,
                pattern=get_extended_pattern(pattern),
                page=page):
            if proj not in projects:
                projects.append(proj)
        projects_count = anitya.lib.model.Project.search(
            SESSION, pattern=get_extended_pattern(pattern), count=True)
    else:
        projects_count = anitya.lib.model.Project.search(
            SESSION, pattern=pattern, count=True)

    if projects_count == 1 and projects[0].name == pattern.replace('*', ''):
        flask.flash(
            'Only one result matching with an exact match, redirecting')
        return flask.redirect(
            flask.url_for('project', project_id=projects[0].id))

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'search.html',
        current='projects',
        pattern=pattern,
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page)


@APP.route('/distro/<distroname>/search')
@APP.route('/distro/<distroname>/search/')
@APP.route('/distro/<distroname>/search/<pattern>')
def distro_projects_search(distroname, pattern=None):

    pattern = flask.request.args.get('pattern', pattern) or '*'
    page = flask.request.args.get('page', 1)
    exact = flask.request.args.get('exact', 0)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = anitya.lib.model.Project.search(
        SESSION, pattern=pattern, distro=distroname, page=page)

    if not str(exact).lower() in ['1', 'true']:
        # Extends the search
        for proj in anitya.lib.model.Project.search(
                SESSION,
                pattern=get_extended_pattern(pattern),
                distro=distroname,
                page=page):
            if proj not in projects:
                projects.append(proj)
        projects_count = anitya.lib.model.Project.search(
            SESSION,
            pattern=get_extended_pattern(pattern),
            distro=distroname, count=True)
    else:
        projects_count = anitya.lib.model.Project.search(
            SESSION, pattern=pattern, distro=distroname, count=True)

    if projects_count == 1 and projects[0].name == pattern.replace('*', ''):
        flask.flash(
            'Only one result matching with an exact match, redirecting')
        return flask.redirect(
            flask.url_for('project', project_id=projects[0].id))

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        'search.html',
        current='projects',
        pattern=pattern,
        projects=projects,
        distroname=distroname,
        total_page=total_page,
        projects_count=projects_count,
        page=page)


@APP.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """
    View for creating a new project.

    This function accepts GET and POST requests. POST requests can result in
    a HTTP 400 for invalid forms, a HTTP 409 if the request conflicts with an
    existing project, or a HTTP 302 redirect to the new project.
    """
    plugins = anitya.lib.plugins.load_plugins(SESSION)
    plg_names = [plugin.name for plugin in plugins]
    form = anitya.forms.ProjectForm(backends=plg_names)

    if flask.request.method == 'GET':
        form.name.data = flask.request.args.get('name', '')
        form.homepage.data = flask.request.args.get('homepage', '')
        form.backend.data = flask.request.args.get('backend', '')

        form.distro.data = flask.request.args.get('distro', '')
        form.package_name.data = flask.request.args.get('package_name', '')
        return flask.render_template(
            'project_new.html',
            context='Add',
            current='Add projects',
            form=form,
            plugins=plugins,
        )
    elif form.validate_on_submit():
        project = None
        try:
            project = anitya.lib.create_project(
                SESSION,
                name=form.name.data.strip(),
                homepage=form.homepage.data.strip(),
                backend=form.backend.data.strip(),
                version_url=form.version_url.data.strip() or None,
                version_prefix=form.version_prefix.data.strip() or None,
                regex=form.regex.data.strip() or None,
                user_id=flask.g.auth.openid,
                check_release=form.check_release.data,
            )
            SESSION.commit()

            # Optionally, the user can also map a distro when creating a proj.
            if form.distro.data and form.package_name.data:
                anitya.lib.map_project(
                    SESSION,
                    project=project,
                    package_name=form.package_name.data,
                    distribution=form.distro.data,
                    user_id=flask.g.auth.openid,
                )
                SESSION.commit()

            flask.flash('Project created')
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(str(err))
            return flask.render_template(
                'project_new.html',
                context='Add',
                current='Add projects',
                form=form,
                plugins=plugins
            ), 409

        if project:
            return flask.redirect(
                flask.url_for('project', project_id=project.id)
            )

    return flask.render_template(
        'project_new.html',
        context='Add',
        current='Add projects',
        form=form,
        plugins=plugins
    ), 400


@APP.route('/project/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    plugins = anitya.lib.plugins.load_plugins(SESSION)
    plg_names = [plugin.name for plugin in plugins]

    form = anitya.forms.ProjectForm(
        backends=plg_names,
        obj=project)

    if form.validate_on_submit():
        try:
            anitya.lib.edit_project(
                SESSION,
                project=project,
                name=form.name.data.strip(),
                homepage=form.homepage.data.strip(),
                backend=form.backend.data.strip(),
                version_url=form.version_url.data.strip(),
                version_prefix=form.version_prefix.data.strip(),
                regex=form.regex.data.strip(),
                insecure=form.insecure.data,
                user_id=flask.g.auth.openid,
                check_release=form.check_release.data,
            )
            flask.flash('Project edited')
            flask.session['justedit'] = True
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(str(err), 'errors')

        return flask.redirect(
            flask.url_for('project', project_id=project_id)
        )

    return flask.render_template(
        'project_new.html',
        context='Edit',
        current='projects',
        form=form,
        project=project,
        plugins=plugins,
    )


@APP.route('/project/<project_id>/flag', methods=['GET', 'POST'])
@login_required
def flag_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    form = anitya.forms.FlagProjectForm(
        obj=project)

    if form.validate_on_submit():
        try:
            anitya.lib.flag_project(
                SESSION,
                project=project,
                reason=form.reason.data,
                user_email=flask.g.auth.email,
                user_id=flask.g.auth.openid,
            )
            flask.flash('Project flagged for admin review')
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(str(err), 'errors')

        return flask.redirect(
            flask.url_for('project', project_id=project.id)
        )

    return flask.render_template(
        'project_flag.html',
        context='Flag',
        current='projects',
        form=form,
        project=project,
    )


@APP.route('/project/<project_id>/map', methods=['GET', 'POST'])
@login_required
def map_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    form = anitya.forms.MappingForm()

    if flask.request.method == 'GET':
        form.package_name.data = flask.request.args.get(
            'package_name', project.name)
        form.distro.data = flask.request.args.get('distro', '')

    if form.validate_on_submit():
        try:
            anitya.lib.map_project(
                SESSION,
                project=project,
                package_name=form.package_name.data.strip(),
                distribution=form.distro.data.strip(),
                user_id=flask.g.auth.openid,
            )
            SESSION.commit()
            flask.flash('Mapping added')
        except anitya.lib.exceptions.AnityaInvalidMappingException as err:
            err.link = flask.url_for('project', project_id=err.project_id)
            flask.flash(err.message, 'error')
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(str(err), 'error')

        return flask.redirect(
            flask.url_for('project', project_id=project.id)
        )

    return flask.render_template(
        'mapping.html',
        current='projects',
        project=project,
        form=form,
    )


@APP.route('/project/<project_id>/map/<pkg_id>', methods=['GET', 'POST'])
@login_required
def edit_project_mapping(project_id, pkg_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    package = anitya.lib.model.Packages.by_id(SESSION, pkg_id)
    if not package:
        flask.abort(404)

    form = anitya.forms.MappingForm(obj=package)

    if form.validate_on_submit():

        try:
            anitya.lib.map_project(
                SESSION,
                project=project,
                package_name=form.package_name.data,
                distribution=form.distro.data,
                user_id=flask.g.auth.openid,
                old_package_name=package.package_name,
                old_distro_name=package.distro,
            )

            SESSION.commit()
            flask.flash('Mapping edited')
        except anitya.lib.exceptions.AnityaInvalidMappingException as err:
            err.link = flask.url_for('project', project_id=err.project_id)
            flask.flash(err.message, 'error')
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(str(err), 'error')

        return flask.redirect(
            flask.url_for('project', project_id=project_id))

    return flask.render_template(
        'mapping.html',
        current='projects',
        project=project,
        package=package,
        form=form,
    )
