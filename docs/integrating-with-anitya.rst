=======================
Integrating with Anitya
=======================

This chapter describes ways how you can integrate Anitya with your solution.


Fedora messaging
================

`Fedora messaging`_ is a message bus. In other words it is a
system that allows for the sending and receiving of notifications between
applications.  For anitya, every action made on the application is
announced/broadcasted on this bus, allowing anyone listening to it to act
immediately instead of (for example) polling hourly all the data, looking for
changes, and acting then.

To start receiving `Fedora messaging`_ messages from anitya,
it is as simple as:

* install ``Fedora messaging`` the way you want:

On Fedora ::

  dnf install fedora-messaging

Via pip ::

  pip install fedora-messaging

For how to start a local broker for `fedora messaging`. See
`Fedora messaging documentation <https://fedora-messaging.readthedocs.io/en/latest/quick-start.html#local-broker>`_.

List of fedora messaging topics
-------------------------------

This section will list all the `Fedora messaging`_ topics Anitya is
sending and in what situation.

* *anitya.distro.add* is sent when a new distribution is created.
* *anitya.distro.edit* is sent when an existing distribution is edited.
* *anitya.distro.remove* is sent when an existing distribution is deleted.
* *anitya.project.add* is sent when a new project is added.
* *anitya.project.edit* is sent when an existing project is edited.
* *anitya.project.remove* is sent when an existing project is deleted.
* *anitya.project.flag* is sent when a new flag is created on project.
* *anitya.project.flag.set* is sent when a status of flag is changed.
* *anitya.project.map.new* is sent when a new mapping to distribution
  is created on project.
* *anitya.project.map.update* is sent when an existing mapping on project
  is edited.
* *anitya.project.map.remove* is sent when an existing mapping on project
  is deleted.
* *anitya.project.version.update* is sent when a new release is found for
  the project. This topic is now deprecated.
* *anitya.project.version.update.v2* is sent when a new release is found
  for the project. This message differentiate between stable and
  not stable releases.
* *anitya.project.version.remove* is sent when an existing release is
  deleted from project.

You can found out more about Anitya messages in `Fedora messaging schema`_.
The schema should be used by every consumer that consumes Anitya messages.

.. _Fedora messaging: https://fedora-messaging.readthedocs.io/en/latest
.. _Fedora messaging schema: https://pypi.org/project/anitya-schema/
