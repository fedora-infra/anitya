Getting started with anitya and fedmsg
======================================

`fedmsg <http://www.fedmsg.com>`_ is a message bus. In other words it is a
system that allows for the sending and receiving of notifications between
applications.  For anitya, every action made on the application is
announced/broadcasted on this bus, allowing anyone listening to it to act
immediately instead of (for example) polling hourly all the data, looking for
changes, and acting then.

To start receiving `fedmsg <http://www.fedmsg.com>`_ messages from anitya,
it is as simple as:

* install ``fedmsg`` the way you want:

On Fedora ::

  dnf install fedmsg

On Debian ::

  apt-get install fedmsg

Via pip ::

  pip install fedmsg

* in the configuration file: ``/etc/fedmsg.d/endpoints.py``, make sure you
  activate the anitya endpoint

  ::

    "anitya-public-relay": [
        "tcp://release-monitoring.org:9940",
    ],

From python
-----------

::

    import fedmsg

    # Yield messages as they're available from a generator
    for name, endpoint, topic, msg in fedmsg.tail_messages():
        print topic, msg


From the shell
--------------

::

    $ fedmsg-tail --really-pretty
