=================
Development Guide
=================

Anitya welcomes contributions! Our issue tracker is located on
`GitHub <https://github.com/fedora-infra/anitya/issues>`_.


Contribution Guidelines
=======================

When you make a pull request, someone from the fedora-infra organization
will review your code. Please make sure you follow the guidelines below:

Python Support
--------------

Anitya supports Python 3.8 or greater so please ensure the code
you submit works with these versions. The test suite will run against all supported
Python versions to make this easier.

Dependency management
---------------------

Anitya is using two dependency management tool. One is `poetry <https://python-poetry.org/>`_
for python packages and `npm <https://www.npmjs.com/>`_ for javascript/CSS packages.
Anitya also uses `renovate <https://docs.renovatebot.com/>`_ to keep those dependencies up to
date in repository.


Code Style
----------

We follow the `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python.
The test suite includes a test that enforces the required style, so all you need to do is
run the tests to ensure your code follows the style. If the unit test passes, you are
good to go!

To automatically format the code run the following in project root. The ``.tox`` folder
will be created when ``poetry run tox`` will be run.

.. code-block:: bash

   .tox/format/bin/black .


Unit Tests
----------

The test suites can be run using `tox <http://tox.readthedocs.io/>`_ by simply running
``poetry run tox`` from the repository root. These tests include unit tests, a linter to ensure
Python code style is correct, checks for possible security issues, and checks the
documentation for Sphinx warnings or errors.

All tests must pass. All new code should have 100% test coverage.
Any bugfix should be accompanied by one or more unit tests to demonstrate the fix.
If you are unsure how to write unit tests for your code, we will be happy to help
you during the code review process.


CI (Continuous Integration)
---------------------------

Anitya has a CI set up to run on each PR. As a CI of choice Anitya is using
`Fedora zuul <https://fedoraproject.org/wiki/Zuul-based-ci>`_ and the configuration
could be found in `.zuul.yaml` in Anitya root directory.

The CI runs unit tests for all supported python versions, code style test, coverage test,
flake8 test (linter), documentation test build and bandit (to check for any security issue).

The successful run of CI is a requirement for merge of the PR.


Documentation
-------------

Anitya uses `sphinx <http://www.sphinx-doc.org/>`_ to create its documentation.
New packages, modules, classes, methods, functions, and attributes all should be
documented using `"Google style" <http://www.sphinx-doc.org/en/1.7/ext/example_google.html>`_
docstrings. For historical reasons you may encounter plain reStructuredText-style
docstrings. Please consider converting them and opening a pull request!

Python API documentation is automatically generated from the code using Sphinx's
`autodoc <http://www.sphinx-doc.org/en/stable/tutorial.html#autodoc>`_ extension.
HTTP REST API documentation is automatically generated from the code using the
`httpdomain <https://pythonhosted.org/sphinxcontrib-httpdomain/>`_ extension.


Release notes
-------------

To add entries to the release notes, create a file in the ``news`` directory
with the ``source.type`` name format, where ``type`` is one of:

* ``feature``: for new features
* ``bug``: for bug fixes
* ``api``: for API changes
* ``dev``: for development-related changes
* ``author``: for contributor names
* ``other``: for other changes

And where the ``source`` part of the filename is:

* ``42`` when the change is described in issue ``42``
* ``PR42`` when the change has been implemented in pull request ``42``, and
  there is no associated issue
* ``username`` for contributors (``author`` extention). It should be the
  username part of their commit's email address.
  
For example:

If this PR is solving `bug 714 <https://github.com/fedora-infra/anitya/issues/714>`_
the file inside ``news`` should be called ``714.bug``
and the content of the file would be:

``Javascript error on add project page``

Matching the issue title.

The text inside the file will be used as entry text.
A preview of the release notes can be generated with ``poetry towncrier --draft``.

Development Environment
=======================

There are two options for setting up a development environment. If you're not
sure which one to choose, pick the Vagrant method.

Vagrant
-------

The `Vagrant`_ development environment is set up using `Ansible`_.

To get started, install Vagrant and Ansible. On Fedora::

    $ sudo dnf install @virtualization vagrant vagrant-libvirt vagrant-sshfs ansible

Make sure that the following services are enabled & started on the host::

    $ sudo systemctl enable --now virtnetworkd
    $ sudo systemctl enable --now libvirtd

Next, clone the repository and start the Vagrant machine::

    $ git clone https://github.com/fedora-infra/anitya.git
    $ cd anitya
    $ vagrant up
    $ vagrant ssh

When you log in you'll be presented with a message of the day with more details
about the environment.

To start the Anitya instance in vagrant you can run::

    $ systemctl --user enable --now anitya.service

You may then access Anitya on your host at::

    http://127.0.0.1:5000

or::

    http://localhost:5000

By default, Anitya imports the production database so you've got something
to start with. If instead you prefer an empty database, add the following
to the Ansible provisioner inside your `Vagrantfile`::

    ansible.extra_vars = { import_production_database: false }

The application's configuration file is ``/home/vagrant/anitya.toml``.
You can also look at the `sample configuration <https://github.com/fedora-infra/anitya/blob/master/files/anitya.toml.sample>`_

.. note::
   Please don't commit any local changes to Vagrantfile. We are managing it
   upstream.

Vagrant is using `PostgreSQL database <https://www.postgresql.org/>`_.
To work with it use ``psql`` command::

    $ sudo -u postgres psql
    postgres=#\connect anitya

