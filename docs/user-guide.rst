==========
User Guide
==========

Anitya attempts to select reasonable default settings for projects and in many
cases, these should work just fine. However, there are millions of software
projects out there and some do not follow common release methods. In those
cases, Anitya offers more flexible tools.

In this chapter of documentation you can find use cases that could be performed
by user in Anitya.

For use cases which needs admin permissions, please refer to :doc:`admin-user-guide`.


Logging in
==========

To `log in`_ to Anitya you need to have an account. Anitya itself doesn't provide
any way to create an account, but it provides option to log in with 3rd party
account. Currently you can log in with either Fedora account or use custom openid
server.


Logging out
===========

If you are currently logged in Anitya, you can log out by clicking on `logout`_
link in the page header.


Listing Projects
================

Anitya provides multiple ways of listing the available projects. All options
are accessible from *projects* menu in site header. You don't need to be logged
in to list the projects.

From this menu you can choose from these options:

* `all`_ will show you table containing all the projects available in Anitya
  sorted by name.
* `updated`_ will show you table containing all the projects that Anitya checked
  without issue. This table is sorted by the time the last check was done.
* `failed to update`_ will show you table containing all the projects that Anitya
  failed to check for new version. On this page you can find number of unsuccessful
  attempts and the reason for the error. This table is sorted by number of unsuccessful
  attempts.
* `never updated`_ will show you table containing all the projects that Anitya never
  checked without an issue. In most cases this means that the project is incorrectly
  set up. They are ordered by the date of creation with the oldest on the top of table.
* `archived`_ will show you projects, that are archived and Anitya no longer checks
  for new versions of these projects. The archived project can no longer be edited, but
  it is good to have them available for history.

Each option allows you to filter the list by using fields above the table. These
fields are supporting patterns. For example you can search for projects ending
with ``py`` by typing ``*py``.


Finding Project by Name
=======================

To find project by name quickly you can use a search field in top of the page.
This field supports pattern recognition. For example you can search for projects ending
with ``py`` by typing ``*py``.


.. _creating-project:

Creating New Project
====================

You can `create new projects`_ in the web interface if you are logged in.
When you create a new project, you must select a :term:`backend` to fetch
the version with. If the project is released in several places, please use
the backend for the language :term:`ecosystem`. For example, if a project is
hosted on `GitHub`_ and publishes releases to `PyPI`_, use the PyPI backend.

.. note::
    Occasionally projects stop publishing releases to their ecosystem's package
    index, but continue to tag releases. In those cases, it's fine to use the
    backend for the source hosting service (GitHub, BitBucket, etc.) the project
    is using.

Bellow you will find the fields currently available on project with description.


Project Name
------------

The project name should match the upstream project name. Duplicate project names
are allowed as long as the projects are not part of the same ecosystem. That is,
you can have two projects called ``msgpack``, but you cannot have two projects
called ``msgpack`` that are both in the ``PyPI`` ecosystem.

.. note::
    When project is not part of any ecosystem, duplicate projects are detected
    based on the homepage of project.


Homepage
--------

Homepage of the project. If the project doesn't have any homepage you could use the URL
where project is hosted.


Backends
--------

The backend of a project tells Anitya how to retrieve the versions of the
project.

The backends available are:

* **BitBucket** for projects hosted on `BitBucket <https://bitbucket.org>`_

  You need to provide **BitBucket owner/project**. For example if project is hosted on
  *https://bitbucket.org/zzzeek/sqlalchemy* this field needs to contain *zzzeek/sqlalchemy*

* **CPAN** for perl projects hosted on `CPAN <https://www.cpan.org/>`_

* **CRAN** for R projects hosted on `CRAN <https://cran.r-project.org/>`_

* **crates.io** for crates hosted on `crates.io <https://crates.io/>`_

* **Debian project** for projects hosted on the
  `Debian ftp <http://ftp.debian.org/debian/pool/main/>`_

* **Drupal6** for Drupal6 modules hosted on
  `drupal.org <https://drupal.org/project/>`_

* **Drupal7** for Drupal7 modules hosted on
  `drupal.org <https://drupal.org/project/>`_

* **folder** for projects whose release archives are provided in a
  basic apache folder or modified one.

  You need to provide **Version URL** where the archives could be found.

* **Freshmeat** for projects hosted on
  `freshmeat.net <http://freshmeat.net/>`_ / `freecode.com <http://freecode.com/>`_

* **GitHub** for projects hosted on `github.com <https://github.com/>`_.
  This backend is using `Github v4 API <https://developer.github.com/v4/>`_.
  
  You need to provide **GitHub owner/project**. For example if project is hosted on
  *https://github.com/zzzeek/sqlalchemy* this field needs to contain *zzzeek/sqlalchemy*.

  When the **GitHub** backend is selected you can also check the option to **Check releases
  instead of tags**, this will tell Anitya to retrieve GitHub releases instead of tags.
  It could be helpful when project is using tags for other things than just releases.

* **GitLab** for projects hosted on
  `GitLab server <https://about.gitlab.com/>`_.
  This backend is using `GitLab API v4 <https://docs.gitlab.com/ee/api/README.html>`_.

  You need to provide **GitLab project url** which needs to point to project root on
  GitLab server.

