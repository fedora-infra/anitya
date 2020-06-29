# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2017-2020  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""
This module provides Anitya's HTTP API.
"""

import flask

from anitya.db import Session, models
from anitya.lib import utilities
import anitya
import anitya.lib.plugins


api_blueprint = flask.Blueprint("anitya_apiv1", __name__)


@api_blueprint.route("/api/")
@api_blueprint.route("/api")
def api():
    """
    Retrieve the HTML information page.

    :deprecated: in Anitya 0.12 in favor of simple Sphinx documentation.
    :statuscode 302: A redirect to the HTML documentation.
    """
    new_url = flask.url_for("static", filename="docs/api.html")
    return flask.redirect(new_url)


@api_blueprint.route("/api/version/")
@api_blueprint.route("/api/version")
def api_version():
    """
    Display the api version information.

    ::

        /api/version

    Accepts GET queries only.

    Sample response:

    ::

        {
          "version": "1.0"
        }

    """
    return flask.jsonify({"version": anitya.__api_version__})


@api_blueprint.route("/api/projects/")
@api_blueprint.route("/api/projects")
def api_projects():
    """
    Lists all the projects registered in Anitya.

    This API accepts GET query strings::

        /api/projects

        /api/projects/?pattern=<pattern>

        /api/projects/?pattern=py*

        /api/projects/?homepage=<homepage>

        /api/projects/?homepage=https%3A%2F%2Fpypi.python.org%2Fpypi%2Fansi2html

    Accepts GET queries only.

    :kwarg pattern: pattern to use to restrict the list of projects returned.

    :kwarg homepage: upstream homepage to use to restrict the list of projects
                     returned.

    The ``pattern`` and ``homepage`` arguments are mutually exclusive and
    cannot be combined.  You can query for packages by a pattern **or** you can
    query by their upstream homepage, but not both.

    Sample response::

      {
        "projects": [
          {
            "backend": "custom",
            "created_on": 1409917222.0,
            "homepage": "https://www.finnie.org/software/2ping/",
            "id": 2,
            "name": "2ping",
            "regex": null,
            "updated_on": 1414400794.0,
            "version": "2.1.1",
            "version_url": "https://www.finnie.org/software/2ping",
            "versions": [
              "2.1.1"
            ]
          },
          {
            "backend": "custom",
            "created_on": 1409917223.0,
            "homepage": "https://www.3proxy.ru/download/",
            "id": 3,
            "name": "3proxy",
            "regex": null,
            "updated_on": 1415115096.0,
            "version": "0.7.1.1",
            "version_url": "https://www.3proxy.ru/download/",
            "versions": [
              "0.7.1.1"
            ]
          }
        ],
        "total": 2
      }

    """

    pattern = flask.request.args.get("pattern", None)
    homepage = flask.request.args.get("homepage", None)
    distro = flask.request.args.get("distro", None)

    if pattern and homepage:
        err = "pattern and homepage are mutually exclusive.  Specify only one."
        output = {"output": "notok", "error": [err]}
        jsonout = flask.jsonify(output)
        jsonout.status_code = 400
        return jsonout

    if homepage is not None:
        project_objs = models.Project.by_homepage(Session, homepage)
    elif pattern or distro:
        if pattern and "*" not in pattern:
            pattern += "*"
        project_objs = models.Project.search(Session, pattern=pattern, distro=distro)
    else:
        project_objs = models.Project.all(Session)

    projects = [project.__json__() for project in project_objs]

    output = {"total": len(projects), "projects": projects}

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@api_blueprint.route("/api/packages/wiki/")
@api_blueprint.route("/api/packages/wiki")
def api_packages_wiki_list():
    """
    List all packages in mediawiki format.

    :deprecated: in Anitya 0.12 due to lack of pagination resulting in
        incredibly poor performance.

    Lists all the packages registered in anitya using the format of the
    old wiki page. If a project is present multiple times on different
    distribution, it will be shown multiple times.

    ::

        /api/packages/wiki

    Accepts GET queries only.

    Sample response::

      * 2ping None https://www.finnie.org/software/2ping
      * 3proxy None https://www.3proxy.ru/download/
    """

    project_objs = models.Project.all(Session)

    projects = []
    for project in project_objs:
        for package in project.packages:
            tmp = "* {name} {regex} {version_url}".format(
                name=package.package_name,
                regex=project.regex,
                version_url=project.version_url,
            )
            projects.append(tmp)

    return flask.Response("\n".join(projects), content_type="text/plain;charset=UTF-8")


@api_blueprint.route("/api/projects/names/")
@api_blueprint.route("/api/projects/names")
def api_projects_names():
    """
    Lists the names of all the projects registered in anitya.

    :query str pattern: pattern to use to restrict the list of names returned.
    :statuscode 200: Returned in all cases.

    **Example request**:

    .. sourcecode:: http

        GET /api/projects/names?pattern=requests* HTTP/1.1
        Accept: application/json
        Accept-Encoding: gzip, deflate
        Connection: keep-alive
        Host: release-monitoring.org
        User-Agent: HTTPie/0.9.4


    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Length: 248
        Content-Type: application/json

        {
            "projects": [
                "requests",
                "Requests",
                "requests-aws",
                "requestsexceptions",
                "requests-file",
                "requests-ftp",
                "requests-mock",
                "requests-ntlm",
                "requests-oauthlib",
                "requests-toolbelt"
            ],
            "total": 10
        }
    """

    pattern = flask.request.args.get("pattern", None)

    if pattern and "*" not in pattern:
        pattern += "*"

    if pattern:
        project_objs = models.Project.search(Session, pattern=pattern)
    else:
        project_objs = models.Project.all(Session)

    projects = [project.name for project in project_objs]

    output = {"total": len(projects), "projects": projects}

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@api_blueprint.route("/api/distro/names/")
@api_blueprint.route("/api/distro/names")
def api_distro_names():
    """
    Lists the names of all the distributions registered in anitya.

    :query pattern: pattern to use to restrict the list of distributions returned.

    **Example request**:

    .. sourcecode:: http

        GET /api/distro/names/?pattern=F* HTTP/1.1
        Accept: application/json
        Accept-Encoding: gzip, deflate
        Connection: keep-alive
        Host: release-monitoring.org
        User-Agent: HTTPie/0.9.4


    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Length: 79
        Content-Type: application/json

        {
            "distro": [
                "Fedora",
                "Fedora EPEL",
                "FZUG"
            ],
            "total": 3
        }
    """

    pattern = flask.request.args.get("pattern", None)

    if pattern and "*" not in pattern:
        pattern += "*"

    if pattern:
        distro_objs = models.Distro.search(Session, pattern=pattern)
    else:
        distro_objs = models.Distro.all(Session)

    distros = [distro.name for distro in distro_objs]

    output = {"total": len(distros), "distro": distros}

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@api_blueprint.route("/api/version/get", methods=["POST"])
def api_get_version():
    """
    Forces anitya to retrieve new versions available from a project
    upstream.

    ::

        /api/version/get

    Accepts POST queries only.

    :arg id: the identifier of the project in anitya.

    Sample response:

    ::

      {
        "versions": [
          "2.7"
        ]
      }

    Sample error response:

    ::

      {
        "output": "notok",
        "error": "Error happened."
      }
    """

    project_id = flask.request.form.get("id", None)
    test = flask.request.form.get("test", False)
    httpcode = 200

    if not project_id:
        errors = []
        if not project_id:
            errors.append("No project id specified")
        output = {"output": "notok", "error": errors}
        httpcode = 400
    else:

        project = models.Project.get(Session, project_id=project_id)

        if not project:
            output = {"output": "notok", "error": "No such project"}
            httpcode = 404
        else:
            try:
                versions = utilities.check_project_release(project, Session, test=test)
                if versions:
                    output = {"versions": versions}
                else:
                    output = {"versions": []}
            except anitya.lib.exceptions.AnityaException as err:
                output = {"output": "notok", "error": [str(err)]}
                httpcode = 400

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@api_blueprint.route("/api/project/<int:project_id>/", methods=["GET"])
@api_blueprint.route("/api/project/<int:project_id>", methods=["GET"])
def api_get_project(project_id):
    """
    Retrieves a specific project using its identifier in anitya.

    ::

        /api/project/<project_id>

    Accepts GET queries only.

    :arg project_id: the identifier of the project in anitya.

    Sample response:

    ::

      {
        "backend": "custom",
        "created_on": 1409917222.0,
        "homepage": "https://www.finnie.org/software/2ping/",
        "id": 2,
        "name": "2ping",
        "packages": [
          {
            "distro": "Fedora",
            "package_name": "2ping"
          }
        ],
        "regex": null,
        "updated_on": 1414400794.0,
        "version": "2.1.1",
        "version_url": "https://www.finnie.org/software/2ping",
        "versions": [
          "2.1.1"
        ]
      }

    """

    project = models.Project.get(Session, project_id=project_id)

    if not project:
        output = {"output": "notok", "error": "no such project"}
        httpcode = 404
    else:
        output = project.__json__(detailed=True)
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@api_blueprint.route("/api/project/<distro>/<path:package_name>/", methods=["GET"])
@api_blueprint.route("/api/project/<distro>/<path:package_name>", methods=["GET"])
def api_get_project_distro(distro, package_name):
    """
    Retrieves a project in a distribution via the name of the distribution
    and the name of the package in said distribution.

    ::

        /api/project/<distro>/<package_name>

    Accepts GET queries only.

    :arg distro: the name of the distribution (case insensitive).
    :arg package_name: the name of the package in the distribution specified.

    Sample response:

    ::

      {
        "backend": "custom",
        "created_on": 1409917222.0,
        "homepage": "https://www.finnie.org/software/2ping/",
        "id": 2,
        "name": "2ping",
        "packages": [
          {
            "distro": "Fedora",
            "package_name": "2ping"
          }
        ],
        "regex": null,
        "updated_on": 1414400794.0,
        "version": "2.1.1",
        "version_url": "https://www.finnie.org/software/2ping",
        "versions": [
          "2.1.1"
        ]
      }

    """
    package_name = package_name.rstrip("/")

    package = models.Packages.by_package_name_distro(Session, package_name, distro)

    if not package:
        output = {
            "output": "notok",
            "error": 'No package "%s" found in distro "%s"' % (package_name, distro),
        }
        httpcode = 404

    else:
        project = models.Project.get(Session, project_id=package.project.id)

        output = project.__json__(detailed=True)
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@api_blueprint.route("/api/by_ecosystem/<ecosystem>/<project_name>/", methods=["GET"])
@api_blueprint.route("/api/by_ecosystem/<ecosystem>/<project_name>", methods=["GET"])
def api_get_project_ecosystem(ecosystem, project_name):
    """
    Retrieves a project in an ecosystem via the name of the ecosystem
    and the name of the project as registered with Anitya.

    :arg str ecosystem: the name of the ecosystem (case insensitive).
    :arg str project_name: the name of the project in Anitya.
    :statuscode 200: Returns the JSON representation of the project.
    :statuscode 404: When either the ecosystem does not exist, or when
        there is no project with that name within the ecosystem.

    **Example request**:

    .. sourcecode:: http

        GET /api/by_ecosystem/pypi/six HTTP/1.1
        Accept: application/json
        Accept-Encoding: gzip, deflate
        Connection: keep-alive
        Host: release-monitoring.org
        User-Agent: HTTPie/0.9.4


    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Length: 516
        Content-Type: application/json

        {
          "backend": "pypi",
          "created_on": 1409917222.0,
          "homepage": "https://pypi.python.org/pypi/six",
          "id": 2,
          "name": "six",
          "packages": [
            {
              "distro": "Fedora",
              "package_name": "python-six"
            }
          ],
          "regex": null,
          "updated_on": 1414400794.0,
          "version": "1.10.0",
          "version_url": null,
          "versions": [
            "1.10.0"
          ]
        }
    """

    project = models.Project.by_name_and_ecosystem(Session, project_name, ecosystem)

    if not project:
        output = {
            "output": "notok",
            "error": 'No project "%s" found in ecosystem "%s"'
            % (project_name, ecosystem),
        }
        httpcode = 404

    else:
        output = project.__json__(detailed=True)
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
