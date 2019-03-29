# -*- coding: utf-8 -*-
"""
This is the version 2 HTTP API.

It uses OpenID Connect for endpoints that require authentication.
"""

from gettext import gettext as _

import flask_login
from flask import jsonify
from flask_restful import Resource, reqparse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from anitya import authentication
from anitya.db import Session, models
from anitya.lib import utilities
from anitya.lib.exceptions import ProjectExists

_BASE_ARG_PARSER = reqparse.RequestParser(trim=True, bundle_errors=True)


def _page_validator(arg):
    """
    Validator for a pagination page number.

    Args:
        arg (object): The object to validate as an integer greater than or
            equal to 1.

    Returns:
        int: The validated argument.

    Raises:
        ValueError: If the integer is smaller than 1 or it can't be cast to an
            int.
    """
    arg = int(arg)
    if arg < 1:
        raise ValueError(_("Value must be greater than or equal to 1."))
    return arg


def _items_per_page_validator(arg):
    """
    Validator for a pagination items_per_page number.

    Args:
        arg (object): The object to validate as an integer greater than or
            equal to 1 and less or equal to 250.

    Returns:
        int: The validated argument.

    Raises:
        ValueError: If the integer is smaller than 1 or it can't be cast to an
            int.
    """
    arg = int(arg)
    if arg < 1:
        raise ValueError(_("Value must be greater than or equal to 1."))
    if arg > 250:
        raise ValueError(_("Value must be less than or equal to 250."))
    return arg


class PackagesResource(Resource):
    """The ``api/v2/packages/`` API endpoint."""

    def get(self):
        """
        List all packages.

        **Example request**:

        .. sourcecode:: http

            GET /api/v2/packages/?name=0ad&distribution=Fedora HTTP/1.1
            Accept: application/json
            Accept-Encoding: gzip, deflate
            Connection: keep-alive
            Host: localhost:5000
            User-Agent: HTTPie/0.9.4

        **Example response**:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Length: 181
            Content-Type: application/json
            Date: Mon, 15 Jan 2018 20:21:44 GMT
            Server: Werkzeug/0.14.1 Python/2.7.14

            {
                "items": [
                    {
                        "distribution": "Fedora",
                        "name": "python-requests"
                        "project": "requests",
                        "ecosystem": "pypi",
                    }
                ],
                "items_per_page": 25,
                "page": 1,
                "total_items": 1
            }


        :query int page: The package page number to retrieve (defaults to 1).
        :query int items_per_page: The number of items per page (defaults to
                                   25, maximum of 250).
        :query str distribution: Filter packages by distribution.
        :query str name: The name of the package.
        :statuscode 200: If all arguments are valid. Note that even if there
                         are no projects, this will return 200.
        :statuscode 400: If one or more of the query arguments is invalid.
        """
        parser = _BASE_ARG_PARSER.copy()
        parser.add_argument("page", type=_page_validator, location="args")
        parser.add_argument(
            "items_per_page", type=_items_per_page_validator, location="args"
        )
        parser.add_argument("distribution", type=str, location="args")
        parser.add_argument("name", type=str, location="args")
        args = parser.parse_args(strict=True)
        q = models.Packages.query
        distro = args.pop("distribution")
        name = args.pop("name")
        if distro:
            q = q.filter_by(distro_name=distro)
        if name:
            q = q.filter_by(package_name=name)
        page = q.paginate(order_by=models.Packages.package_name, **args)
        return {
            u"items": [
                {
                    u"distribution": package.distro_name,
                    u"name": package.package_name,
                    u"project": package.project.name,
                    u"ecosystem": package.project.ecosystem_name,
                }
                for package in page.items
            ],
            u"page": page.page,
            u"items_per_page": page.items_per_page,
            u"total_items": page.total_items,
        }

    @authentication.require_token
    def post(self):
        """
        Create a new package associated with an existing project and distribution.

        **Example request**:

        .. sourcecode:: http

            POST /api/v2/packages/ HTTP/1.1
            Accept: application/json
            Accept-Encoding: gzip, deflate
            Authorization: Token gAOFi2wQPzUJFIfDkscAKjbJfXELCz0r44m57Ur2
            Connection: keep-alive
            Content-Length: 120
            Content-Type: application/json
            Host: localhost:5000
            User-Agent: HTTPie/0.9.4

            {
                "distribution": "Fedora",
                "package_name": "python-requests",
                "project_ecosystem": "pypi",
                "project_name": "requests"
            }

        .. sourcecode:: http

            HTTP/1.0 201 CREATED
            Content-Length: 69
            Content-Type: application/json
            Date: Mon, 15 Jan 2018 21:49:01 GMT
            Server: Werkzeug/0.14.1 Python/2.7.14

            {
                "distribution": "Fedora",
                "name": "python-requests"
            }


        :reqheader Authorization: API token to use for authentication
        :reqjson string distribution: The name of the distribution that contains this
            package.
        :reqjson string package_name: The name of the package in the distribution repository.
        :reqjson string project_name: The project name in Anitya.
        :reqjson string project_ecosystem: The ecosystem the project is a part of.
            If it's not part of an ecosystem, use the homepage used in the Anitya project.

        :statuscode 201: When the package was successfully created.
        :statuscode 400: When required arguments are missing or malformed.
        :statuscode 401: When your access token is missing or invalid
        :statuscode 409: When the package already exists.
        """
        distribution_help = _(
            "The name of the distribution that contains this package."
        )
        package_name_help = _("The name of the package in the distribution repository.")
        project_name_help = _("The project name in Anitya.")
        project_ecosystem_help = _(
            "The ecosystem the project is a part of. If it's not part of an ecosystem,"
            " use the homepage used in the Anitya project."
        )

        parser = _BASE_ARG_PARSER.copy()
        parser.add_argument(
            "distribution", type=str, help=distribution_help, required=True
        )
        parser.add_argument(
            "package_name", type=str, help=package_name_help, required=True
        )
        parser.add_argument(
            "project_name", type=str, help=project_name_help, required=True
        )
        parser.add_argument(
            "project_ecosystem", type=str, help=project_ecosystem_help, required=True
        )
        args = parser.parse_args(strict=True)
        try:
            project = models.Project.query.filter_by(
                name=args.project_name, ecosystem_name=args.project_ecosystem
            ).one()
        except NoResultFound:
            return (
                {
                    "error": 'Project "{}" in ecosystem "{}" not found'.format(
                        args.project_name, args.project_ecosystem
                    )
                },
                400,
            )

        try:
            distro = models.Distro.query.filter_by(name=args.distribution).one()
        except NoResultFound:
            return (
                {"error": 'Distribution "{}" not found'.format(args.distribution)},
                400,
            )

        try:
            package = models.Packages(
                distro_name=distro.name, project=project, package_name=args.package_name
            )

            Session.add(package)
            Session.commit()

            message = dict(
                agent=flask_login.current_user.email,
                project=project.name,
                distro=distro.name,
                new=package.package_name,
            )
            utilities.log(
                Session,
                project=project.__json__(),
                distro=distro.__json__(),
                topic="project.map.new",
                message=message,
            )
            return {u"distribution": distro.name, u"name": package.package_name}, 201
        except IntegrityError:
            Session.rollback()
            return {"error": "package already exists in distribution"}, 409