* **GNOME** for projects hosted on
  `download.gnome.org <https://download.gnome.org/sources/>`_

* **GNU Project** for projects hosted on `gnu.org <https://www.gnu.org/software/>`_
 
* **Google code** for projects hosted on
  `code.google.com <https://code.google.com/>`_

* **Hackage** for projects hosted on
  `hackage.haskell.org <https://hackage.haskell.org/>`_

* **Launchpad** for projects hosted on
  `launchpad.net <https://launchpad.net/>`_

* **Maven Central** for projects hosted on
  `maven.org <https://search.maven.org/>`_

* **npmjs** for projects hosted on `npmjs.org <https://www.npmjs.org/>`_

* **Packagist** for projects hosted on
  `packagist.org <https://packagist.org/>`_

  You need to provide **Packagist owner/group**. For example if project is hosted on
  *https://packagist.org/packages/phpunit/php-code-coverage* this field needs to contain
  *phpunit/php-code-coverage*

* **pagure** for projects hosted on
  `pagure.io <https://pagure.io/>`_

* **PEAR** for projects hosted on
  `pear.php.net <https://pear.php.net/>`_

* **PECL** for projects hosted on
  `pecl.php.net <https://pecl.php.net/>`_

* **PyPI** for projects hosted on
  `pypi.python.org <https://pypi.python.org/pypi>`_

* **Rubygems** for projects hosted on
  `rubygems.org <https://rubygems.org/>`_

* **Sourcefoge** for projects hosted on
  `sourceforge.net <https://sourceforge.net/>`_

  You need to provide **Sourceforge name** if the name on RSS feed is different then the
  project name on Sourceforge.

* **Stackage** for projects hosted on
  `www.stackage.org <https://www.stackage.org/>`_

If your project cannot be used with any of these backend you can always try
the **custom** backend. **custom** backend is for projects who require a more
flexible way of finding their version.

The custom backend requires two arguments:

* **Version URL** is the url of the page where the versions information can be
  found, for example for `banshee <http://banshee.fm/>`_
  that would be `their download page <http://banshee.fm/download/>`_

.. note::
    It's possible to provide a "glob" for projects that place their tarballs
    in multiple directories. For example, gcc uses
    ``https://ftp.gnu.org/gnu/gcc/*/`` to find the tarballs in each version
    directory.

* **Regex** is a regular expression using the Python `re`_ syntax to find the
  releases on the **Version URL** page.

.. note:: In most cases, you can set the **Regex** to `DEFAULT` which will
          make Anitya use its default regular expression:

          ::

             	(?i){project name}(?:[-_]?(?:minsrc|src|source))?[-_]([^-/_\s]+?)(?:[-_](?:minsrc|src|source|asc|release))?\.(?:tar|t[bglx]z|tbz2|zip)

.. _version-scheme:

Version Scheme
--------------

Version scheme is used for sorting the retrieved versions for the projects.
Anitya provides three different versions scheme.

* **RPM** corresponds to versioning used by `RPM packages <https://docs.fedoraproject.org/en-US/packaging-guidelines/Versioning/>`_ 

* **Calendar** corresponds to project versions in format described
  on `Calendar Versioning <https://calver.org/>`_

* **Semantic** corresponds to project versions in format described
  on `Semantic Versioning 2.0.0 <https://semver.org/>`_

.. note::
    Anitya currently doesn't work well with projects that are using multiple
    versions schemes throughout their life. For these projects just use the most
    recent scheme and the rest will be moved to bottom unsorted.


Version Prefix
--------------

The version prefix can be used to retrieve the exact version number when the
upstream maintainer prefixes its versions.

For example, if the project's version are: ``foo-1.2``, you can set the
version prefix to ``foo-`` to tell Anitya how to get the version ``1.2``.

You can specify multiple prefixes by separating them by ``;``. For example
``foo-;v`` will remove both ``foo-`` and ``v`` from retrieved versions.

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


Pre-release filter
------------------

Sometimes the recognition of stable and unstable versions by :ref:`version-scheme` isn't
working for the project and in this field you can specify strings that will be considered
as unstable release.

For example, if the project's version are: ``1.2alpha``, you can set the
pre-release filter to ``alpha`` to tell Anitya to treat this release as unstable.

You can specify multiple filters by separating them by ``;``. For example
``alpha;beta`` will mark versions with ``alpha`` and ``beta`` as unstable.

.. note::
   This filter is applied after recognition of unstable versions by :ref:`version-scheme`.
   So the filter is not needed for cases where :ref:`version-scheme` is able to recognize
   unstable versions.


Version filter
--------------

Sometimes the upstream project is tagging things that aren't releases. For this case
you can use this field to specify which version shouldn't be retrieved by Anitya.

For example, if the project has tag ``xyz``, you can set the
version filter to ``xyz`` to tell Anitya to ignore this tag.

You can specify multiple filters by separating them by ``;``. For example
``notrelease;test`` will ignore versions with ``notrelease`` and ``test``.

