# -*- coding: utf-8 -*-

import flask

import anitya
import anitya.lib.plugins
import anitya.lib.model

from anitya.app import APP, SESSION
from anitya.doc_utils import load_doc


@APP.template_filter('InsertDiv')
def insert_div(content):
    """ Template filter inserting an opening <div> and closing </div>
    after the first title and then at the end of the content.
    """
    # This is quite a hack but simpler solution using .replace() didn't work
    # for some reasons...
    content = content.split('\n')
    output = []
    for row in content:
        if row.startswith('<h1 class="title">'):
          title = row.split('"title">')[1].split('</h1>')[0]
          link = '<a name="%(title)s" class="glyphicon glyphicon-link btn-xs" '\
              'title="Permalink to this headline" href="#%(title)s"></a>' % (
                  {
                      'title': title.replace(' ', '_'),
                  }
              )
          row = str(row).replace('</h1>', link + '</h1>')
        if row.startswith('<div class="document" id='):
            continue
        output.append(row)
    output = "\n".join(output)
    output = output.replace('</div>', '')
    output = output.replace('h1', 'h3')

    return output


@APP.route('/api/')
@APP.route('/api')
def api():
    ''' Display the api information page. '''
    doc_api_version = load_doc(api_version)
    doc_api_projects = load_doc(api_projects)
    doc_api_packages_wiki_list = load_doc(api_packages_wiki_list)
    doc_api_projects_names = load_doc(api_projects_names)
    doc_api_get_version = load_doc(api_get_version)
    doc_api_get_project = load_doc(api_get_project)
    doc_api_get_project_distro = load_doc(api_get_project_distro)
    return flask.render_template(
        'api.html',
        docs=[
            doc_api_version,
            doc_api_projects,
            doc_api_packages_wiki_list,
            doc_api_projects_names,
            doc_api_get_version,
            doc_api_get_project,
            doc_api_get_project_distro,
        ],
    )


@APP.route('/api/version/')
@APP.route('/api/version')
def api_version():
    '''
    API Version
    -----------
    Display the api version information.

    ::

        /api/version

    Accepts GET queries only.

    Sample response:

    ::

        {
          "version": "1.0"
        }

    '''
    return flask.jsonify({'version': anitya.__api_version__})


@APP.route('/api/projects/')
@APP.route('/api/projects')
def api_projects():
    '''
    List all projects
    -----------------
    Lists all the projects registered in anitya.

    ::

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

    Sample response:

    ::

      {
        "projects": [
          {
            "backend": "custom",
            "created_on": 1409917222.0,
            "homepage": "http://www.finnie.org/software/2ping/",
            "id": 2,
            "name": "2ping",
            "regex": null,
            "updated_on": 1414400794.0,
            "version": "2.1.1",
            "version_url": "http://www.finnie.org/software/2ping",
            "versions": [
              "2.1.1"
            ]
          },
          {
            "backend": "custom",
            "created_on": 1409917223.0,
            "homepage": "http://www.3proxy.ru/download/",
            "id": 3,
            "name": "3proxy",
            "regex": null,
            "updated_on": 1415115096.0,
            "version": "0.7.1.1",
            "version_url": "http://www.3proxy.ru/download/",
            "versions": [
              "0.7.1.1"
            ]
          }
        ],
        "total": 2
      }

    '''

    pattern = flask.request.args.get('pattern', None)
    homepage = flask.request.args.get('homepage', None)
    distro = flask.request.args.get('distro', None)

    if pattern and homepage:
        err = 'pattern and homepage are mutually exclusive.  Specify only one.'
        output = {'output': 'notok', 'error': [err]}
        jsonout = flask.jsonify(output)
        jsonout.status_code = 400
        return jsonout

    if homepage is not None:
        project_objs = anitya.lib.model.Project.by_homepage(SESSION, homepage)
    elif pattern or distro:
        if pattern and '*' not in pattern:
            pattern += '*'
        project_objs = anitya.lib.model.Project.search(
            SESSION, pattern=pattern, distro=distro)
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


@APP.route('/api/packages/wiki/')
@APP.route('/api/packages/wiki')
def api_packages_wiki_list():
    '''
    List all packages in mediawiki format
    -------------------------------------
    Lists all the packages registered in anitya using the format of the
    old wiki page. If a project is present multiple times on different
    distribution, it will be shown multiple times.

    ::

        /api/packages/wiki

    Accepts GET queries only.

    Sample response:

    ::

      * 2ping None http://www.finnie.org/software/2ping
      * 3proxy None http://www.3proxy.ru/download/
    '''


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
    '''
    List all projects names
    ------------------------
    Lists the names of all the projects registered in anitya.

    ::

        /api/projects/names

        /api/projects/names/?pattern=<pattern>

        /api/projects/names/?pattern=py*

    Accepts GET queries only.

    :kwarg pattern: pattern to use to restrict the list of names returned.

    Sample response:

    ::

      {
        "projects": [
          "2ping",
          "3proxy",
        ],
        "total": 2
      }

    '''

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


