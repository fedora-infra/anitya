# -*- coding: utf-8 -*-

from dateutil import parser
from math import ceil
import logging

import flask

from anitya.lib import utilities
from anitya.db import models, Session
import anitya
import anitya.forms

from anitya.ui import login_required, ui_blueprint


_log = logging.getLogger(__name__)


def is_admin(user=None):
    """Check if the provided user, or the user logged in are recognized
    as being admins.
    """
    user = user or flask.g.user
    if user.is_authenticated:
        return user.is_admin


@ui_blueprint.route("/distro/<distro_name>/edit", methods=["GET", "POST"])
@login_required
def edit_distro(distro_name):

    distro = models.Distro.by_name(Session, distro_name)
    if not distro:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.DistroForm(obj=distro)

    if form.validate_on_submit():
        name = form.name.data

        if name != distro.name:
            utilities.publish_message(
                distro=distro.__json__(),
                topic="distro.edit",
                message=dict(agent=flask.g.user.username, old=distro.name, new=name),
            )

            distro.name = name

            Session.add(distro)
            Session.commit()
            message = "Distribution edited"
            flask.flash(message)
        return flask.redirect(flask.url_for("anitya_ui.distros"))

    return flask.render_template(
        "distro_add_edit.html",
        context="Edit",
        current="distros",
        distro=distro,
        form=form,
    )


@ui_blueprint.route("/distro/<distro_name>/delete", methods=["GET", "POST"])
@login_required
def delete_distro(distro_name):
    """ Delete a distro """

    distro = models.Distro.by_name(Session, distro_name)
    if not distro:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.ConfirmationForm()

    if form.validate_on_submit():
        utilities.publish_message(
            distro=distro.__json__(),
            topic="distro.remove",
            message=dict(agent=flask.g.user.username, distro=distro.name),
        )

        Session.delete(distro)
        Session.commit()
        flask.flash("Distro %s has been removed" % distro_name)
        return flask.redirect(flask.url_for("anitya_ui.distros"))

    return flask.render_template(
        "distro_delete.html", current="distros", distro=distro, form=form
    )


@ui_blueprint.route("/project/<project_id>/delete", methods=["GET", "POST"])
@login_required
def delete_project(project_id):

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    project_name = project.name

    form = anitya.forms.ConfirmationForm()
    confirm = flask.request.form.get("confirm", False)

    if form.validate_on_submit():
        if confirm:
            utilities.publish_message(
                project=project.__json__(),
                topic="project.remove",
                message=dict(agent=flask.g.user.username, project=project.name),
            )

            for version in project.versions_obj:
                Session.delete(version)

            Session.delete(project)
            Session.commit()
            flask.flash("Project %s has been removed" % project_name)
            return flask.redirect(flask.url_for("anitya_ui.projects"))
        else:
            return flask.redirect(
                flask.url_for("anitya_ui.project", project_id=project.id)
            )

    return flask.render_template(
        "project_delete.html", current="projects", project=project, form=form
    )


@ui_blueprint.route(
    "/project/<project_id>/archive/set/<state>", methods=["GET", "POST"]
)
@login_required
def set_project_archive_state(project_id, state):

    if not is_admin():
        flask.abort(401)

    if state not in ("true", "false"):
        flask.abort(422)

    project = models.Project.get(Session, project_id)
    archive = False
    if state == "true":
        archive = True

    if not project:
        flask.abort(404)

    form = anitya.forms.ConfirmationForm()
    confirm = flask.request.form.get("confirm", False)

    if form.validate_on_submit():
        if confirm:
            try:
                utilities.edit_project(
                    Session,
                    project=project,
                    name=project.name,
                    homepage=project.homepage,
                    backend=project.backend,
                    version_scheme=project.version_scheme,
                    version_pattern=project.version_pattern,
                    version_url=project.version_url,
                    version_prefix=project.version_prefix,
                    pre_release_filter=project.pre_release_filter,
                    version_filter=project.pre_release_filter,
                    regex=project.regex,
                    insecure=project.insecure,
                    releases_only=project.releases_only,
                    archived=archive,
                    user_id=flask.g.user.username,
                )
                if bool(archive):
                    flask.flash("Project '{0}' archived".format(project.name))
                else:
                    flask.flash(
                        "Project '{0}' is no longer archived".format(project.name)
                    )
            except anitya.lib.exceptions.AnityaException as err:
                flask.flash(str(err), "errors")

        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project.id))

    return flask.render_template(
        "project_archive.html",
        current="projects",
        project=project,
        form=form,
        archive=archive,
    )


