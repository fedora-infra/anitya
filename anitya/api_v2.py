# -*- coding: utf-8 -*-

from gettext import gettext as _

from flask_restful import Resource, reqparse

from anitya.app import APP, SESSION
import anitya
import anitya.lib.model
import anitya.authentication

_BASE_ARG_PARSER = reqparse.RequestParser(trim=True, bundle_errors=True)
_BASE_ARG_PARSER.add_argument('access_token', type=str)

class ProjectsResource(Resource):
    """
    The ``api/v2/projects/`` API endpoint.
    """

    @anitya.authentication.parse_api_token
    def get(self):
        """Lists all projects"""
        # TODO paginate
        project_objs = anitya.lib.model.Project.all(SESSION)
        projects = [project.__json__() for project in project_objs]
        return projects

    @anitya.authentication.require_api_token("upstream")
    def post(self):
        """Create a new project"""
        name_help = _('The project name')
        homepage_help = _('The project homepage URL')
        backend_help = _('The project backend (github, folder, etc.)')
        version_url_help = _('The URL to fetch when determining the project '
                             'version (defaults to null)')
        version_prefix_help = _('The project version prefix, if any. For '
                                'example, some projects prefix with "v"')
        regex_help = _('The regex to use when searching the version_url page')
        insecure_help = _('When retrieving the versions via HTTPS, do not '
                          'validate the certificate (defaults to false)')
        check_release_help = _('Check the release immediately after creating '
                               'the project.')

        parser = _BASE_ARG_PARSER.copy()
        parser.add_argument('name', type=str, help=name_help, required=True)
        parser.add_argument(
            'homepage', type=str, help=homepage_help, required=True)
        parser.add_argument(
            'backend', type=str, help=backend_help, required=True)
        parser.add_argument(
            'version_url', type=str, help=version_url_help, default=None)
        parser.add_argument(
            'version_prefix', type=str, help=version_prefix_help, default=None)
        parser.add_argument('regex', type=str, help=regex_help, default=None)
        parser.add_argument(
            'insecure', type=bool, help=insecure_help, default=False)
        parser.add_argument(
            'check_release', type=bool, help=check_release_help)
        args = parser.parse_args(strict=True)
        access_token = args.pop('access_token')

        # TODO conficts etc
        anitya.lib.create_project(
            SESSION,
            user_id=APP.oidc.user_getfield('email', access_token),
            **args
        )
        SESSION.commit()


APP.api.add_resource(ProjectsResource, '/api/v2/projects/')
