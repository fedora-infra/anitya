Getting started with fedmsg/anitya
==================================

`fedmsg <http://www.fedmsg.com>`_ is a bus. In other words it is a system
that allows to send and receive notifications between applications.
For anitya, every action made on the application is announced/broadcasted
on this bus, allowing anyone listening to it to act immediately instead of
(for example) pull hourly all the data to see the changes and act then.




To start receiving `fedmsg <http://www.fedmsg.com>`_ messages from anitya,
it is as simple as:

* install ``fedmsg`` the way you want:

On Fedora ::

  yum install fedmsg

On Debian ::

  apt-get install fedmsg

Via pip ::

  pip install fedmsg

* in the configuration file: ``endpoints.py``, make sure you activate the
  anitya endpoint

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


Form the shell
--------------

::

    $ fedmsg-tail --really-pretty