After this you can use standard `SQL queries
<https://www.postgresql.org/docs/10/static/tutorial-sql.html>`_ or
another ``psql`` commands::

    # Show description of tables
    \dt
    # Show table description
    \d users

For additional ``psql`` commands see ``man psql``.

To run check service in the guest vm simply run::

   $ systemctl --user enable --now check-service.service

Docker / Podman
---------------

This way, you will be able to control each service (anitya-web, RabbitMQ, etc) separately. You can turn off RabbitMQ or PostgreSQL or both, then connect to external services or use them with the application.

Requirements:

* Docker / Podman
* Docker Compose / Podman Compose

Next, clone the repository and start containers::

    $ git clone https://github.com/fedora-infra/anitya
    $ cd anitya
    $ make up

.. list-table:: Container Service Informations:
   :widths: 25 25 50
   :header-rows: 1

   * - Name 1
     - Url
     - Credentials
   * - RabbitMQ
     - localhost:5672
     - anitya:anitya
   * - RabbitMQ Management UI
     - http://localhost:15672
     - anitya:anitya
   * - PostgreSQL
     - localhost:5432
     - postgres:anypasswordworkslocally

Makefile scripts that provide easier container management:

* ``make up`` Starts all the container services
* ``make restart`` Restarts all the container services that are either stopped or running
* ``make halt`` Stops and removes the containers
* ``make bash-web`` Connects to anitya-web container
* ``make init-db`` Creates database
* ``make dump-restore`` Import production database
* ``make logs`` Shows all logs of all containers
* ``make clean`` Removes all images used by Anitya compose

Project files are bound to each other with host and container. Whenever you change any project file from the host or the container, the same change will happen on the opposite side as well.

Anitya is accessible on http://localhost:5000

Start the check service with::

    $ make bash-consumer or make-bash-web
    $ check_service.py

To apply changes run::
    $ make restart

This will restart the container, deploy the changes in code and start the development instance again.

Python virtualenv
-----------------

Anitya can also be run in a Python virtualenv. For Fedora::

    $ dnf install poetry npm
    $ git clone https://github.com/fedora-infra/anitya.git
    $ cd anitya

Next, install Anitya. Poetry will create a virtualenv for the project::

    $ poetry install

Install javascript dependencies::

    $ pushd anitya/static
    $ npm install
    $ popd

Create the database, by default it will be a sqlite database located at
``/var/tmp/anitya-dev.sqlite``::

    $ poetry run python createdb.py

You can start the development web server included with Flask with::

    $ FLASK_APP=anitya.wsgi poetry run flask run

If you want to change the application's configuration, create a valid configuration
file and start the application with the ``ANITYA_WEB_CONFIG`` environment variable
set to the configuration file's path. You can look at the
`sample configuration <https://github.com/fedora-infra/anitya/blob/master/files/anitya.toml.sample>`_
for guidance.


Release Guide
=============

Testing before release
----------------------

To test the new version before release just update the ``staging`` branch
to current ``master``::

    git checkout staging
    git rebase master
    git push origin/staging

This will automatically start the deployment in
`staging instance <https://stg.release-monitoring.org/>`_. You can then test the new
changes there.

If you need to do any changes in configuration of ``staging`` instance,
just update the
`release-monitoring role <https://pagure.io/fedora-infra/ansible/blob/main/f/roles/openshift-apps/release-monitoring>`_
in Fedora infra ansible repository.

If the changes are merged, you can run the playbook by following
`configuration guide <https://fedora-infra-docs.readthedocs.io/en/latest/sysadmin-guide/sops/anitya.html#configuration>`_
for Anitya in Fedora infra documentation.

.. note::
   Have in mind that everything needs to be only done for staging. In configuration use jinja statements
   and when deploying don't forget to use ``-l staging`` switch.

Anitya
------

To do the release you need following python packages installed::

    poetry

If you are a maintainer and wish to make a release, follow these steps:

1. Change the version using ``poetry version <version>``.
   This is used to set the version in the documentation.

2. Add any missing news fragments to the ``news`` folder.

3. Get authors of commits by ``python get-authors.py``.

.. note::
   This script must be executed in ``news`` folder, because it
   creates files in current working directory.

4. Install Anitya in virtual environment by ``poetry install``.

5. Generate the changelog by running ``poetry run towncrier``.

.. note::
    If you added any news fragment in the previous step, you might see ``towncrier``
    complaining about removing them, because they are not committed in git.
    Just ignore this and remove all of them manually; release notes will be generated
    anyway.

6. Remove every remaining news fragment from ``news`` folder.

7. Generate new DB schema image by running ``poetry run ./generate_db_schema`` in ``docs`` folder.

8. Commit your changes with message *Anitya <version>*.

9. Tag a release with ``git tag -s <version>`` with description *Anitya <version>*.

10. Don't forget to ``git push --tags``.

11. Sometimes you need to also do ``git push``.

12. Build the Python packages with ``poetry build``.

13. Upload the packages with ``poetry publish``.

14. Create new release on `GitHub releases <https://github.com/fedora-infra/the-new-hotness/releases>`_.

15. Deploy the new version in staging::

     $ git checkout staging
     $ git rebase master
     $ git push origin staging

16. When successfully tested in staging deploy to production::

     $ git checkout production
     $ git rebase staging
     $ git push origin production

.. _Ansible: https://www.ansible.com/
.. _Vagrant: https://vagrantup.com/