class ProjectsResource(Resource):
    """
    The ``api/v2/projects/`` API endpoint.
    """

    def get(self):
        """
        Lists all projects.

        **Example request**:

        .. sourcecode:: http

            GET /api/v2/projects/?items_per_page=1&page=2 HTTP/1.1
            Accept: application/json
            Accept-Encoding: gzip, deflate
            Connection: keep-alive
            Host: localhost:5000
            User-Agent: HTTPie/0.9.4

        **Example response**:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Length: 676
            Content-Type: application/json
            Date: Fri, 24 Mar 2017 18:44:32 GMT
            Server: Werkzeug/0.12.1 Python/2.7.13

            {
                "items": [
                    {
                        "backend": "Sourceforge",
                        "created_on": 1412174943.0,
                        "ecosystem": "https://sourceforge.net/projects/zero-install",
                        "homepage": "https://sourceforge.net/projects/zero-install",
                        "id": 1,
                        "name": "0install",
                        "regex": "",
                        "updated_on": 1482495004.0,
                        "version": "2.12",
                        "version_url": "zero-install",
                        "versions": [
                            "2.12",
                            "2.11",
                            "2.10",
                            "2.9.1",
                            "2.9",
                            "2.8",
                            "2.7"
                        ]
                    }
                ],
                "items_per_page": 1,
                "page": 2,
                "total_items": 13468
            }


        :query int page: The project page number to retrieve (defaults to 1).
        :query int items_per_page: The number of items per page (defaults to
                                   25, maximum of 250).
        :query string ecosystem: The project ecosystem (e.g. pypi, rubygems).
            If the project is not part of a language package index, use its homepage.
        :query string name: The project name to filter the query by.
        :statuscode 200: If all arguments are valid. Note that even if there
                         are no projects matching the query, this will return 200.
        :statuscode 400: If one or more of the query arguments is invalid.
        """
        parser = _BASE_ARG_PARSER.copy()
        parser.add_argument("page", type=_page_validator, location="args")
        parser.add_argument(
            "items_per_page", type=_items_per_page_validator, location="args"
        )
        parser.add_argument("ecosystem", type=str, location="args")
        parser.add_argument("name", type=str, location="args")
        args = parser.parse_args(strict=True)
        ecosystem = args.pop("ecosystem")
        name = args.pop("name")
        q = models.Project.query
        if ecosystem:
            q = q.filter_by(ecosystem_name=ecosystem)
        if name:
            q = q.filter_by(name=name)
        projects_page = q.paginate(
            order_by=(models.Project.name, models.Project.ecosystem_name), **args
        )
        return projects_page.as_dict()

    @authentication.require_token
    def post(self):
        """
        Create a new project.

        **Example Request**:

        .. sourcecode:: http

            POST /api/v2/projects/ HTTP/1.1
            Authorization: token hxPpKow7nnT6UTAEKMtQwl310P6GtyqV8DDbexnk
            Accept: application/json
            Accept-Encoding: gzip, deflate
            Connection: keep-alive
            Content-Length: 114
            Content-Type: application/json
            Host: localhost:5000
            User-Agent: HTTPie/0.9.4

            {
                "backend": "custom",
                "homepage": "https://example.com/test",
                "name": "test_project",
                "version_prefix": "release-"
            }


        **Example Response**:

        .. sourcecode:: http

            HTTP/1.0 201 CREATED
            Content-Length: 276
            Content-Type: application/json
            Date: Sun, 26 Mar 2017 15:56:30 GMT
            Server: Werkzeug/0.12.1 Python/2.7.13

            {
                "backend": "PyPI",
                "created_on": 1490543790.0,
                "homepage": "http://python-requests.org",
                "id": 13857,
                "name": "requests",
                "regex": null,
                "updated_on": 1490543790.0,
                "version": null,
                "version_url": null,
                "versions": []
            }

        :query string access_token: Your API access token.
        :reqjson string name: The project name
        :reqjson string homepage: The project homepage URL
        :reqjson string backend: The project backend (github, folder, etc.).
        :reqjson string version_url: The URL to fetch when determining the
                                     project version (defaults to null).
        :reqjson string version_prefix: The project version prefix, if any. For
                                        example, some projects prefix with "v".
        :reqjson string regex: The regex to use when searching the
                               ``version_url`` page.
        :reqjson bool insecure: When retrieving the versions via HTTPS, do not
                                validate the certificate (defaults to false).
        :reqjson bool check_release: Check the release immediately after
                                     creating the project.

        :statuscode 201: When the project was successfully created.
        :statuscode 400: When required arguments are missing or malformed.
        :statuscode 401: When your access token is missing or invalid, or when
                         the server is not configured for OpenID Connect. The
                         response will include a JSON body describing the exact
                         problem.
        :statuscode 409: When the project already exists.
        """
        name_help = _("The project name")
        homepage_help = _("The project homepage URL")
        backend_help = _("The project backend (github, folder, etc.)")
        version_url_help = _(
            "The URL to fetch when determining the project "
            "version (defaults to null)"
        )
        version_prefix_help = _(
            "The project version prefix, if any. For "
            'example, some projects prefix with "v"'
        )
        regex_help = _("The regex to use when searching the version_url page")
        insecure_help = _(
            "When retrieving the versions via HTTPS, do not "
            "validate the certificate (defaults to false)"
        )
        check_release_help = _(
            "Check the release immediately after creating " "the project."
        )

        parser = _BASE_ARG_PARSER.copy()
        parser.add_argument("name", type=str, help=name_help, required=True)
        parser.add_argument("homepage", type=str, help=homepage_help, required=True)
        parser.add_argument("backend", type=str, help=backend_help, required=True)
        parser.add_argument(
            "version_url", type=str, help=version_url_help, default=None
        )
        parser.add_argument(
            "version_prefix", type=str, help=version_prefix_help, default=None
        )
        parser.add_argument("regex", type=str, help=regex_help, default=None)
        parser.add_argument("insecure", type=bool, help=insecure_help, default=False)
        parser.add_argument("check_release", type=bool, help=check_release_help)
        args = parser.parse_args(strict=True)

        try:
            project = utilities.create_project(
                Session, user_id=flask_login.current_user.email, **args
            )
            Session.commit()
            return project.__json__(), 201
        except ProjectExists as e:
            response = jsonify(e.to_dict())
            response.status_code = 409
            return response