@ui_blueprint.route(
    "/project/<project_id>/delete/<distro_name>/<pkg_name>", methods=["GET", "POST"]
)
@login_required
def delete_project_mapping(project_id, distro_name, pkg_name):

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    distro = models.Distro.get(Session, distro_name)
    if not distro:
        flask.abort(404)

    package = models.Packages.get(Session, project.id, distro.name, pkg_name)
    if not package:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.ConfirmationForm()
    confirm = flask.request.form.get("confirm", False)

    if form.validate_on_submit():
        if confirm:
            utilities.publish_message(
                project=project.__json__(),
                topic="project.map.remove",
                message=dict(
                    agent=flask.g.user.username,
                    project=project.name,
                    distro=distro.name,
                ),
            )

            Session.delete(package)
            Session.commit()

            flask.flash("Mapping for %s has been removed" % project.name)
        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project.id))

    return flask.render_template(
        "regex_delete.html",
        current="projects",
        project=project,
        package=package,
        form=form,
    )


@ui_blueprint.route("/project/<project_id>/delete/<version>", methods=["GET", "POST"])
@login_required
def delete_project_version(project_id, version):

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    version_obj = None
    for vers in project.versions_obj:
        if version == vers.version:
            version_obj = vers
            break

    if version_obj is None:
        flask.abort(
            404, "Version %s not found for project %s" % (version, project.name)
        )

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.ConfirmationForm()
    confirm = flask.request.form.get("confirm", False)

    if form.validate_on_submit():
        if confirm:
            utilities.publish_message(
                project=project.__json__(),
                topic="project.version.remove",
                message=dict(
                    agent=flask.g.user.username, project=project.name, version=version
                ),
            )

            # Delete the record of the version for this project
            Session.delete(version_obj)
            # Adjust the latest_version if needed
            sorted_versions = project.get_sorted_version_objects()
            if len(sorted_versions) > 1 and sorted_versions[0].version == version:
                project.latest_version = sorted_versions[1].parse()
                Session.add(project)
            elif len(sorted_versions) == 1:
                project.latest_version = None
                Session.add(project)
            Session.commit()

            flask.flash("Version for %s has been removed" % version)
        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project.id))

    return flask.render_template(
        "version_delete.html",
        current="projects",
        project=project,
        version=version,
        form=form,
    )


@ui_blueprint.route("/project/<project_id>/delete/versions", methods=["GET", "POST"])
@login_required
def delete_project_versions(project_id):
    """
    Delete all versions on the project.
    """

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    if not is_admin():
        flask.abort(401)

    form = anitya.forms.ConfirmationForm()
    confirm = flask.request.form.get("confirm", False)

    if form.validate_on_submit():
        if confirm:
            for version in project.versions_obj:
                # Delete the record of the version for this project
                Session.delete(version)

                utilities.publish_message(
                    project=project.__json__(),
                    topic="project.version.remove",
                    message=dict(
                        agent=flask.g.user.username,
                        project=project.name,
                        version=str(version),
                    ),
                )

            project.latest_version = None
            Session.add(project)
            Session.commit()

            flask.flash("All versions were removed")
        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project.id))

    return flask.render_template(
        "project_versions_delete.html",
        current="projects",
        project=project,
        form=form,
    )


@ui_blueprint.route("/flags")
@login_required
def browse_flags():

    if not is_admin():
        flask.abort(401)

    from_date = flask.request.args.get("from_date", None)
    state = flask.request.args.get("state", "open")
    project = flask.request.args.get("project", None)
    flags_for_user = flask.request.args.get("user", None)
    refresh = flask.request.args.get("refresh", False)
    limit = flask.request.args.get("limit", 50)
    page = flask.request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    try:
        int(limit)
    except ValueError:
        limit = 50
        flask.flash("Incorrect limit provided, using default", "errors")

    if from_date:
        try:
            from_date = parser.parse(from_date)
        except (ValueError, TypeError):
            flask.flash("Incorrect from_date provided, using default", "errors")
            from_date = None

    if from_date:
        from_date = from_date.date()

    offset = 0
    if page is not None and limit is not None and limit != 0:
        offset = (page - 1) * limit

    flags = []

    try:
        flags = models.ProjectFlag.search(
            Session,
            project_name=project or None,
            state=state or None,
            from_date=from_date,
            user=flags_for_user or None,
            offset=offset,
            limit=limit,
        )

        cnt_flags = models.ProjectFlag.search(
            Session,
            project_name=project or None,
            state=state or None,
            from_date=from_date,
            user=flags_for_user or None,
            count=True,
        )
    except Exception as err:
        _log.exception(err)
        flask.flash(err, "errors")

    total_page = int(ceil(cnt_flags / float(limit)))

    form = anitya.forms.ConfirmationForm()

    return flask.render_template(
        "flags.html",
        current="flags",
        refresh=refresh,
        flags=flags,
        cnt_flags=cnt_flags,
        total_page=total_page,
        form=form,
        page=page,
        project=project or "",
        from_date=from_date or "",
        flags_for_user=flags_for_user or "",
        state=state or "",
    )


