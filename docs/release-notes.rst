=============
Release Notes
=============

v0.13.0
=======

Dependencies
------------

* Explicitly depend on ``defusedxml``

Features
--------

* Update GitHub backend to `GitHub API v4
  <https://developer.github.com/v4/>`_ (`#582
  <https://github.com/release-monitoring/anitya/pull/582>`_).

* Add GitLab backend. This is implemented using `GitLab API v4
  <https://docs.gitlab.com/ee/api/README.html>`_ (`#591
  <https://github.com/release-monitoring/anitya/pull/591>`_).

* Update CPAN backend to use metacpan.org (`#569
  <https://github.com/release-monitoring/anitya/pull/569>`_).

* Parse XML from CPAN with defusedxml (`#569
  <https://github.com/release-monitoring/anitya/pull/569>`_).

Bug Fixes
---------

* Change edit message for project, when no edit actually happened (`#579
  <https://github.com/release-monitoring/anitya/pull/579>`_).

* Fix wrong title on Edit page (`#578
  <https://github.com/release-monitoring/anitya/pull/578>`_).

* Default custom regex is now configurable (`#571
  <https://github.com/release-monitoring/anitya/pull/571>`_).

v0.12.1
=======

Dependencies
------------

* Unpin ``straight.plugin`` dependency. It was pinned to avoid a bug which has
  since been fixed in the latest releases (`#564
  <https://github.com/release-monitoring/anitya/pull/564>`_).

Bug Fixes
---------

* Rather than returning an HTTP 500 when authenticating with two separate
  identity providers using the same email, return a HTTP 400 to indicate the
  client should not retry the request and inform them they must log in with
  the original identity provider (`#563
  <https://github.com/release-monitoring/anitya/pull/563>`_).


v0.12.0
=======

Dependencies
------------

* Drop the dependency on the Python ``bunch`` package as it is not used.

* There is no longer a hard dependency on the ``rpm`` Python package.

* Introduce a dependency on the Python ``social-auth-app-flask-sqlalchemy`` and
  ``flask-login`` packages in order to support authenticating against OAuth2,
  OpenID Connect, and plain OpenID providers.

* Introduce a dependency on the Python ``blinker`` package to support signaling
  in Flask.

* Introduce a dependency on the Python ``pytoml`` package in order to support
  a TOML configuration format.


Backwards-incompatible Changes
------------------------------

* Dropped support for Python 2.6

* Added support for Python 3.4+

APIs
^^^^

A number of functions that make up Anitya's Python API have been moved
(`#503 <https://github.com/release-monitoring/anitya/pull/503>`_). The full
list of functions are below. Note that no function signatures have changed.

* ``anitya.check_release`` is now ``anitya.lib.utilities.check_project_release``.

* ``anitya.fedmsg_publish`` is now ``anitya.lib.utilities.fedmsg_publish``.

* ``anitya.log`` is now ``anitya.lib.utilities.log``.

* ``anitya.lib.init`` is now ``anitya.lib.utilities.init``.

* ``anitya.lib.create_project`` is now ``anitya.lib.utilities.create_project``.

* ``anitya.lib.edit_project`` is now ``anitya.lib.utilities.edit_project``.

* ``anitya.lib.map_project`` is now ``anitya.lib.utilities.map_project``.

* ``anitya.lib.flag_project`` is now ``anitya.lib.utilities.flag_project``.

* ``anitya.lib.set_flag_state`` is now ``anitya.lib.utilities.set_flag_state``.

* ``anitya.lib.get_last_cron`` is now ``anitya.lib.utilities.get_last_cron``.


Deprecations
------------

* Deprecated the v1 HTTP API.


Features
--------

* Introduced a new set of APIs under ``api/v2/`` that support write operations
  for users authenticated with an API token.

* Configuration is now TOML format.

* Added a user guide to the documentation.

* Added an admin guide to the documentation.

* Automatically generate API documentation with Sphinx.

* Introduce httpdomain support to document the HTTP APIs.

* Add initial support for projects to set a "version scheme" in order to help
  with version ordering. At the present the only version scheme implemented is
  the RPM scheme.

* Add support for authenticating using a large number of OAuth2, OpenID Connect,
  and OpenID providers.

* Add a fedmsg consumer that integrates with libraries.io to provide more timely
  project update notifications.

* Add support for running on OpenShift with s2i.

* Switch over to pypi.org rather than pypi.python.org

* Use HTTPS in backend examples, default URLs, and documentation.


Bug Fixes
---------

* Fixed deprecation warnings from using ``flask.ext`` (#431).

* Fix the NPM backend's update feed.


Developer Improvements
----------------------

* Fixed all warnings generated from building the Sphinx documentation and
  introduce tests to ensure there are no regressions (#427).

* Greatly improved the unit tests by breaking monolithic tests up.

* Moved the unit tests into the ``anitya.tests`` package so tests didn't need
  to mess with the Python path.

* Fixed logging during test runs

* Switched to pytest as the test runner since nose is dead.

* Introduced nested transactions for database tests rather than removing the
  database after each test. This greatly reduced run time.

* Added support for testing against multiple Python versions via tox.

* Added Travis CI integration.

* Added code coverage with pytest-cov and Codecov integration.

* Fixed all flake8 errors.

* Refactored the database code to avoid circular dependencies.

* Allow the Vagrant environment to be provisioned with an empty database.


Contributors
------------

Many thanks to all the contributors for this release, including those who filed
issues. Commits for this release were contributed by:

* Elliott Sales de Andrade
* Jeremy Cline
* luto
* Michael Simacek
* Nick Coghlan
* Nicolas Quiniou-Briand
* Ricardo Martincoski
* robled

Thank you all for your hard work.


v0.11.0
=======

Released February 08, 2017.

* Return 4XX codes in error cases for /projects/new rather than 200 (Issue #246)

* Allow projects using the "folder" backend to make insecure HTTPS requests
  (Issue #386)

* Fix an issue where turning the insecure flag on and then off for a project
  resulted in insecure requests until the server was restarted (Issue #394)

* Add a data migration to set the ecosystem of existing projects if the backend
  they use is the default backend for an ecosystem. Note that this migration
  can fail if existing data has duplicate projects since there is a new
  constraint that a project name is unique within an ecosystem (Issue #402).

* Fix the regular expression used with the Debian backend to strip the "orig"
  being incorrectly included in the version (Issue #398)

* Added a new backend and ecosystem for https://crates.io (Issue #414)

* [insert summary of change here]


v0.10.1
=======

Released November 29, 2016.

* Fix an issue where the version prefix was not being stripped (Issue #372)

* Fix an issue where logs were not viewable to some users (Issue #367)

* Update anitya's mail_logging to be compatible with old and new psutil
  (Issue #368)

* Improve Anitya's error reporting via email (Issue #368)

* Report the reason fetching a URL failed for the folder backend (Issue #338)

* Add a timeout to HTTP requests Anitya makes to ensure it does not wait
  indefinitely (Issue #377)

* Fix an issue where prefixes could be stripped further than intended (Issue #381)

* Add page titles to the HTML templates (Issue #371)

* Switch from processes to threads in the Anitya cron job to avoid sharing
  network sockets for HTTP requests across processes (Issue #335)
