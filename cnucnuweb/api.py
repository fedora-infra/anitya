#-*- coding: utf-8 -*-

import flask

from cnucnu.package_list import Package

import cnucnuweb
import cnucnuweb.model

from cnucnuweb.app import APP, SESSION


@APP.route('/api/projects')
@APP.route('/api/projects/')
def api_projects():

    pattern = flask.request.args.get('pattern', None)

    if pattern and not '*' in pattern:
        pattern += '*'

    if pattern:
        project_objs = cnucnuweb.model.Project.search(
            SESSION, pattern=pattern)
    else:
        project_objs = cnucnuweb.model.Project.all(SESSION)

    projects = [project.__json__() for project in project_objs]

    output = {
        'total': len(projects),
        'projects': projects
    }

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@APP.route('/api/projects/wiki')
@APP.route('/api/projects/wiki/')
def api_projects_list():

    project_objs = cnucnuweb.model.Project.all(SESSION)

    projects = []
    for project in project_objs:
        tmp = '* {name} {regex} {version_url}'.format(
            name=project.name,
            regex=project.regex,
            version_url=project.version_url)
        projects.append(tmp)

    return flask.Response(
        "\n".join(projects),
        content_type="text/plain;charset=UTF-8"
    )


@APP.route('/api/projects/names')
@APP.route('/api/projects/names/')
def api_projects_names():

    pattern = flask.request.args.get('pattern', None)

    if pattern and not '*' in pattern:
        pattern += '*'

    if pattern:
        project_objs = cnucnuweb.model.Project.search(
            SESSION, pattern=pattern)
    else:
        project_objs = cnucnuweb.model.Project.all(SESSION)

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

    name = flask.request.form.get('name', None)
    url = flask.request.form.get('url', None)
    regex = flask.request.form.get('regex', None)
    httpcode = 200

    if not name or not url or not regex:
        errors = []
        if not name:
            errors.append('No name specified')
        if not url:
            errors.append('No url specified')
        if not regex:
            errors.append('No regex specified')
        output = {'output': 'notok', 'error': errors}
        httpcode = 400
    else:
        try:
            pkg = Package(name=name, url=url, regex=regex)
            versions = pkg.upstream_versions
            latest_version = pkg.latest_upstream
        except Exception as err:
            output = {'output': 'notok', 'error': err.message}
            httpcode = 400
        else:
            output = {
                'name': pkg.name,
                'url': pkg.url,
                'regex': pkg.regex,
                'raw_url': pkg.raw_url,
                'raw_regex': pkg.raw_regex,
                'versions': versions,
                'latest_version': latest_version,
            }

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@APP.route('/api/project/<project_name>', methods=['GET'])
@APP.route('/api/project/<project_name>/', methods=['GET'])
def api_get_project(project_name):

    project = cnucnuweb.model.Project.get(SESSION, name=project_name)

    if not project:
        output = {'output': 'notok', 'error': 'no such project'}
        httpcode = 404
    else:
        output = project.__json__()
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@APP.route('/api/project/<distro>/<package_name>', methods=['GET'])
@APP.route('/api/project/<distro>/<package_name>/', methods=['GET'])
def api_get_project_distro(distro, package_name):

    package = cnucnuweb.model.Packages.by_package_name_distro(
        SESSION, package_name, distro)

    if not package:
        output = {
            'output': 'notok',
            'error': 'No package "%s" found in distro "%s"' % (
                package_name, distro)}
        httpcode = 404

    else:
        project = cnucnuweb.model.Project.get(
            SESSION, name=package.project.name)

        if not project:
            output = {'output': 'notok', 'error': 'no such project'}
            httpcode = 404
        else:
            output = project.__json__()
            httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
