Cnucnu Web
==========

Cnucnu is a project monitoring daily for new releases made by projects.

With this application, you can register an application you have interest in,
all you need to do this is the name of the project, its homepage, then a url
to a page providing the different version and a regular expression to find
the version in this page.


Project name
------------

The three names can be specified, the first is the cannonical name of
the project itself. After this, a name can be specified for the Fedora
package corresponding to this project and the same thing for the Debian
package.


Homepage URL
------------

This refers to the main URL of the project.


Version URL
-----------

For a number of forges of projects, Cnucnu has pre-set URLs, by simply
specifying one of these pre-set you spare yourself the work of finding the
best page to follow the new version.


Version Regex
-------------

For a number of forges/repositories of projects, Cnucnu has a number of
pre-set regular expression. You can use this if the project is using the
classic place/versioning system.


The default regex is::

    \b<package name>[-_]([^-/_\s]+?)(?i)(?:[-_](?:src|source))?\.(?:tar|t[bglx]z|tbz2|zip)\b

The other pre-set regex are:

* ``CPAN-DEFAULT`` remove `perl-` from the project name (if present) and use the default regex.
* ``PEAR-DEFAULT`` remove `php-pear-` from the project name (if present) and use the default regex.
* ``PECL-DEFAULT`` remove `php-pecl-` from the project name (if present) and use the default regex.
* ``HACKAGE-DEFAULT`` remove `ghc-` from the project name (if present) and use the default regex.
* ``FM-DEFAULT`` a dedicated regex for FreshMeat::

        <a href="/projects/[^/]*/releases/[0-9]*">([^<]*)</a>

* ``DIR-LISTING-DEFAULT`` a dedicated regex for apache directory listing::

    href="([0-9][0-9.]*)/"

* ``RUBYGEMS-DEFAULT`` a dedicated regex for rubygems to match the version of gem in JSON::

    "gem_uri":"http:\/\/rubygems.org\/gems\/<project name>-([0-9.]*?)\.gem"

* ``NPM-DEFAULT`` remove `nodejs-` prefix from the project name and use a dedicated regex for npmjs.org::

    "version":"([0-9.]*?)"


Dénouement
----------

You can report `issues
<https://github.com/fedora-infra/cnucnuweb/issues>`_ and find the
`source <https://github.com/fedora-infra/cnucnuweb/>`_ on github.
The development team hangs out in ``#fedora-apps``. Please do stop by and say
hello.
