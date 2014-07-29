# -*- coding: utf-8 -*-

from dateutil import parser
from math import ceil

import flask
from sqlalchemy.exc import SQLAlchemyError

import anitya
import anitya.forms
import anitya.lib.model

from anitya.app import APP, SESSION, login_required, is_admin


@APP.route('/distro/add', methods=['GET', 'POST'])
@login_required
def add_distro():

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.DistroForm()

    if form.validate_on_submit():
        name = form.name.data

        distro = anitya.lib.model.Distro(name)

        anitya.log(
            SESSION,
            distro=distro,
            topic='distro.add',
            message=dict(
                agent=flask.g.auth.email,
                distro=distro.name,
            )
        )

        try:
            SESSION.add(distro)
            SESSION.commit()
            flask.flash('Distribution added')
        except SQLAlchemyError as err:
            flask.flash(
                'Could not add this distro, already exists?', 'error')
        return flask.redirect(
            flask.url_for('distros')
        )

    return flask.render_template(
        'distro_add.html',
        current='distros',
        form=form)


@APP.route('/distro/<distro_name>/edit', methods=['GET', 'POST'])
@login_required
def edit_distro(distro_name):

    distro = anitya.lib.model.Distro.by_name(SESSION, distro_name)
    if not distro:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.DistroForm(obj=distro)

    if form.validate_on_submit():
        name = form.name.data

        if name != distro.name:
            anitya.log(
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

    return flask.render_template(
        'distro_edit.html',
        current='distros',
        distro=distro,
        form=form)


@APP.route('/project/<project_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    project_name = project.name

    form = anitya.forms.ConfirmationForm()
    confirm = flask.request.form.get('confirm', False)

    if form.validate_on_submit():
        if confirm:
            anitya.log(
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
                flask.url_for('project', project_id=project.id))

    return flask.render_template(
        'project_delete.html',
        current='projects',
        project=project,
        form=form)


@APP.route(
    '/project/<project_id>/delete/<distro_name>/<pkg_name>',
    methods=['GET', 'POST'])
@login_required
def delete_project_mapping(project_id, distro_name, pkg_name):

    project = anitya.lib.model.Project.get(SESSION, project_id)
    if not project:
        flask.abort(404)

    distro = anitya.lib.model.Distro.get(SESSION, distro_name)
    if not distro:
        flask.abort(404)

    package = anitya.lib.model.Packages.get(
        SESSION, project.id, distro.name, pkg_name)
    if not package:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.ConfirmationForm()
    confirm = flask.request.form.get('confirm', False)

    if form.validate_on_submit():
        if confirm:
            anitya.log(
                SESSION,
                project=project,
                topic='project.map.remove',
                message=dict(
                    agent=flask.g.auth.email,
                    project=project.name,
                    distro=distro.name,
                )
            )

            SESSION.delete(package)
            SESSION.commit()

            flask.flash('Mapping for %s has been removed' % project.name)
        return flask.redirect(
            flask.url_for('project', project_id=project.id))

    return flask.render_template(
        'regex_delete.html',
        current='projects',
        project=project,
        package=package,
        form=form)


@APP.route('/logs')
@login_required
def browse_logs():

    if not is_admin():
        flask.abort(401)

    cnt_logs = anitya.lib.model.Log.search(SESSION, count=True)

    from_date = flask.request.args.get('from_date', None)
    project = flask.request.args.get('project', None)
    refresh = flask.request.args.get('refresh', False)
    limit = flask.request.args.get('limit', 50)
    page = flask.request.args.get('page', 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    try:
        int(limit)
    except ValueError:
        limit = 50
        flask.flash('Incorrect limit provided, using default', 'errors')

    if from_date:
        try:
            from_date = parser.parse(from_date)
        except (ValueError, TypeError):
            flask.flash(
                'Incorrect from_date provided, using default', 'errors')
            from_date = None

    if from_date:
        from_date = from_date.date()

    offset = 0
    if page is not None and limit is not None and limit != 0:
        offset = (page - 1) * limit

    logs = []
    try:
        logs = anitya.lib.model.Log.search(
            SESSION,
            project_name=project or None,
            from_date=from_date,
            offset=offset,
            limit=limit,
        )
    except Exception, err:
        import logging
        logging.exception(err)
        flask.flash(err, 'errors')

    total_page = int(ceil(cnt_logs / float(limit)))

    return flask.render_template(
        'logs.html',
        current='logs',
        refresh=refresh,
        logs=logs,
        cnt_logs=cnt_logs,
        total_page=total_page,
        page=page,
        project=project or '',
        from_date=from_date or '',
    )
