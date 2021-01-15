====================
Administration Guide
====================

This guide is intended for administrators that are trying to deploy Anitya in their
environment. For reference you can check `release-monitoring.org`_ ansible
`deployment role`_ in Fedora infrastructure.


Installation
============

Anitya is not currently available in any distribution's default repository.
To install it from PyPI::

    $ pip install anitya

Configuration
=============

If the ``ANITYA_WEB_CONFIG`` environment variable is set to a file system path
Anitya can read, the configuration is loaded from that location. Otherwise, the
configuration is read from ``/etc/anitya/anitya.toml``. If neither can be read,
Anitya will log a warning and use its configuration defaults.

.. warning:: The default configuration for Anitya includes a secret key for
        web sessions. It is *not* safe to use the default configuration in a
        production environment.

Anitya uses TOML as its configuration format. A complete configuration file
with inline documentation is below.

.. include:: ../files/anitya.toml.sample
   :literal:

Anitya uses second configuration file for Fedora messaging. A sample
configuration file is bellow. To know more about the configuration of
fedora messaging please refer to
`fedora messaging configuration documentation <https://fedora-messaging.readthedocs.io/en/latest/configuration.html>`_.

.. include:: ../files/config.toml.sample
   :literal:

Services
========

Anitya is made up of a :ref:`wsgi-app`, an :ref:`update-service` that could be run
separately, an optional :ref:`sse-client`, :ref:`sar-script`, and requires a :ref:`database`.

.. _wsgi-app:

WSGI Application
----------------

The WSGI application is located at ``anitya/wsgi.py``. This application handles the
web interface for creating, updating, and viewing projects. It also offers a
REST API.

There is also a ``anitya.wsgi`` file that could be used directly.
You can find example `anitya.wsgi <https://github.com/fedora-infra/anitya/blob/master/anitya.wsgi>`_
in Anitya repository.
You can use this file with Apache server or deploy it by flask. Fedora uses Apache
so you can look at their
`configuration <https://pagure.io/fedora-infra/ansible/blob/main/f/roles/openshift-apps/release-monitoring/templates/httpd.conf>`_.

.. _update-service:

Update Service
--------------

The service that checks for project updates is located at
``anitya/check_service.py`` in the git repository and Python package.
To enable it, just start this service.

.. note::
   This script should be also available system wide, installed by ```scripts``
   argument in python setup. See `python setup documentation`_
   for more info.

.. _sse-client:

Libraries.io SSE client
-----------------------

This optional service listens to SSE feed for messages published by the
`libraries.io`_ service.

The service is located at ``anitya/librariesio_consumer.py``. To enable
it just start the service.

.. note::
   This script should be also available system wide, installed by ```scripts``
   argument in python setup. See `python setup documentation`_
   for more info.

.. _sar-script:

SAR Script
----------

Subject Access Requests script is intended for handling GDPR users requests for
obtaining their data from Anitya. This script could be found in ``anitya/sar.py``.
It just connects to the database using Anitya configuration and takes out user
relevant data.

.. note::
   This script should be also available system wide, installed by ```scripts``
   argument in python setup. See `python setup documentation`_
   for more info.

.. _database:

Database
--------

Anitya should work with any SQL database, but it is only tested with SQLite
and PostgreSQL. It is recommended to use PostgreSQL in a production deployment.
The SQLite database can't work with update service, because it doesn't allow
database changes in parallel threads.

For creating a database schema you can use
`createdb.py script <https://github.com/fedora-infra/anitya/blob/master/createdb.py>`_
from Anitya repository.

After this you need to apply any migrations done above the basic database
schema. You can run the migrations by using the
`alembic tool <https://pypi.org/project/alembic/>`_. You can use the configuration
file `alembic.ini <https://github.com/fedora-infra/anitya/blob/master/alembic.ini>`_
from Anitya repository.

.. code-block:: bash

   alembic -c <path_to_alembic.ini> upgrade head

.. note::
   The migrations needs to be applied each time upgrade of Anitya is done.


Fedora messaging
----------------

The Anitya needs to connect to RabbitMQ server which will listen for it's messages. For deployment
of your own RabbitMQ server please look at the `official documentation <https://www.rabbitmq.com/>`_.


.. _libraries.io: https://libraries.io/
.. _release-monitoring.org: https://release-monitoring.org/
.. _deployment role: https://pagure.io/fedora-infra/ansible/blob/master/f/roles/openshift-apps/release-monitoring
.. _python setup documentation: https://docs.python.org/3/distutils/setupscript.html#installing-scripts