@ui_blueprint.route("/flags/<flag_id>/set/<state>", methods=["POST"])
@login_required
def set_flag_state(flag_id, state):

    if not is_admin():
        flask.abort(401)

    if state not in ("open", "closed"):
        flask.abort(422)

    flag = models.ProjectFlag.get(Session, flag_id)

    if not flag:
        flask.abort(404)

    form = anitya.forms.ConfirmationForm()

    if form.validate_on_submit():
        try:
            utilities.set_flag_state(
                Session, flag=flag, state=state, user_id=flask.g.user.username
            )
            flask.flash("Flag {0} set to {1}".format(flag.id, state))
        except anitya.lib.exceptions.AnityaException as err:
            flask.flash(str(err), "errors")

    return flask.redirect(flask.url_for("anitya_ui.browse_flags"))


@ui_blueprint.route("/users", methods=["GET"])
@login_required
def browse_users():

    if not is_admin():
        flask.abort(401)

    user_id = flask.request.args.get("user_id", None)
    username = flask.request.args.get("username", None)
    email = flask.request.args.get("email", None)
    admin = flask.request.args.get("admin", None)
    active = flask.request.args.get("active", None)
    limit = flask.request.args.get("limit", 50)
    page = flask.request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    if admin:
        if admin.upper() == "TRUE":
            admin = True
        elif admin.upper() == "FALSE":
            admin = False
        else:
            admin = None

    if active:
        if active.upper() == "TRUE":
            active = True
        elif active.upper() == "FALSE":
            active = False
        else:
            active = None

    try:
        limit = int(limit)
    except ValueError:
        limit = 50
        flask.flash("Incorrect limit provided, using default", "errors")

    offset = 0
    if page is not None and limit is not None and limit > 0:
        offset = (page - 1) * limit

    users = []
    cnt_users = 0
    try:
        users_query = Session.query(models.User)

        if user_id:
            users_query = users_query.filter_by(id=user_id)

        if username:
            users_query = users_query.filter_by(username=username)

        if email:
            users_query = users_query.filter_by(email=email)

        if admin is not None:
            users_query = users_query.filter_by(admin=admin)

        if active is not None:
            users_query = users_query.filter_by(active=active)

        if offset > 0:
            users_query = users_query.offset(offset)
        if limit > 0:
            users_query = users_query.limit(limit)

        users = users_query.all()
        cnt_users = users_query.count()
    except Exception as err:
        _log.exception(err)
        flask.flash(err, "errors")

    try:
        total_page = int(ceil(cnt_users / float(limit)))
    except ZeroDivisionError:
        total_page = 1

    form = anitya.forms.ConfirmationForm()

    return flask.render_template(
        "users.html",
        current="users",
        users=users,
        cnt_users=cnt_users,
        total_page=total_page,
        form=form,
        page=page,
        username=username or "",
        email=email or "",
        user_id=user_id or "",
        admin=admin,
        active=active,
    )


@ui_blueprint.route("/users/<user_id>/admin/<state>", methods=["POST"])
@login_required
def set_user_admin_state(user_id, state):

    if not is_admin():
        flask.abort(401)

    if state.upper() == "TRUE":
        state = True
    elif state.upper() == "FALSE":
        state = False
    else:
        flask.abort(422)

    try:
        user = Session.query(models.User).filter(models.User.id == user_id).one()
    except Exception as err:
        _log.exception(err)
        user = None

    if not user:
        flask.abort(404)

    form = anitya.forms.ConfirmationForm()

    if form.validate_on_submit():
        try:
            user.admin = state
            Session.add(user)
            Session.commit()
            if state:
                flask.flash("User {0} is now admin".format(user.username))
            else:
                flask.flash("User {0} is not admin anymore".format(user.username))
        except Exception as err:
            _log.exception(err)
            flask.flash(str(err), "errors")
            Session.rollback()

    return flask.redirect(flask.url_for("anitya_ui.browse_users"))


@ui_blueprint.route("/users/<user_id>/active/<state>", methods=["POST"])
@login_required
def set_user_active_state(user_id, state):

    if not is_admin():
        flask.abort(401)

    if state.upper() == "TRUE":
        state = True
    elif state.upper() == "FALSE":
        state = False
    else:
        flask.abort(422)

    try:
        user = Session.query(models.User).filter(models.User.id == user_id).one()
    except Exception as err:
        _log.exception(err)
        user = None

    if not user:
        flask.abort(404)

    form = anitya.forms.ConfirmationForm()

    if form.validate_on_submit():
        try:
            user.active = state
            Session.add(user)
            Session.commit()
            if state:
                flask.flash("User {0} is no longer banned".format(user.username))
            else:
                flask.flash("User {0} is banned".format(user.username))
        except Exception as err:
            _log.exception(err)
            flask.flash(str(err), "errors")
            Session.rollback()

    return flask.redirect(flask.url_for("anitya_ui.browse_users"))
