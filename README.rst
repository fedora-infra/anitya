.. image:: https://codecov.io/gh/release-monitoring/anitya/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/release-monitoring/anitya

======
Anitya
======

Anitya is a release monitoring project. It provides a user-friendly interface
to add, edit, or browse projects. A cron job can be configured to regularly
scan for new releases of projects. When Anitya discovers a new release for a
project, it publishes a ZeroMQ message via `fedmsg <http://fedmsg.com>`_.
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
