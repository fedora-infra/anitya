# -*- coding: utf-8 -*-

from math import ceil

from flask_login import login_required, logout_user, current_user
import flask
from sqlalchemy.exc import SQLAlchemyError

from anitya.db import Session, models
from anitya.lib import utilities, exceptions, plugins as anitya_plugins
import anitya


ui_blueprint = flask.Blueprint(
    "anitya_ui", __name__, static_folder="static", template_folder="templates"
)


def get_extended_pattern(pattern):
    """For a given pattern `p` return it so that it looks like `*p*`
    adjusting it accordingly.
    """

    if not pattern.startswith("*"):
        pattern = "*" + pattern
    if not pattern.endswith("*"):
        pattern += "*"
    return pattern


@ui_blueprint.route("/")
def index():
    total = models.Project.all(Session, count=True)
    if current_user.is_authenticated and flask.session.get("next_url", ""):
        next_url = flask.session.get("next_url")
        del flask.session["next_url"]
        return flask.redirect(next_url)
    return flask.render_template("index.html", current="index", total=total)


@ui_blueprint.route("/about")
def about():
    """A backwards-compatibility route for old documentation links"""
    new_path = flask.url_for("anitya_ui.static", filename="docs/index.html")
    return flask.redirect(new_path)


@ui_blueprint.route("/login/", methods=("GET", "POST"))
@ui_blueprint.route("/login", methods=("GET", "POST"))
def login():
    flask.session["next_url"] = flask.request.args.get("next", "/")
    return flask.render_template("login.html")


@ui_blueprint.route("/logout/")
@ui_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect("/")


@ui_blueprint.route("/settings/", methods=("GET", "POST"))
@login_required
def settings():
    """The user's settings, currently only the API token page."""
    return flask.render_template(
        "settings.html", current="settings", form=anitya.forms.TokenForm()
    )


@ui_blueprint.route("/settings/tokens/new", methods=("POST",))
@login_required
def new_token():
    """Create a new API token for the current user."""
    form = anitya.forms.TokenForm()
    if form.validate_on_submit():
        token = models.ApiToken(user=flask.g.user, description=form.description.data)
        Session.add(token)
        Session.commit()
        return flask.redirect(flask.url_for("anitya_ui.settings"))
    else:
        flask.abort(400)


@ui_blueprint.route("/settings/tokens/delete/<token>/", methods=("POST",))
@login_required
def delete_token(token):
    """Delete the API token provided for current user."""
    form = anitya.forms.TokenForm()
    if form.validate_on_submit():
        t = models.ApiToken.query.filter_by(user=flask.g.user, token=token).first()
        if t is None:
            flask.abort(404)
        Session.delete(t)
        Session.commit()
        return flask.redirect(flask.url_for("anitya_ui.settings"))
    else:
        flask.abort(400)


@ui_blueprint.route("/project/<int:project_id>")
@ui_blueprint.route("/project/<int:project_id>/")
def project(project_id):

    project = models.Project.by_id(Session, project_id)

    if not project:
        flask.abort(404)

    return flask.render_template("project.html", current="project", project=project)


@ui_blueprint.route("/project/<project_name>")
@ui_blueprint.route("/project/<project_name>/")
def project_name(project_name):

    page = flask.request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = models.Project.search(Session, pattern=project_name, page=page)
    projects_count = models.Project.search(Session, pattern=project_name, count=True)

    if projects_count == 1:
        return project(projects[0].id)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        "search.html",
        current="projects",
        pattern=project_name,
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page,
    )


@ui_blueprint.route("/projects")
@ui_blueprint.route("/projects/")
def projects():

    page = flask.request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = models.Project.all(Session, page=page)
    projects_count = models.Project.all(Session, count=True)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        "projects.html",
        current="projects",
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page,
    )


@ui_blueprint.route("/projects/updates")
@ui_blueprint.route("/projects/updates/")
@ui_blueprint.route("/projects/updates/<status>")
def projects_updated(status="updated"):

    page = flask.request.args.get("page", 1)
    name = flask.request.args.get("name", None)
    log = flask.request.args.get("log", None)

    try:
        page = int(page)
    except ValueError:
        page = 1

    statuses = ["updated", "failed", "never_updated", "archived"]

    if status not in statuses:
        flask.flash(
            "%s is invalid, you should use one of: %s; using default: "
            "`updated`" % (status, ", ".join(statuses)),
            "errors",
        )
        flask.flash(
            "Returning all the projects regardless of how/if their version "
            "was retrieved correctly"
        )

    projects = models.Project.updated(
        Session, status=status, name=name, log=log, page=page
    )
    projects_count = models.Project.updated(
        Session, status=status, name=name, log=log, count=True
    )

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        "updates.html",
        current="projects",
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page,
        status=status,
        name=name,
        log=log,
    )


