
.. image:: https://img.shields.io/pypi/v/anitya.svg
  :target: https://pypi.org/project/anitya/

.. image:: https://img.shields.io/pypi/pyversions/anitya.svg
  :target: https://pypi.org/project/anitya/

.. image:: https://readthedocs.org/projects/anitya/badge/?version=latest
  :alt: Documentation Status
  :target: https://anitya.readthedocs.io/en/latest/?badge=latest

.. image:: https://codecov.io/gh/fedora-infra/anitya/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/fedora-infra/anitya
  
.. image:: https://travis-ci.org/fedora-infra/anitya.svg?branch=master
  :target: https://travis-ci.org/fedora-infra/anitya
  
.. image:: https://img.shields.io/lgtm/alerts/g/fedora-infra/anitya.svg?logo=lgtm&logoWidth=18
  :target: https://lgtm.com/projects/g/fedora-infra/anitya/alerts/

.. image:: https://img.shields.io/lgtm/grade/javascript/g/fedora-infra/anitya.svg?logo=lgtm&logoWidth=18
  :target: https://lgtm.com/projects/g/fedora-infra/anitya/context:javascript
  
.. image:: https://img.shields.io/lgtm/grade/python/g/fedora-infra/anitya.svg?logo=lgtm&logoWidth=18
  :target: https://lgtm.com/projects/g/fedora-infra/anitya/context:python
  

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