.. note::
   This filter is not applied on version that is already retrieved, but if you
   create the filter and the admin deletes the version, it will not be retrieved
   again.


Regular Expressions
-------------------

Sometimes you need to use a custom regular expression to find the version
on a page. Anitya accepts user-defined regular expressions using the Python
`re`_ syntax. This option is only available when using **custom** backend.

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


Check latest release on submit
------------------------------

This option will tell the Anitya to do a check for versions when the project is
submitted. In other case the project is scheduled and checked on next run check service,
this service is doing checks regularly multiple times a day.


Distro (optional)
-----------------

When creating a new project in Anitya you can specify distribution in which the project
could be found. You can select from distributions that are already available in Anitya
or you can create a new one later, see :ref:`creating-distribution`.


Package (optional)
------------------

If you selected the distribution you must write the package name under which the project
is known in distribution. For example python projects in Fedora distribution are prefixed
with ``python3-`` prefix, so the project *alembic* will be called ``python3-alembic`` in
Fedora. However the name of the project in Anitya should still be *alembic*.


Test check
----------

You can test your changes before submitting by using the **Test check** button at the bottom
of the project form. This will take the current values from the fields and do a check for
new version with temporary project. This is very useful if you are doing multiple changes
and you are not sure of the output.


Editing Project
===============

You can edit any project in the web interface if you have logged in.
The editing of a project could be done from the project page by clicking
on button **Edit**.

The editing is very similar to creating a new project with the exception of optional
fields which are missing. For field reference please check :ref:`creating-project`.


.. _creating-distribution-mapping:

Creating New Distribution Mapping
=================================

To add a new mapping of the project to distribution you can use **Add new distribution mapping**
under the *Mappings* table on project page.

This opens a new page which allows you to add a new mapping for the distribution of your choice.


Distribution
------------

You can select from distributions that are already available in Anitya
or you can create a new one and add the mapping later, see :ref:`creating-distribution`
for how to create a new distribution.


Package name
------------

If you selected the distribution you must write the package name under which the project
is known in distribution. For example python projects in Fedora distribution are prefixed
with ``python3-`` prefix, so the project *alembic* will be called ``python3-alembic`` in
Fedora.


Editing Distribution Mapping
============================

To edit existing mapping of the project to distribution you can use **Edit** button beside
corresponding mapping in the *Mappings* table on project page.

This opens a new page which is similar to :ref:`creating-distribution-mapping` page.
See :ref:`creating-distribution-mapping` for more info about fields.


Flagging a Project
==================

If you find a project which contains bad version, is duplicate, or is no longer supported upstream,
you can flag this project. To flag a project you can use **Flag** button in top of the project
page. This will redirect you to *Flag project* form, where you need to provide a reason. The flagged
project will be later reviewed by admin user. 

.. _listing-distributions:

Listing Distributions
=====================

Anitya provides a way to look at all the distributions that Anitya knows about and that could be used
when working with project mapping. To list all the distributions just click on the `distros`_ link in
the header of page. This will show you a page with list of all the distributions sorted by name.


.. _creating-distribution:

Creating a New Distribution
===========================

If you are missing any distribution in Anitya you can add it. To add a new distribution first list the
existing distributions, see :ref:`listing-distributions`, and then click `Add a new distribution`_ button.
This will redirect you to a new page where you can fill out a distribution name and submit the new
distribution.

Obtaining an API Token
======================

If you need to communicate through API with Anitya (see :doc:`api` for more info) you will need
an API token for any operation that is changing data in Anitya. To obtain one, you need to
click on the `settings`_ link in page header. This will redirect you to your user settings page.
Here you can see your User Id, which could be needed by admin user for some use cases,
and API tokens. You can create a new token here, just provide some description (optional)
and click **Create API Token** button.

Removing an API Token
=====================

If you wish to remove an existing API token created for your account, you need to
click on the `settings`_ link in page header. This will redirect you to your user settings page.
Here you can see your User Id, which could be needed by admin user for some use cases,
and API tokens. You can remove a existing token here, just click **Remove API Token** button
beside the API token you want to remove.

Reporting Issues
================

You can report problems on our `issue tracker`_. The `source code`_ is also
available on GitHub. The development team hangs out in ``#fedora-apps`` on the
freenode network. Please do stop by and say hello.

.. _log in: https://release-monitoring.org/login
.. _logout: https://release-monitoring.org/logout
.. _all: https://release-monitoring.org/projects
.. _updated: https://release-monitoring.org/projects/updates
.. _failed to update: https://release-monitoring.org/projects/updates/failed
.. _never updated: https://release-monitoring.org/projects/updates/never_updated
.. _archived: https://release-monitoring.org/projects/updates/archived
.. _distros: https://release-monitoring.org/distros
.. _settings: https://release-monitoring.org/settings
.. _Add a new distribution: https://release-monitoring.org/distro/add
.. _create new projects: https://release-monitoring.org/project/new
.. _GitHub: https://github.com/
.. _PyPI: https://pypi.python.org/
.. _re: https://docs.python.org/3/library/re.html
.. _issue tracker: https://github.com/fedora-infra/anitya/issues
.. _source code: https://github.com/fedora-infra/anitya
