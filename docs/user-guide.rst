==========
User Guide
==========

Anitya attempts to select reasonable default settings for projects and in many
cases, these should work just fine. However, there are millions of software
projects out there and some do not follow common release methods. In those
cases, Anitya offers more flexible tools.


Creating a New Project
======================

You can `create new projects`_ in the web interface if you have logged in.
When you create a new project, you must select a :term:`backend` to fetch
the version with. If the project is released in several places, please use
the backend for the language :term:`ecosystem`. For example, if a project is
hosted on `GitHub`_ and publishes releases to `PyPI`_, use the PyPI backend.

.. note::
    Occasionally projects stop publishing releases to their ecosystem's package
    index, but continue to tag releases. In those cases, it's fine to use the
    backend for the source hosting service (GitHub, BitBucket, etc.) the project
    is using.


Backends
--------

The backend of a project tells Anitya how to retrieve the versions of the
project.

The backends available are:

* ``cpan.py`` for perl projects hosted on `CPAN <https://www.cpan.org/>`_
* ``cran.py`` for R projects hosted on `CRAN <https://cran.r-project.org/>`_
* ``crates.py`` for crates hosted on `crates.io <https://crates.io/>`_
* ``debian.py`` for projects hosted on the
  `Debian ftp <http://ftp.debian.org/debian/pool/main/>`_
* ``drupal6.py`` for Drupal6 modules hosted on
  `drupal.org <https://drupal.org/project/>`_
* ``drupal7.py`` for Drupal7 modules hosted on
  `drupal.org <https://drupal.org/project/>`_
* ``folder.py`` for projects whose release archives are provided in a folder
  basic apache folder or modified one.
* ``freshmeat.py`` for projects hosted on
  `freshmeat.net <http://freshmeat.net/>`_ / `freecode.com <http://freecode.com/>`_
* ``github.py`` for projects hosted on `github.com <https://github.com/>`_
  using `Github v4 API <https://developer.github.com/v4/>`
* ``gitlab.py`` for projects hosted on
  `GitLab server <https://about.gitlab.com/>_`.
  This backend is using `GitLab API v4 <https://docs.gitlab.com/ee/api/README.html>_`
* ``gnome.py`` for projects hosted on
  `download.gnome.org <https://download.gnome.org/sources/>`_
* ``gnu.py`` for projects hosted on `gnu.org <https://www.gnu.org/software/>`_
* ``google.py`` for projects hosted on
  `code.google.com <https://code.google.com/>`_
* ``hackage.py`` for projects hosted on
  `hackage.haskell.org <https://hackage.haskell.org/>`_
* ``launchpad.py`` for projects hosted on
  `launchpad.net <https://launchpad.net/>`_
* ``npmjs.py`` for projects hosted on `npmjs.org <https://www.npmjs.org/>`_
* ``pear.py`` for projects hosted on
  `pear.php.net <https://pear.php.net/>`_
* ``pecl.py`` for projects hosted on
  `pecl.php.net <https://pecl.php.net/>`_
* ``pypi.py`` for projects hosted on
  `pypi.python.org <https://pypi.python.org/pypi>`_
* ``rubygems.py`` for projects hosted on
  `rubygems.org <https://rubygems.org/>`_
* ``sourceforge.py`` for projects hosted on
  `sourceforge.net <https://sourceforge.net/>`_
* ``stackage.py`` for projects hosted on
  `www.stackage.org <https://www.stackage.org/>`_

If your project cannot be used with any of these backend you can always try
the ``custom`` backend.

* ``custom.py`` for projects who require a more flexible way of finding their
  version.


The custom backend requires two arguments:

* ``version_url`` the url of the page where the versions information can be
  found, for example for `banshee <http://banshee.fm/>`_
  that would be `their download page <http://banshee.fm/download/>`_

.. note::
    It's possible to provide a "glob" for projects that place their tarballs
    in multiple directories. For example, gcc uses
    ``https://ftp.gnu.org/gnu/gcc/*/`` to find the tarballs in each version
    directory.

