#-*- coding: utf-8 -*-

from math import ceil

import flask

import cnucnuweb
import cnucnuweb.model

from cnucnuweb.app import APP, SESSION, login_required, is_admin


@APP.route('/distro/add', methods=['GET', 'POST'])
@login_required
def add_distro():

    if not is_admin():
        flask.abort(405)

    form = cnucnuweb.forms.DistroForm()

    if form.validate_on_submit():
        name = form.name.data

        distro = cnucnuweb.model.Distro(name)

        cnucnuweb.log(
            SESSION,
            distro=distro,
            topic='distro.add',
            message=dict(
                agent=flask.g.auth.email,
                distro=distro.name,
            )
        )

        SESSION.add(distro)
        SESSION.commit()
        flask.flash('Distribution added')
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

    distro = cnucnuweb.model.Distro.by_name(SESSION, distro_name)
    if not distro:
        flask.abort(404)

    if not is_admin():
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

    if not is_admin():
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


@APP.route('/logs')
@login_required
def browse_logs():

    if not is_admin():
        flask.abort(403)

    cnt_logs = cnucnuweb.model.Log.search(SESSION, count=True)

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

    if page is not None and limit is not None and limit != 0:
        page = (page - 1) * limit

    logs = []
    try:
        logs = cnucnuweb.model.Log.search(
            SESSION,
            project_name=project or None,
            from_date=from_date,
            offset=page,
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