@ui_blueprint.route("/logs")
@login_required
def browse_logs():

    refresh = flask.request.args.get("refresh", False)
    page = flask.request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    if page < 1:
        page = 1

    page_obj = models.Project.query.paginate(
        page=page, order_by=models.Project.last_check.desc()
    )

    projects = page_obj.items

    cnt_projects = page_obj.total_items

    total_page = int(ceil(cnt_projects / float(page_obj.items_per_page)))

    return flask.render_template(
        "logs.html",
        current="logs",
        refresh=refresh,
        projects=projects,
        total_page=total_page,
        page=page,
    )


@ui_blueprint.route("/distros")
@ui_blueprint.route("/distros/")
def distros():

    page = flask.request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    distros = models.Distro.all(Session, page=page)
    distros_count = models.Distro.all(Session, count=True)

    total_page = int(ceil(distros_count / float(50)))

    return flask.render_template(
        "distros.html",
        current="distros",
        distros=distros,
        total_page=total_page,
        distros_count=distros_count,
        page=page,
    )


@ui_blueprint.route("/distro/<distroname>")
@ui_blueprint.route("/distro/<distroname>/")
def distro(distroname):

    page = flask.request.args.get("page", 1)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = models.Project.by_distro(Session, distro=distroname, page=page)
    projects_count = models.Project.by_distro(Session, distro=distroname, count=True)

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        "projects.html",
        current="projects",
        projects=projects,
        distroname=distroname,
        total_page=total_page,
        projects_count=projects_count,
        page=page,
    )


@ui_blueprint.route("/distro/add", methods=["GET", "POST"])
@login_required
def add_distro():

    form = anitya.forms.DistroForm()

    if form.validate_on_submit():
        name = form.name.data

        distro = models.Distro(name)

        utilities.publish_message(
            distro=distro.__json__(),
            topic="distro.add",
            message=dict(agent=flask.g.user.username, distro=distro.name),
        )

        try:
            Session.add(distro)
            Session.commit()
            flask.flash("Distribution added")
        except SQLAlchemyError:
            Session.rollback()
            flask.flash("Could not add this distro, already exists?", "error")
        return flask.redirect(flask.url_for("anitya_ui.distros"))

    return flask.render_template(
        "distro_add_edit.html", context="Add", current="distros", form=form
    )


@ui_blueprint.route("/projects/search")
@ui_blueprint.route("/projects/search/")
@ui_blueprint.route("/projects/search/<pattern>")
def projects_search(pattern=None):

    pattern = flask.request.args.get("pattern", pattern) or "*"
    page = flask.request.args.get("page", 1)
    exact = flask.request.args.get("exact", 0)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = models.Project.search(Session, pattern=pattern, page=page)

    if not str(exact).lower() in ["1", "true"]:
        # Extends the search
        for proj in models.Project.search(
            Session, pattern=get_extended_pattern(pattern), page=page
        ):
            if proj not in projects:
                projects.append(proj)
        projects_count = models.Project.search(
            Session, pattern=get_extended_pattern(pattern), count=True
        )
    else:
        projects_count = models.Project.search(Session, pattern=pattern, count=True)

    if projects_count == 1 and projects[0].name == pattern.replace("*", ""):
        flask.flash("Only one result matching with an exact match, redirecting")
        return flask.redirect(
            flask.url_for("anitya_ui.project", project_id=projects[0].id)
        )

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        "search.html",
        current="projects",
        pattern=pattern,
        projects=projects,
        total_page=total_page,
        projects_count=projects_count,
        page=page,
    )


@ui_blueprint.route("/distro/<distroname>/search")
@ui_blueprint.route("/distro/<distroname>/search/")
@ui_blueprint.route("/distro/<distroname>/search/<pattern>")
def distro_projects_search(distroname, pattern=None):

    pattern = flask.request.args.get("pattern", pattern) or "*"
    page = flask.request.args.get("page", 1)
    exact = flask.request.args.get("exact", 0)

    try:
        page = int(page)
    except ValueError:
        page = 1

    projects = models.Project.search(
        Session, pattern=pattern, distro=distroname, page=page
    )

    if not str(exact).lower() in ["1", "true"]:
        # Extends the search
        for proj in models.Project.search(
            Session, pattern=get_extended_pattern(pattern), distro=distroname, page=page
        ):
            if proj not in projects:
                projects.append(proj)
        projects_count = models.Project.search(
            Session,
            pattern=get_extended_pattern(pattern),
            distro=distroname,
            count=True,
        )
    else:
        projects_count = models.Project.search(
            Session, pattern=pattern, distro=distroname, count=True
        )

    if projects_count == 1 and projects[0].name == pattern.replace("*", ""):
        flask.flash("Only one result matching with an exact match, redirecting")
        return flask.redirect(
            flask.url_for("anitya_ui.project", project_id=projects[0].id)
        )

    total_page = int(ceil(projects_count / float(50)))

    return flask.render_template(
        "search.html",
        current="projects",
        pattern=pattern,
        projects=projects,
        distroname=distroname,
        total_page=total_page,
        projects_count=projects_count,
        page=page,
    )


