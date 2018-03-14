=================
Development Guide
=================

Anitya welcomes contributions! Our issue tracker is located on
`GitHub <https://github.com/release-monitoring/anitya/issues>`_.


Contribution Guidelines
=======================

When you make a pull request, someone from the release-monitoring organization
will review your code. Please make sure you follow the guidelines below:

Python Support
--------------

Anitya supports Python 2.7 and Python 3.4 or greater so please ensure the code
you submit works with these versions. The test suite will run against all supported
Python versions to make this easier.

Code Style
----------

We follow the `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python.
The test suite includes a test that enforces the required style, so all you need to do is
run the tests to ensure your code follows the style. If the unit test passes, you are
good to go!

Unit Tests
----------

The test suites can be run using `tox <http://tox.readthedocs.io/>`_ by simply running
``tox`` from the repository root. These tests include unit tests, a linter to ensure
Python code style is correct, and checks the documentation for Sphinx warnings or
errors.

All tests must pass. All new code should have 100% test coverage.
Any bugfix should be accompanied by one or more unit tests to demonstrate the fix.
If you are unsure how to write unit tests for your code, we will be happy to help
you during the code review process.

Documentation
-------------

Anitya uses `sphinx <http://www.sphinx-doc.org/>`_ to create its documentation.
New packages, modules, classes, methods, functions, and attributes all should be
documented using `"Google style" <http://www.sphinx-doc.org/en/latest/ext/example_google.html>`_
docstrings. For historical reasons you may encounter plain reStructuredText-style
docstrings. Please consider converting them and opening a pull request!

Python API documentation is automatically generated from the code using Sphinx's
`autodoc <http://www.sphinx-doc.org/en/stable/tutorial.html#autodoc>`_ extension.
HTTP REST API documentation is automatically generated from the code using the
`httpdomain <https://pythonhosted.org/sphinxcontrib-httpdomain/>`_ extension.


Development Environment
=======================

There are two options for setting up a development environment. If you're not
sure which one to choose, pick the Vagrant method.

Vagrant
-------

The `Vagrant`_ development environment is set up using `Ansible`_.

To get started, install Vagrant and Ansible. On Fedora::

    $ sudo dnf install vagrant libvirt vagrant-libvirt vagrant-sshfs ansible

Next, clone the repository and configure your Vagrantfile::

    $ git clone https://github.com/release-monitoring/anitya.git
    $ cd anitya
    $ cp Vagrantfile.example Vagrantfile
    $ vagrant up
    $ vagrant reload
    $ vagrant ssh

You may then access Anitya on your host at::

    http://127.0.0.1:5000

When you log in you'll be presented with a message of the day with more details
about the environment.

By default, Anitya imports the production database so you've got something
to work off of. If instead you prefer an empty database, add the following
to the Ansible provisioner inside your `Vagrantfile`::

    ansible.extra_vars = { import_production_database: false }

Python virtualenv
-----------------

Anitya can also be run in a Python virtualenv. For Fedora::

    $ git clone https://github.com/release-monitoring/anitya.git
    $ cd anitya
    $ sudo dnf install python3-virtualenv
    $ virtualenv-3 anitya-env
    $ source anitya-env/bin/activate

Issuing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Next, install Anitya::

    (anitya-env)$ pip install -r test_requirements.txt
    (anitya-env)$ pip install -e .

Create the database, by default it will be a sqlite database located at
``/var/tmp/anitya-dev.sqlite``::

    (anitya-env) $ python createdb.py

You can start the development web server included with Flask with::

    (anitya-env)$ FLASK_APP=anitya.wsgi flask run

If you want to change the application's configuration, create a valid configuration
file and start the application with the ``ANITYA_WEB_CONFIG`` environment variable
set to the configuration file's path.


Listening for local event announcements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To listen for local event announcements over the Federated Message Bus,
first start a local relay in the background::

    $ fedmsg-relay --config-filename fedmsg.d/fedmsg-config.py &

And then display the received messages in the local console::

    $ fedmsg-tail --config fedmsg.d/fedmsg-config.py --no-validate --really-pretty

These commands will pick up the local config automatically if you're in
the Anitya checkout directory, but being explicit ensures they don't silently
default to using the global configuration.

To display the messages, we turn off signature validation (since the local
server will be emitting unsigned messages) and pretty-print the received JSON.

Refer to the `fedmsg consumer API <http://www.fedmsg.com/en/latest/consuming/>`_
for more details on receiving event messages programmatically.


Tips
----

Anitya publishes fedmsgs, and these are viewable with ``fedmsg-tail``::

    $ workon anitya
    $ fedmsg-tail

This will also show you all incoming messages from `libraries.io's <https://libraries.io/>`_
SSE feed.


.. _Ansible: https://www.ansible.com/
.. _Vagrant: https://vagrantup.com/
