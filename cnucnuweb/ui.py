#-*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
from math import ceil

import flask

import cnucnuweb
import cnucnuweb.model

from cnucnuweb.app import APP, SESSION, login_required


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
            project=project,
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
                project=project,
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
        project=project,
        url_aliases=URL_ALIASES,
        regex_aliases=REGEX_ALIASES)


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