@ui_blueprint.route("/project/new", methods=["GET", "POST"])
@login_required
def new_project():
    """
    View for creating a new project.

    This function accepts GET and POST requests. POST requests can result in
    a HTTP 400 for invalid forms, a HTTP 409 if the request conflicts with an
    existing project, or a HTTP 302 redirect to the new project.
    """
    backend_plugins = anitya_plugins.load_plugins(Session)
    plg_names = [plugin.name for plugin in backend_plugins]
    version_plugins = anitya_plugins.load_plugins(Session, family="versions")
    version_plg_names = [plugin.name for plugin in version_plugins]
    # Get all available distros name
    distros = models.Distro.all(Session)
    distro_names = []
    for distro in distros:
        distro_names.append(distro.name)

    form = anitya.forms.ProjectForm(
        backends=plg_names, version_schemes=version_plg_names, distros=distro_names
    )

    if flask.request.method == "GET":
        form.name.data = flask.request.args.get("name", "")
        form.homepage.data = flask.request.args.get("homepage", "")
        form.backend.data = flask.request.args.get("backend", "")
        form.version_scheme.data = flask.request.args.get("version_scheme", "")
        form.distro.data = flask.request.args.get("distro", "")
        form.package_name.data = flask.request.args.get("package_name", "")
        return flask.render_template(
            "project_new.html",
            context="Add",
            current="Add projects",
            form=form,
            plugins=backend_plugins,
        )
    elif form.validate_on_submit():
        project = None
        try:
            project = utilities.create_project(
                Session,
                name=form.name.data.strip(),
                homepage=form.homepage.data.strip(),
                backend=form.backend.data.strip(),
                version_scheme=form.version_scheme.data.strip(),
                version_url=form.version_url.data.strip() or None,
                version_prefix=form.version_prefix.data.strip() or None,
                pre_release_filter=form.pre_release_filter.data.strip() or None,
                version_filter=form.version_filter.data.strip() or None,
                regex=form.regex.data.strip() or None,
                user_id=flask.g.user.username,
                releases_only=form.releases_only.data,
            )
            Session.commit()

            # Optionally, the user can also map a distro when creating a proj.
            if form.distro.data and form.package_name.data:
                utilities.map_project(
                    Session,
                    project=project,
                    package_name=form.package_name.data,
                    distribution=form.distro.data,
                    user_id=flask.g.user.username,
                )
                Session.commit()

            flask.flash("Project created")
        except exceptions.AnityaException as err:
            flask.flash(str(err))
            return (
                flask.render_template(
                    "project_new.html",
                    context="Add",
                    current="Add projects",
                    form=form,
                    plugins=backend_plugins,
                ),
                409,
            )

        if form.check_release.data is True:
            try:
                utilities.check_project_release(project, Session)
            except exceptions.AnityaException:
                flask.flash("Check failed")

        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project.id))

    return (
        flask.render_template(
            "project_new.html",
            context="Add",
            current="Add projects",
            form=form,
            plugins=backend_plugins,
        ),
        400,
    )


@ui_blueprint.route("/project/<project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id):

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    # Archived project is not editable
    if project.archived:
        flask.abort(404)

    backend_plugins = anitya_plugins.load_plugins(Session)
    plg_names = [plugin.name for plugin in backend_plugins]
    version_plugins = anitya_plugins.load_plugins(Session, family="versions")
    version_plg_names = [plugin.name for plugin in version_plugins]

    form = anitya.forms.ProjectForm(
        backends=plg_names, version_schemes=version_plg_names, obj=project
    )

    if form.validate_on_submit():
        try:
            changes = utilities.edit_project(
                Session,
                project=project,
                name=form.name.data.strip(),
                homepage=form.homepage.data.strip(),
                backend=form.backend.data.strip(),
                version_scheme=form.version_scheme.data.strip(),
                version_pattern=form.version_pattern.data.strip(),
                version_url=form.version_url.data.strip(),
                version_prefix=form.version_prefix.data.strip(),
                pre_release_filter=form.pre_release_filter.data.strip(),
                version_filter=form.version_filter.data.strip(),
                regex=form.regex.data.strip(),
                insecure=form.insecure.data,
                user_id=flask.g.user.username,
                check_release=form.check_release.data,
                releases_only=form.releases_only.data,
            )
            if changes:
                flask.flash("Project edited")
            else:
                flask.flash("Project edited - No changes were made")
            flask.session["justedit"] = True
        except exceptions.AnityaException as err:
            flask.flash(str(err), "errors")

        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project_id))

    return flask.render_template(
        "project_new.html",
        context="Edit",
        current="projects",
        form=form,
        project=project,
        plugins=backend_plugins,
    )


