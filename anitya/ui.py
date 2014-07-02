#-*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
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

    plugins = anitya.plugins.get_plugin_names()

    form = anitya.forms.ProjectForm(backends=plugins)

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
    )


@APP.route('/project/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    plugins = anitya.plugins.get_plugin_names()

    form = anitya.forms.ProjectForm(
        backends=plugins,
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
            flask.flash('Project created')
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(err)

        return flask.redirect(
            flask.url_for('project', project_id=project.id)
        )

    return flask.render_template(
        'project_new.html',
        context='Edit',
        current='projects',
        form=form,
        project=project,
        url_aliases=URL_ALIASES,
        regex_aliases=REGEX_ALIASES)


@APP.route('/project/<project_id>/map', methods=['GET', 'POST'])
@login_required
def map_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    form = anitya.forms.MappingForm()

    if form.validate_on_submit():

        try:
            pkg = anitya.lib.map_project(
                SESSION,
                project=project,
                package_name=form.package_name.data,
                distribution=form.distro.data,
                user_mail=flask.g.auth.email,
            )
            #flask.flash('Project created')
            SESSION.commit()
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(err)

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

    project = cnucnuweb.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    package = cnucnuweb.model.Packages.by_id(SESSION, pkg_id)
    if not package:
        flask.abort(404)

    form = cnucnuweb.forms.MappingForm()

    if form.validate_on_submit():
        distro = form.distro.data
        pkgname = form.package_name.data
        version_url = form.version_url.data
        regex = form.regex.data

        cnt = 0
        msgs = []

        distro_obj = cnucnuweb.model.Distro.get(
            SESSION, distro.strip())

        if not distro_obj:
            distro_obj = cnucnuweb.model.Distro.get_or_create(
                SESSION, distro)
            cnucnuweb.log(
                SESSION,
                distro=distro_obj,
                topic='distro.add',
                message=dict(
                    agent=flask.g.auth.email,
                    distro=distro,
                )
            )

        pkg = cnucnuweb.model.Packages.get(
            SESSION, project.id, distro, pkgname)

        topic = 'project.map.update'
        if not pkg:
            topic = 'project.map.new'

        cnucnuweb.model.map_project_distro(
            SESSION, project_id, distro_obj.name, pkgname,
            version_url, regex)

        flask.flash('%s updated' % distro)
        cnucnuweb.log(
            SESSION,
            project=project,
            distro=distro_obj,
            topic=topic,
            message=dict(
                agent=flask.g.auth.email,
                project=project.name,
                distro=distro,
                new=pkgname,
            )
        )

        SESSION.commit()
        return flask.redirect(
            flask.url_for('project', project_id=project_id))

    elif flask.request.method == 'GET':
        form = cnucnuweb.forms.MappingForm(package=package)

    return flask.render_template(
        'mapping.html',
        current='projects',
        project=project,
        package=package,
        form=form,
    )
