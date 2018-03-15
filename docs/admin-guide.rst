====================
Administration Guide
====================

This guide is intended for administrators of an Anitya deployment.


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


Services
========

Anitya is made up of a WSGI application, an update script that should be run at
regular intervals via cron or similar, an optional fedmsg consumer, and requires
a database.


WSGI Application
----------------

The WSGI application is located at ``anitya.wsgi``. This application handles the
web interface for creating, updating, and viewing projects. It also offers a
REST API.


Update Script
-------------

The script that checks for project updates is located at
``files/anitya_cron.py`` in the git repository and Python package.


Libraries.io fedmsg Consumer
----------------------------

This optional service listens to a ZeroMQ socket for messages published by the
`libraries.io`_ service. This requires that a bridge from Server-Sent Events
(SSE) to ZeroMQ be running.

To run this, set the ``anitya.libraryio.enabled`` key to ``True`` in your fedmsg
configuration and run the ``fedmsg-hub`` service.


Database
--------

Anitya should work with any SQL database, but it is only tested with SQLite
and PostgreSQL. It is recommended to use PostgreSQL in a production deployment.


.. _libraries.io: https://libraries.io/
