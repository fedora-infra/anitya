#-*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
from math import ceil

import flask

import anitya
import anitya.lib
import anitya.lib.model

from anitya.app import APP, SESSION, PLUGINS, login_required, load_docs


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

    versions_known = True
    for pkg in project.packages:
        if pkg.regex and not pkg.version:
            versions_known = False
            break

    return flask.render_template(
        'project.html',
        current='project',
        project=project,
        versions_known=versions_known,
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

    form = cnucnuweb.forms.ProjectForm(backends=PLUGINS)

    if form.validate_on_submit():
        try:
            project = anitya.lib.create_project(
                SESSION,
                name=form.name.data,
                homepage=form.homepage.data,
                backend=form.backend.data,
                version_url=form.version_url.data,
                regex=form.regex.data,
            )
            topic = 'project.add'
            message = 'Project created'
        except AnityaException:
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

    form = cnucnuweb.forms.MappingForm()

    if form.validate_on_submit():
        distro = form.distro.data
        pkgname = form.package_name.data
        version_url = form.version_url.data
        regex = form.regex.data

        print distro, pkgname, version_url, regex

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
            SESSION,
            project_id=project.id,
            distro_name=distro_obj.name,
            pkg_name=pkgname,
            version_url=version_url,
            regex=regex)

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
            flask.url_for('project', project_id=project.id))

    return flask.render_template(
        'mapping.html',
        current='projects',
        project=project,
        form=form,
        url_aliases=URL_ALIASES,
        regex_aliases=REGEX_ALIASES,
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
        url_aliases=URL_ALIASES,
        regex_aliases=REGEX_ALIASES,
        )
