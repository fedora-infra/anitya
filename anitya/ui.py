# -*- coding: utf-8 -*-

from math import ceil

import flask

import anitya
import anitya.lib
import anitya.lib.exceptions
import anitya.lib.model

from anitya.app import APP, SESSION, login_required, load_docs


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
    return flask.render_template(
        'docs.html',
        current='about',
        docs=load_docs(flask.request),
    )


@APP.route('/project/<project_id>')
@APP.route('/project/<project_id>/')
def project(project_id):

    project = anitya.lib.model.Project.by_id(SESSION, project_id)

    if not project:
        flask.abort(404)

    return flask.render_template(
        'project.html',
        current='project',
        project=project,
    )


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


@APP.route('/projects/search')
@APP.route('/projects/search/')
@APP.route('/projects/search/<pattern>')
def projects_search(pattern=None):

    pattern = flask.request.args.get('pattern', pattern) or '*'
    page = flask.request.args.get('page', 1)

    if '*' not in pattern:
        pattern += '*'

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = anitya.lib.model.Project.search(
        SESSION, pattern=pattern, page=page)
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


@APP.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():

    plugins = anitya.lib.plugins.load_plugins(SESSION)
    plg_names = [plugin.name for plugin in plugins]

    form = anitya.forms.ProjectForm(backends=plg_names)

    if form.validate_on_submit():
        project = None
        try:
            project = anitya.lib.create_project(
                SESSION,
                name=form.name.data,
                homepage=form.homepage.data,
                backend=form.backend.data,
                version_url=form.version_url.data,
                regex=form.regex.data,
                user_mail=flask.g.auth.email,
            )
            flask.flash('Project created')
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(err)

        if project:
            return flask.redirect(
                flask.url_for('project', project_id=project.id)
            )

    return flask.render_template(
        'project_new.html',
        context='Add',
        current='Add projects',
        form=form,
        plugins=plugins,
    )


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
                name=form.name.data,
                homepage=form.homepage.data,
                backend=form.backend.data,
                version_url=form.version_url.data,
                regex=form.regex.data,
                user_mail=flask.g.auth.email,
            )
            flask.flash('Project edited')
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(str(err), 'errors')

        return flask.redirect(
            flask.url_for('project', project_id=project.id)
        )

    return flask.render_template(
        'project_new.html',
        context='Edit',
        current='projects',
        form=form,
        project=project,
        plugins=plugins,
    )


@APP.route('/project/<project_id>/map', methods=['GET', 'POST'])
@login_required
def map_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    form = anitya.forms.MappingForm()

    if form.validate_on_submit():

        try:
            anitya.lib.map_project(
                SESSION,
                project=project,
                package_name=form.package_name.data,
                distribution=form.distro.data,
                user_mail=flask.g.auth.email,
            )
            SESSION.commit()
            flask.flash('Mapping added')
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
                user_mail=flask.g.auth.email,
                old_package_name=package.package_name,
                old_distro_name=package.distro,
            )

            SESSION.commit()
            flask.flash('Mapping edited')
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
