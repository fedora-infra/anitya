#-*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
from math import ceil

from sqlalchemy.exc import SQLAlchemyError

import flask

import cnucnuweb
import cnucnuweb.model

from cnucnuweb.app import APP, SESSION, login_required, load_docs


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


@APP.route('/project/<project_id>')
@APP.route('/project/<project_id>/')
def project(project_id):

    project = cnucnuweb.model.Project.by_id(SESSION, project_id)

    if not project:
        flask.abort(404)

    return flask.render_template(
        'project.html',
        current='project',
        project=project)


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

        project = cnucnuweb.model.Project.get_or_create(
            SESSION,
            name=name,
            homepage=homepage,
        )
        if project.created_on.date() == datetime.today():
            topic = 'project.add'
            message = 'Project created'
        else:
            topic = 'project.add.tried'
            message = 'Project existed already'
        cnucnuweb.log(
            SESSION,
            project=project,
            topic=topic,
            message=dict(
                agent=flask.g.auth.email,
                project=project.name,
            )
        )

        SESSION.commit()
        flask.flash(message)

        return flask.redirect(
            flask.url_for('project', project_id=project.id)
        )

    return flask.render_template(
        'project_new.html',
        context='Add',
        current='Add projects',
        form=form,
        url_aliases=URL_ALIASES,
        regex_aliases=REGEX_ALIASES)


@APP.route('/project/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):

    project = cnucnuweb.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    form = cnucnuweb.forms.ProjectForm()

    if form.validate_on_submit():
        name = form.name.data
        homepage = form.homepage.data

        edit = []
        if name != project.name:
            project.name = name
            edit.append('name')
        if homepage != project.homepage:
            project.homepage = homepage
            edit.append('homepage')

        try:
            if edit:
                cnucnuweb.log(
                    SESSION,
                    project=project,
                    topic='project.edit',
                    message=dict(
                        agent=flask.g.auth.email,
                        project=project.name,
                        fields=edit,
                    )
                )

                SESSION.add(project)
                SESSION.commit()
                message = 'Project edited'
                flask.flash(message)
        except SQLAlchemyError, err:
            SESSION.rollback()
            print err
            flask.flash(
                'Could not edit this project. Is there already a project '
                'with this homepage?', 'errors')

        return flask.redirect(
            flask.url_for('project', project_id=project.id)
        )
    else:
        form = cnucnuweb.forms.ProjectForm(project=project)

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

    project = cnucnuweb.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    form = cnucnuweb.forms.ConfirmationForm()

    if form.validate_on_submit():
        distros = flask.request.form.getlist('distros')
        pkgnames = flask.request.form.getlist('pkgname')
        version_urls = flask.request.form.getlist('version_url')
        regexs = flask.request.form.getlist('regex')

        cnt = 0
        msgs = []
        for distro in distros:
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

            pkgname = pkgnames[cnt].strip()
            version_url = version_urls[cnt].strip()
            regex = regexs[cnt].strip()

            if not distro or not pkgname or not version_url or not regex:
                continue

            else:
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
            cnt += 1

        SESSION.commit()
        return flask.redirect(
            flask.url_for('project', project_id=project_id))

    return flask.render_template(
        'package.html',
        current='projects',
        project=project,
        form=form)