@APP.route('/api/distro/names/')
@APP.route('/api/distro/names')
def api_distro_names():
    '''
    List all distribution names
    ---------------------------
    Lists the names of all the distributions registered in anitya.

    ::

        /api/distro/names

        /api/projects/names/?pattern=<pattern>

        /api/projects/names/?pattern=f*

    Accepts GET queries only.

    :kwarg pattern: pattern to use to restrict the list of distro returned.

    Accepts GET queries only.

    Sample response:

    ::

      {
        "distro": [
          "Fedora",
          "Debian",
        ],
        "total": 2
      }

    '''

    pattern = flask.request.args.get('pattern', None)

    if pattern and '*' not in pattern:
        pattern += '*'

    if pattern:
        distro_objs = anitya.lib.model.Distro.search(
            SESSION, pattern=pattern)
    else:
        distro_objs = anitya.lib.model.Distro.all(SESSION)

    distros = [distro.name for distro in distro_objs]

    output = {
        'total': len(distros),
        'distro': distros
    }

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@APP.route('/api/version/get', methods=['POST'])
def api_get_version():
    '''
    Retrieve version
    ----------------
    Forces anitya to retrieve the latest version available from a project
    upstream.

    ::

        /api/version/get

    Accepts POST queries only.

    :arg id: the identifier of the project in anitya.

    Sample response:

    ::

      {
        "backend": "Sourceforge",
        "created_on": 1409917222.0,
        "homepage": "http://sourceforge.net/projects/zero-install",
        "id": 1,
        "name": "zero-install",
        "packages": [
          {
            "distro": "Fedora",
            "package_name": "0install"
          }
        ],
        "regex": "",
        "updated_on": 1413794215.0,
        "version": "2.7",
        "version_url": "0install",
        "versions": [
          "2.7"
        ]
      }

    '''

    project_id = flask.request.form.get('id', None)
    test = flask.request.form.get('test', False)
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
                version = anitya.check_release(project, SESSION, test=test)
                if version:
                    output = {'version': version}
                else:
                    output = project.__json__(detailed=True)
            except anitya.lib.exceptions.AnityaException as err:
                output = {'output': 'notok', 'error': [str(err)]}
                httpcode = 400

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@APP.route('/api/project/<int:project_id>/', methods=['GET'])
@APP.route('/api/project/<int:project_id>', methods=['GET'])
def api_get_project(project_id):
    '''
    Retrieve a specific project
    ----------------------------
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
        "homepage": "http://www.finnie.org/software/2ping/",
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
        "version_url": "http://www.finnie.org/software/2ping",
        "versions": [
          "2.1.1"
        ]
      }

    '''

    project = anitya.lib.model.Project.get(SESSION, project_id=project_id)

    if not project:
        output = {'output': 'notok', 'error': 'no such project'}
        httpcode = 404
    else:
        output = project.__json__(detailed=True)
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout


@APP.route('/api/project/<distro>/<package_name>/', methods=['GET'])
@APP.route('/api/project/<distro>/<package_name>', methods=['GET'])
def api_get_project_distro(distro, package_name):
    '''
    Retrieve a package for a distro
    -------------------------------
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
        "homepage": "http://www.finnie.org/software/2ping/",
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
        "version_url": "http://www.finnie.org/software/2ping",
        "versions": [
          "2.1.1"
        ]
      }

    '''

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

        output = project.__json__(detailed=True)
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout

@APP.route('/api/by_ecosystem/<ecosystem>/<project_name>/', methods=['GET'])
@APP.route('/api/by_ecosystem/<ecosystem>/<project_name>', methods=['GET'])
def api_get_project_ecosystem(ecosystem, project_name):
    '''
    Retrieve a project from a given ecosystem
    -------------------------------
    Retrieves a project in an ecosystem via the name of the ecosystem
    and the name of the project as registered with Anitya.

    ::

        /api/by_ecosystem/<ecosystem>/<project_name>

    Accepts GET queries only.

    :arg ecosystem: the name of the ecosystem (case insensitive).
    :arg project_name: the name of the project in Anitya.

    Sample response:

    ::

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

    '''

    project = anitya.lib.model.Project.by_name_and_ecosystem(
        SESSION, project_name, ecosystem)

    if not project:
        output = {
            'output': 'notok',
            'error': 'No project "%s" found in ecosystem "%s"' % (
                project_name, ecosystem)}
        httpcode = 404

    else:
        output = project.__json__(detailed=True)
        httpcode = 200

    jsonout = flask.jsonify(output)
    jsonout.status_code = httpcode
    return jsonout
