# -*- coding: utf-8 -*-

import flask

import anitya
import anitya.lib.plugins
import anitya.lib.model

from anitya.app import APP, SESSION


@APP.route('/api/projects/')
@APP.route('/api/projects')
def api_projects():

    pattern = flask.request.args.get('pattern', None)

    if pattern and '*' not in pattern:
        pattern += '*'

    if pattern:
        project_objs = anitya.lib.model.Project.search(
            SESSION, pattern=pattern)
    else:
        project_objs = anitya.lib.model.Project.all(SESSION)

    projects = [project.__json__() for project in project_objs]

    output = {
        'total': len(projects),
        'projects': projects
    }

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@APP.route('/api/projects/wiki/')
@APP.route('/api/projects/wiki')
def api_projects_list():

    project_objs = anitya.lib.model.Project.all(SESSION)

    projects = []
    for project in project_objs:
        for package in project.packages:
            tmp = '* {name} {regex} {version_url}'.format(
                name=package.package_name,
                regex=project.regex,
                version_url=project.version_url)
            projects.append(tmp)

    return flask.Response(
        "\n".join(projects),
        content_type="text/plain;charset=UTF-8"
    )


@APP.route('/api/projects/names/')
@APP.route('/api/projects/names')
def api_projects_names():

    pattern = flask.request.args.get('pattern', None)

    if pattern and '*' not in pattern:
        pattern += '*'

    if pattern:
        project_objs = anitya.lib.model.Project.search(
            SESSION, pattern=pattern)
    else:
        project_objs = anitya.lib.model.Project.all(SESSION)

    projects = [project.name for project in project_objs]

    output = {
        'total': len(projects),
        'projects': projects
    }

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@APP.route('/api/version/', methods=['POST'])
def api_get_version():

    project_id = flask.request.form.get('id', None)
    httpcode = 200

    if not project_id:
        errors = []
        if not project_id:
            errors.append('No project id specified')
        output = {'output': 'notok', 'error': errors}
        httpcode = 400
    else:

        project = anitya.lib.model.Project.get(
            SESSION, project_id=project_id)

        if not project:
            output = {'output': 'notok', 'error': 'No such project'}
            httpcode = 404
        else:
            try:
                anitya.check_release(project, SESSION)
                output = project.__json__()
            except anitya.lib.exceptions.AnityaException as err:
                output = {'output': 'notok', 'error': [str(err)]}
                httpcode = 400

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@APP.route('/api/project/<project_id>/', methods=['GET'])
@APP.route('/api/project/<project_id>', methods=['GET'])
def api_get_project(project_id):

    project = anitya.lib.model.Project.get(SESSION, project_id=project_id)

    if not project:
        output = {'output': 'notok', 'error': 'no such project'}
        httpcode = 404
    else:
        output = project.__json__()
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@APP.route('/api/project/<distro>/<package_name>/', methods=['GET'])
@APP.route('/api/project/<distro>/<package_name>', methods=['GET'])
def api_get_project_distro(distro, package_name):

    package = anitya.lib.model.Packages.by_package_name_distro(
        SESSION, package_name, distro)

    if not package:
        output = {
            'output': 'notok',
            'error': 'No package "%s" found in distro "%s"' % (
                package_name, distro)}
        httpcode = 404

    else:
        project = anitya.lib.model.Project.get(
            SESSION, project_id=package.project.id)

        output = project.__json__()
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
