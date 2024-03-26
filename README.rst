
.. image:: https://img.shields.io/pypi/v/anitya.svg
  :target: https://pypi.org/project/anitya/

.. image:: https://img.shields.io/pypi/pyversions/anitya.svg
  :target: https://pypi.org/project/anitya/

.. image:: https://readthedocs.org/projects/anitya/badge/?version=latest
  :alt: Documentation Status
  :target: https://anitya.readthedocs.io/en/latest/?badge=latest
  
.. image:: https://img.shields.io/badge/renovate-enabled-brightgreen.svg
  :target: https://renovatebot.com/

.. image::  https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
  :target:  https://pre-commit.com/
  

======
Anitya
======

Anitya is a release monitoring project. It provides a user-friendly interface
to add, edit, or browse projects. A cron job can be configured to regularly
scan for new releases of projects. When Anitya discovers a new release for a
project, it publishes a RabbitMQ messages via `fedora messaging`_.
This makes it easy to integrate with Anitya and perform actions when a new
release is created for a project. For example, the Fedora project runs a service
called `the-new-hotness <https://github.com/fedora-infra/the-new-hotness/>`_
which files a Bugzilla bug against a package when the upstream project makes a
new release.

For more information, check out the `documentation`_!


Development
===========

For details on how to contribute, check out the `contribution guide`_.


.. _documentation: https://anitya.readthedocs.io/
.. _contribution guide: https://anitya.readthedocs.io/en/latest/contributing.html
.. _fedora messaging: https://fedora-messaging.readthedocs.io/en/latest