* ``regex`` a regular expression using the Python `re`_ syntax to find the
  releases on the ``version_url`` page.

.. note:: In most cases, you can set the ``regex`` to `DEFAULT` which will
          make anitya use its default regular expression:

          ::

            <package name>(?:[-_]?(?:minsrc|src|source))?[-_]([^-/_\s]+?)(?i)(?:[-_](?:minsrc|src|source|asc|release))?\.(?:tar|t[bglx]z|tbz2|zip)


Project Name
------------

The project name should match the upstream project name. Duplicate project names
are allowed as long as the projects are not part of the same ecosystem. That is,
you can have two projects called ``msgpack``, but you cannot have two projects
called ``msgpack`` that are both in the ``PyPI`` ecosystem.

.. note::
    When project is not part of any ecosystem, duplicate projects are detected
    based on the homepage of project.


Version Prefix
--------------

The version prefix can be used to retrieve the exact version number when the
upstream maintainer prefixes its versions.

For example, if the project's version are: ``foo-1.2``, you can set the
version prefix to ``foo-`` to tell Anitya how to get the version ``1.2``.

.. note::
    It's common for projects to prefix their source control tags with a ``v`` when
    making a release. Anitya will automatically strip this from versions it finds.

More concrete examples:

* `junit <https://github.com/junit-team/junit/tags>`_ tags are of the form:
  ``r<version>``, to retrieve the version, one can set the version prefix
  to ``r``.

* `fdupes <https://github.com/adrianlopezroche/fdupes/tags>`_ tags are of
  the form ``fdupes-<version>``, for this project, the version prefix can
  be set to ``fdupes-``.


Regular Expressions
-------------------

Sometimes you need to use a custom regular expression to find the version
on a page. Anitya accepts user-defined regular expressions using the Python
`re`_ syntax.

The simplest way to check your regular expression is to open a python shell
and test it.

Below is an example on how it can be done::

  >>> url = 'http://www.opendx.org/download.html'
  >>>
  >>> import requests
  >>> import re
  >>> text = requests.get(url).text
  >>> re.findall('version.is ([\d]*)\.', text)
  [u'4']
  >>> re.findall('version.is ([\d\.-]*)\.', text)
  [u'4.4.4']

If you prefer graphical representation you can use
`Debuggex <https://www.debuggex.com/>`_.

The regular expression ``version.is ([\d\.]*)\.`` can then be provided to
anitya and used to find the new releases.

.. note::
    Only the captured groups are used as version, delimited by dot.
    For example: ``1_2_3`` could be captured by regular expression ``(\d)_(\d)_(\d)``.
    This will create version ``1.2.3``.


Integrating with Anitya
=======================


fedmsg
------

`fedmsg <http://www.fedmsg.com>`_ is a message bus. In other words it is a
system that allows for the sending and receiving of notifications between
applications.  For anitya, every action made on the application is
announced/broadcasted on this bus, allowing anyone listening to it to act
immediately instead of (for example) polling hourly all the data, looking for
changes, and acting then. For the full list of messages Anitya sends, see
the `fedmsg topic documentation`_.

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
^^^^^^^^^^^

::

    import fedmsg

    # Yield messages as they're available from a generator
    for name, endpoint, topic, msg in fedmsg.tail_messages():
        print topic, msg


From the shell
^^^^^^^^^^^^^^

::

    $ fedmsg-tail --really-pretty


Reporting Issues
================

You can report problems on our `issue tracker`_. The `source code`_ is also
available on GitHub. The development team hangs out in ``#fedora-apps`` on the
freenode network. Please do stop by and say hello.


.. _create new projects: https://release-monitoring.org/project/new
.. _GitHub: https://github.com/
.. _PyPI: https://pypi.python.org/
.. _re: https://docs.python.org/3/library/re.html
.. _issue tracker: https://github.com/release-monitoring/anitya/issues
.. _source code: https://github.com/release-monitoring/anitya
.. _fedmsg topic documentation:
    https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#anitya
