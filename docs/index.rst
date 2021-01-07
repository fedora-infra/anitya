.. Anitya documentation master file, created by
   sphinx-quickstart on Tue Nov 22 14:46:31 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

======
Anitya
======

Anitya is a release monitoring project.

Its goal is to regularly check if a project has made a new release.
When Anitya discovers a new release for a project, it publishes a RabbitMQ message via
`fedora messaging <https://fedora-messaging.readthedocs.io/en/stable/>`_.
This makes it easy to integrate with Anitya and perform
actions when a new release is created for a project. For example, the Fedora project
runs a service called `the-new-hotness <https://github.com/fedora-infra/the-new-hotness/>`_
which files a Bugzilla bug against a package when the upstream project makes a new release.

Anitya provides a user-friendly interface to add, edit, or browse projects.

:Github page: https://github.com/fedora-infra/anitya

User Guide
==========

.. toctree::
   :maxdepth: 2

   user-guide
   admin-user-guide
   release-notes
   glossary

Admin Guide
===========

.. toctree::
   :maxdepth: 2

   admin-guide
   integrating-with-anitya

Developer Guide
===============

.. toctree::
   :maxdepth: 2

   api
   contributing
   database