@ui_blueprint.route("/project/<project_id>/flag", methods=["GET", "POST"])
@login_required
def flag_project(project_id):

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    form = anitya.forms.FlagProjectForm(obj=project)

    if form.validate_on_submit():
        try:
            utilities.flag_project(
                Session,
                project=project,
                reason=form.reason.data,
                user_email=flask.g.user.email,
                user_id=flask.g.user.username,
            )
            flask.flash("Project flagged for admin review")
        except exceptions.AnityaException as err:
            flask.flash(str(err), "errors")

        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project.id))

    return flask.render_template(
        "project_flag.html",
        context="Flag",
        current="projects",
        form=form,
        project=project,
    )


@ui_blueprint.route("/project/<project_id>/map", methods=["GET", "POST"])
@login_required
def map_project(project_id):

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    # Get all available distros name
    distros = models.Distro.all(Session)
    distro_names = []
    for distro in distros:
        distro_names.append(distro.name)

    form = anitya.forms.MappingForm(distros=distro_names)

    if flask.request.method == "GET":
        form.package_name.data = flask.request.args.get("package_name", project.name)
        form.distro.data = flask.request.args.get("distro", "")

    if form.validate_on_submit():
        try:
            utilities.map_project(
                Session,
                project=project,
                package_name=form.package_name.data.strip(),
                distribution=form.distro.data.strip(),
                user_id=flask.g.user.username,
            )
            Session.commit()
            flask.flash("Mapping added")
        except exceptions.AnityaInvalidMappingException as err:
            err.link = flask.url_for("anitya_ui.project", project_id=err.project_id)
            flask.flash(err.message, "error")
        except exceptions.AnityaException as err:
            flask.flash(str(err), "error")

        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project.id))

    return flask.render_template(
        "mapping.html", current="projects", project=project, form=form
    )


@ui_blueprint.route("/project/<project_id>/map/<pkg_id>", methods=["GET", "POST"])
@login_required
def edit_project_mapping(project_id, pkg_id):

    project = models.Project.get(Session, project_id)
    if not project:
        flask.abort(404)

    package = models.Packages.by_id(Session, pkg_id)
    if not package:
        flask.abort(404)

    # Get all available distros name
    distros = models.Distro.all(Session)
    distro_names = []
    for distro in distros:
        distro_names.append(distro.name)

    form = anitya.forms.MappingForm(
        package_name=package.package_name,
        distro=package.distro_name,
        distros=distro_names,
    )

    if form.validate_on_submit():

        try:
            utilities.map_project(
                Session,
                project=project,
                package_name=form.package_name.data,
                distribution=form.distro.data,
                user_id=flask.g.user.username,
                old_package_name=package.package_name,
                old_distro_name=package.distro_name,
            )

            Session.commit()
            flask.flash("Mapping edited")
        except exceptions.AnityaInvalidMappingException as err:
            err.link = flask.url_for("anitya_ui.project", project_id=err.project_id)
            flask.flash(err.message, "error")
        except exceptions.AnityaException as err:
            flask.flash(str(err), "error")

        return flask.redirect(flask.url_for("anitya_ui.project", project_id=project_id))

    return flask.render_template(
        "mapping.html", current="projects", project=project, package=package, form=form
    )


def format_examples(examples):
    """ Return the plugins examples as HTML links. """
    output = ""
    if examples:
        for cnt, example in enumerate(examples):
            if cnt > 0:
                output += " <br /> "
            output += "<a href='%(url)s'>%(url)s</a> " % ({"url": example})

    return output


def context_class(category):
    """ Return bootstrap context class for a given category. """
    values = {"message": "default", "error": "danger", "info": "info"}
    return values.get(category, "warning")


ui_blueprint.add_app_template_filter(format_examples, name="format_examples")
ui_blueprint.add_app_template_filter(context_class, name="context_class")
