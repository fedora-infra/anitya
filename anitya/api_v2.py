# -*- coding: utf-8 -*-
"""
This is the version 2 HTTP API.

It uses OpenID Connect for endpoints that require authentication.
"""

from gettext import gettext as _
import logging

import flask_login
from flask import jsonify
from flask_restful import Resource, inputs, reqparse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from anitya import authentication
from anitya.db import Session, models
from anitya.lib import utilities
from anitya.lib.exceptions import ProjectExists, AnityaException

_BASE_ARG_PARSER = reqparse.RequestParser(trim=True, bundle_errors=True)
_log = logging.getLogger(__name__)


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
            q = q.filter(func.lower(models.Packages.distro_name) == func.lower(distro))
        if name:
            q = q.filter(func.lower(models.Packages.package_name) == func.lower(name))
        page = q.paginate(order_by=models.Packages.package_name, **args)
        return {
            "items": [
                {
                    "distribution": package.distro_name,
                    "name": package.package_name,
                    "project": package.project.name,
                    "ecosystem": package.project.ecosystem_name,
                }
                for package in page.items
            ],
            "page": page.page,
            "items_per_page": page.items_per_page,
            "total_items": page.total_items,
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
            project = models.Project.query.filter(
                func.lower(models.Project.name) == func.lower(args.project_name),
                func.lower(models.Project.ecosystem_name)
                == func.lower(args.project_ecosystem),
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
            distro = models.Distro.query.filter(
                func.lower(models.Distro.name) == func.lower(args.distribution)
            ).one()
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
            utilities.publish_message(
                project=project.__json__(),
                distro=distro.__json__(),
                topic="project.map.new",
                message=message,
            )
            return {"distribution": distro.name, "name": package.package_name}, 201
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
                        ],
                        "stable_versions": [
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
            q = q.filter(
                func.lower(models.Project.ecosystem_name) == func.lower(ecosystem)
            )
        if name:
            q = q.filter(func.lower(models.Project.name) == func.lower(name))
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
                "versions": [],
                "stable_versions": []
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
                Session,
                user_id=flask_login.current_user.email,
                name=args.name,
                homepage=args.homepage,
                backend=args.backend,
                version_url=args.version_url,
                version_prefix=args.version_prefix,
                regex=args.regex,
                insecure=args.insecure,
            )
            Session.commit()
            if args.check_release:
                try:
                    utilities.check_project_release(project, Session)
                except AnityaException as err:
                    _log.error(str(err))
            return project.__json__(), 201
        except ProjectExists as e:
            response = jsonify(e.to_dict())
            response.status_code = 409
            return response


class VersionsResource(Resource):
    """
    The ``api/v2/versions/`` API endpoint.
    """

    def get(self):
        """
        Lists all versions on project.

        **Example request**:

        .. sourcecode:: http

            GET /api/v2/versions/?project_id=1 HTTP/1.1
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
                "latest_version": "2.12",
                "versions": [
                    "2.12",
                    "2.11",
                    "2.10",
                    "2.9.1",
                    "2.9",
                    "2.8",
                    "2.7"
                ],
                "stable_versions": [
                    "2.12",
                    "2.11",
                    "2.10",
                    "2.9.1",
                    "2.9",
                    "2.8",
                    "2.7"
                ]
            }


        :query int project_id: The id of the project we want to get versions for.
        :statuscode 200: If all arguments are valid.
        :statuscode 400: If one or more of the query arguments is invalid.
        :statuscode 404: If project with specified id doesn't exist.
        """
        parser = _BASE_ARG_PARSER.copy()
        parser.add_argument("project_id", type=int, location="args")
        args = parser.parse_args(strict=True)
        project_id = args.pop("project_id")
        project = models.Project.get(Session, project_id=project_id)
        if not project:
            response = {"output": "notok", "error": "No such project"}, 404
            return response

        response = {
            "latest_version": project.latest_version,
            "versions": project.versions,
            "stable_versions": [v.version for v in project.stable_versions],
        }
        return response

    @authentication.require_token
    def post(self):
        """
        Check for new versions on the project. The API first checks if the project exists,
        if exists it will do check on it while applying any changes.
        If not it will create a temporary object in memory and do a check on the temporary object.

        **Example Request**:

        .. sourcecode:: http

            POST /api/v2/versions/ HTTP/1.1
            Accept: application/json, */*
            Accept-Encoding: gzip, deflate
            Authorization: token s12p01zUiVdEOZIhVf0jyZqtyYXfo2DECi6YdqqV
            Connection: keep-alive
            Content-Length: 15
            Content-Type: application/json
            Host: localhost:5000
            User-Agent: HTTPie/1.0.3

            {
                "id": "55612"
            }

        **Example Response**:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Length: 118
            Content-Type: application/json
            Date: Tue, 20 Oct 2020 08:49:01 GMT
            Server: Werkzeug/0.16.0 Python/3.8.6

            {
                "found_versions": [],
                "latest_version": "0.0.2",
                "versions": [
                    "0.0.2",
                    "0.0.1"
                ],
                "stable_versions": [
                    "0.0.2",
                    "0.0.1"
                ]
            }

        :query string access_token: Your API access token.
        :reqjson int id: Id of the project.
                         If provided the check is done above existing project.
        :reqjson string name: The project name. Used as a filter to find existing project,
                              if id not provided.
        :reqjson string homepage: The project homepage URL. Used as a filter to find
                                  existing project, if id not provided.
        :reqjson string backend: The project backend (github, folder, etc.).
        :reqjson string version_url: The URL to fetch when determining the
                                     project version.
        :reqjson string version_scheme: The project version scheme
                                        (defaults to "RPM" for temporary project).
        :reqjson string version_pattern: The version pattern for calendar version scheme.
        :reqjson string version_prefix: The project version prefix, if any.
        :reqjson string pre_release_filter: Filter for unstable versions.
        :reqjson string version_filter: Filter for blacklisted versions.
        :reqjson string regex: The regex to use when searching the
                               ``version_url`` page
                               (defaults to none for temporary project).
        :reqjson bool insecure: When retrieving the versions via HTTPS, do not
                                validate the certificate
                                (defaults to false for temporary project).
        :reqjson bool releases_only: When retrieving the versions, use releases
                                     instead of tags (defaults to false
                                     for temporary project).
                                     Only available for GitHub backend.
        :reqjson bool dry_run: If set, doesn't save anything (defaults to true).
                               Can't be set to False for temporary project.

        :statuscode 200: When the versions were successfully retrieved.
        :statuscode 400: When required arguments are missing or malformed.
        :statuscode 401: When your access token is missing or invalid, or when
                         the server is not configured for OpenID Connect. The
                         response will include a JSON body describing the exact
                         problem.
        :statuscode 404: When id is provided and the project doesn't exist or is archived.
        :statuscode 500: If there is error during the check
        """
        id_help = _(
            "Id of the project. If provided the check is done above existing project."
        )
        name_help = _(
            "The project name. Used as a filter to find existing project, "
            "if id not provided."
        )
        homepage_help = _(
            "The project homepage URL. Used as a filter to find "
            "existing project, if id not provided."
        )
        backend_help = _("The project backend (github, folder, etc.).")
        version_url_help = _(
            "The URL to fetch when determining the " "project version."
        )
        version_scheme_help = _(
            "The project version scheme " "(defaults to 'RPM' for temporary project)."
        )
        version_pattern_help = _("The version pattern for calendar version scheme.")
        version_prefix_help = _("The project version prefix, if any.")
        pre_release_filter_help = _("Filter for unstable versions.")
        version_filter_help = _("Filter for blacklisted versions.")
        regex_help = _(
            "The regex to use when searching the version_url page "
            "(defaults to none for temporary project)."
        )
        insecure_help = _(
            "When retrieving the versions via HTTPS, do not "
            "validate the certificate (defaults to false for temporary project)."
        )
        releases_only_help = _(
            "When retrieving the versions, use releases "
            "instead of tags (defaults to false for temporary project). "
            "Only available for GitHub backend."
        )
        dry_run_help = _(
            "If set, doesn't save anything (defaults to true). "
            "Can't be set to False for temporary project."
        )

        parser = _BASE_ARG_PARSER.copy()
        parser.add_argument("id", type=int, help=id_help)
        parser.add_argument("name", type=str, help=name_help)
        parser.add_argument("homepage", type=str, help=homepage_help)
        parser.add_argument("backend", type=str, help=backend_help)
        parser.add_argument("version_url", type=str, help=version_url_help)
        parser.add_argument("version_scheme", type=str, help=version_scheme_help)
        parser.add_argument("version_pattern", type=str, help=version_pattern_help)
        parser.add_argument("version_prefix", type=str, help=version_prefix_help)
        parser.add_argument(
            "pre_release_filter", type=str, help=pre_release_filter_help
        )
        parser.add_argument("version_filter", type=str, help=version_filter_help)
        parser.add_argument("regex", type=str, help=regex_help, default=None)
        parser.add_argument(
            "insecure", type=inputs.boolean, help=insecure_help, default=False
        )
        parser.add_argument(
            "releases_only", type=inputs.boolean, help=releases_only_help, default=False
        )
        parser.add_argument(
            "dry_run", type=inputs.boolean, help=dry_run_help, default=True
        )
        args = parser.parse_args(strict=True)

        project = None
        dry_run = args.get("dry_run")

        # If we have id, try to get the project
        if args.id:
            project = models.Project.get(Session, project_id=args.pop("id"))

            if not project:
                response = "No such project", 404
                return response

        # Don't look for the project if already retrieved
        if not project:
            homepage = args.get("homepage")
            name = args.get("name")
            q = models.Project.query
            if homepage:
                q = q.filter(
                    func.lower(models.Project.homepage) == func.lower(homepage)
                )
            if name:
                q = q.filter(func.lower(models.Project.name) == func.lower(name))

            query_result = q.all()

            if len(query_result) > 1:
                response = (
                    "More than one project found",
                    400,
                )
                return response
            elif len(query_result) == 1:
                project = query_result[0]

        # If we still don't have project create temporary one
        if not project:
            # Check if we have all the required parameters
            missing_parameters = []
            name = args.get("name")
            if not name:
                missing_parameters.append("name")
            homepage = args.get("homepage")
            if not homepage:
                missing_parameters.append("homepage")
            backend = args.get("backend")
            if not backend:
                missing_parameters.append("backend")
            version_url = args.get("version_url")
            if not version_url:
                version_url = homepage

            if missing_parameters:
                response = (
                    "Can't create temporary project. Missing arguments: "
                    + str(missing_parameters),
                    400,
                )
                return response

            # Before we create a temporary project, check the dry_run parameter
            if not dry_run:
                dry_run = True

            project = utilities.create_project(
                Session,
                user_id=flask_login.current_user.email,
                name=name,
                homepage=homepage,
                backend=backend,
                version_url=version_url,
                version_pattern=args.version_pattern,
                version_scheme=args.version_scheme,
                version_prefix=args.version_prefix,
                pre_release_filter=args.pre_release_filter,
                version_filter=args.version_filter,
                regex=args.regex,
                insecure=args.insecure,
                dry_run=dry_run,
            )
        # If the project was retrieved, update it with provided arguments
        else:
            # If argument is missing, use the actual one
            name = args.get("name")
            if not name:
                name = project.name
            homepage = args.get("homepage")
            if not homepage:
                homepage = project.homepage
            backend = args.get("backend")
            if not backend:
                backend = project.backend
            version_scheme = args.get("version_scheme")
            if not version_scheme:
                version_scheme = project.version_scheme
            version_pattern = args.get("version_pattern")
            if not version_pattern:
                version_pattern = project.version_pattern
            version_url = args.get("version_url")
            if not version_url:
                version_url = project.version_url
            version_prefix = args.get("version_prefix")
            if not version_prefix:
                version_prefix = project.version_prefix
            pre_release_filter = args.get("pre_release_filter")
            if not pre_release_filter:
                pre_release_filter = project.pre_release_filter
            version_filter = args.get("version_filter")
            if not version_filter:
                version_filter = project.version_filter
            regex = args.get("regex")
            if not regex:
                regex = project.regex
            insecure = args.get("insecure")
            if not insecure:
                insecure = project.insecure
            releases_only = args.get("releases_only")
            if not releases_only:
                releases_only = project.releases_only
            try:
                utilities.edit_project(
                    Session,
                    user_id=flask_login.current_user.email,
                    project=project,
                    name=name,
                    homepage=homepage,
                    backend=backend,
                    version_scheme=version_scheme,
                    version_pattern=version_pattern,
                    version_url=version_url,
                    version_prefix=version_prefix,
                    pre_release_filter=pre_release_filter,
                    version_filter=version_filter,
                    regex=regex,
                    insecure=insecure,
                    releases_only=releases_only,
                    dry_run=dry_run,
                )
            except AnityaException as err:
                response = str(err), 500
                return response

        if project:
            try:
                versions = utilities.check_project_release(
                    project, Session, test=dry_run
                )
            except AnityaException as err:
                response = "Error when checking for new version: " + str(err), 500
                return response

            response = {
                "latest_version": project.latest_version,
                "found_versions": versions,
                "versions": project.versions,
                "stable_versions": [v.version for v in project.stable_versions],
            }
            return response
