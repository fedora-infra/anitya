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

Anitya supports Python 3.6 or greater so please ensure the code
you submit works with these versions. The test suite will run against all supported
Python versions to make this easier.


Code Style
----------

We follow the `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python.
The test suite includes a test that enforces the required style, so all you need to do is
run the tests to ensure your code follows the style. If the unit test passes, you are
good to go!

To automatically format the code run the following in project root. The ``.tox`` folder
will be created when ``tox`` will be run.

.. code-block:: bash

   .tox/format/bin/black .


Unit Tests
----------

The test suites can be run using `tox <http://tox.readthedocs.io/>`_ by simply running
``tox`` from the repository root. These tests include unit tests, a linter to ensure
Python code style is correct, checks for possible security issues, and checks the
documentation for Sphinx warnings or errors.

All tests must pass. All new code should have 100% test coverage.
Any bugfix should be accompanied by one or more unit tests to demonstrate the fix.
If you are unsure how to write unit tests for your code, we will be happy to help
you during the code review process.


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
A preview of the release notes can be generated with ``towncrier --draft``.

Development Environment
=======================

There are two options for setting up a development environment. If you're not
sure which one to choose, pick the Vagrant method.

Vagrant
-------

The `Vagrant`_ development environment is set up using `Ansible`_.

To get started, install Vagrant and Ansible. On Fedora::

    $ sudo dnf install vagrant libvirt vagrant-libvirt vagrant-sshfs ansible

Next, clone the repository and start the Vagrant machine::

    $ git clone https://github.com/fedora-infra/anitya.git
    $ cd anitya
    $ vagrant up
    $ vagrant reload
    $ vagrant ssh

When you log in you'll be presented with a message of the day with more details
about the environment.

To start the Anitya instance in vagrant you can run::

    $ systemctl --user start anitya

You may then access Anitya on your host at::

    http://127.0.0.1:5000

By default, Anitya imports the production database so you've got something
to start with. If instead you prefer an empty database, add the following
to the Ansible provisioner inside your `Vagrantfile`::

    ansible.extra_vars = { import_production_database: false }

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

To run libraries.io service simply run::

   $ librariesio_consumer.py

To run check service simply run::

   $ check_service.py


Python virtualenv
-----------------

Anitya can also be run in a Python virtualenv. For Fedora::

    $ git clone https://github.com/fedora-infra/anitya.git
    $ cd anitya
    $ sudo dnf install python3-virtualenvwrapper
    $ source /usr/bin/virtualenvwrapper.sh
    $ mkvirtualenv anitya
    $ workon anitya

Issuing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Next, install Anitya::

    (anitya)$ pip install -r test_requirements.txt
    (anitya)$ pip install -e .

Create the database, by default it will be a sqlite database located at
``/var/tmp/anitya-dev.sqlite``::

    (anitya) $ python createdb.py

You can start the development web server included with Flask with::

    (anitya)$ FLASK_APP=anitya.wsgi flask run

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

    wheel
    twine
    towncrier

If you are a maintainer and wish to make a release, follow these steps:

1. Change the version in ``anitya.__init__.__version__``. This is used to set the
   version in the documentation project and the setup.py file.

2. Add any missing news fragments to the ``news`` folder.

3. Get authors of commits by ``python get-authors.py``.

.. note::
   This script must be executed in ``news`` folder, because it
   creates files in current working directory.

4. Generate the changelog by running ``towncrier``.

.. note::
    If you added any news fragment in the previous step, you might see ``towncrier``
    complaining about removing them, because they are not committed in git.
    Just ignore this and remove all of them manually; release notes will be generated
    anyway.

5. Remove every remaining news fragment from ``news`` folder.

6. Generate new DB schema image by running ``./generate_db_schema`` in ``docs`` folder.

7. Commit your changes with message *Anitya <version>*.

8. Tag a release with ``git tag -s <version>``.

9. Don't forget to ``git push --tags``.

10. Sometimes you need to also do ``git push``.

11. Build the Python packages with ``python setup.py sdist bdist_wheel``.

12. Upload the packages with ``twine upload dist/<dists>``.


Fedora messaging schema
-----------------------

To do the release you need following python packages installed::

    wheel
    twine

If you are a maintainer and wish to make a release of Anitya fedora messaging schema, follow these steps:

1. Enter ``anitya_schema`` directory.
   
2. Change the version in ``setup.py``.

3. Commit your changes with message *Anitya schema <version>*.

4. Don't forget to ``git push``.
   
5. Build the Python packages with ``python setup.py sdist bdist_wheel``.

6. Upload the packages with ``twine upload dist/<dists>``.

.. _Ansible: https://www.ansible.com/
.. _Vagrant: https://vagrantup.com/
