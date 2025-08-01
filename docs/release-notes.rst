=============
Release Notes
=============

.. towncrier release notes start

2.0.2 (2025-07-30)
==================

Bug Fixes
---------

* Fix: Internal server error when adding packages
  (`#1911 <https://github.com/fedora-infra/anitya/issues/1911>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release.


2.0.1 (2025-07-03)
==================

Bug Fixes
---------

* You are going to be blocked from scraping MetaCPAN.org
  (`#1900 <https://github.com/fedora-infra/anitya/issues/1900>`_)

* Fix api_v2 returning 500
  (`#1906 <https://github.com/fedora-infra/anitya/issues/1906>`_)


Development Changes
-------------------

* Update dev environment to latest fedora release
  (`#1909 <https://github.com/fedora-infra/anitya/issues/1909>`_)


Other Changes
-------------

* Update documentation for APIv2
  (`PR#1891 <https://github.com/fedora-infra/anitya/pull/1891>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anton Medvedev
* Peter Oliver
* Michal Konecny
* Alex Mayer

2.0.0 (2025-01-10)
==================

Features
--------

* Migrate from social_auth to authlib
  (`#1139 <https://github.com/fedora-infra/anitya/issues/1139>`_)

  WARNING: This removes social_auth tables from Anitya, which can't be recovered back.
  Thus making this version backwards incompatible.

Development Changes
-------------------

* Improve development container
  (`#1859 <https://github.com/fedora-infra/anitya/issues/1859>`_)

* Remove Vagrant dev environemnt
  (`#1860 <https://github.com/fedora-infra/anitya/issues/1860>`_)

Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Lenka Segura
* Michal Konecny


1.10.0 (2024-05-29)
===================

Features
--------

* Add option to delete user to users management page
  (`#931 <https://github.com/fedora-infra/anitya/issues/931>`_)

* Sort search by a "clickable" 'name' 'homepage' 'backend' 'latest version'
  (`#1627 <https://github.com/fedora-infra/anitya/issues/1627>`_)


Bug Fixes
---------

* Error when uuid object is returned from Fedora Account System
  (`#1727 <https://github.com/fedora-infra/anitya/issues/1727>`_)


Development Changes
-------------------

* Remove `straight.plugin` dependency
  (`#1769 <https://github.com/fedora-infra/anitya/issues/1769>`_)


Other Changes
-------------

* Added instructions for configuring `social_sqlalchemy` in Anitya to the contributing guidelines.
  (`#1723 <https://github.com/fedora-infra/anitya/issues/1723>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Vidit Maheshwari
* Arthur Zamarin
* NyuydineBill
* freedisch
* Michal Konecny

1.9.0 (2024-01-30)
==================

Features
--------

* Support odd-numbered pre-release version filtering
  (`PR#1708 <https://github.com/fedora-infra/anitya/pull/1708>`_)

* Created Gitea backend.
  (`#1566 <https://github.com/fedora-infra/anitya/issues/1566>`_)


Bug Fixes
---------

* libraries.io consumer crashing
  (`#1666 <https://github.com/fedora-infra/anitya/issues/1666>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Erol Keskin
* James Knight
* Liora Milbaum
* Michal Konecny


1.8.1 (2023-05-26)
==================

Features
--------

* Sort the list of distributions in the project view
  (`PR#1599 <https://github.com/fedora-infra/anitya/pull/1599>`_)


Bug Fixes
---------

* Error when checking for versions in cgit backend
  (`#1536 <https://github.com/fedora-infra/anitya/issues/1536>`_)

* Fix bug in PEP440 sorting
  (`#1586 <https://github.com/fedora-infra/anitya/issues/1586>`_)

* Fix 500 when accesing project with PYTHON versioning scheme when the version is not a correct version
  (`#1590 <https://github.com/fedora-infra/anitya/issues/1590>`_)


Development Changes
-------------------

* Add python 3.11 support
  (`#1592 <https://github.com/fedora-infra/anitya/issues/1592>`_)


Other Changes
-------------

* Add tox and towncrier to dev dependencies
  (`PR#1596 <https://github.com/fedora-infra/anitya/pull/1596>`_)

* Document what kind of "package name" to use in a distribution mapping
  (`#1554 <https://github.com/fedora-infra/anitya/issues/1554>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Dan Fandrich
* Liora Milbaum
* AsciiWolf
* Michal Konečný


1.8.0 (2023-04-27)
==================

API Changes
-----------

* add stable_version as output in PackagesResource
  (`#1033 <https://github.com/fedora-infra/anitya/issues/1033>`_)


Bug Fixes
---------

* project page: Remove fixed column widths
  (`PR#1557 <https://github.com/fedora-infra/anitya/pull/1557>`_)

* Fix the arbitrary URL jumping vulnerability of /login
  (`PR#1562 <https://github.com/fedora-infra/anitya/pull/1562>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Arthur Zamarin
* FeRD (Frank Dana)
* lu4nx
* Michal Konečný


1.7.0 (2023-01-26)
==================

Features
--------

* Delete all versions throws 504 Gateway Timeout
  (`#1468 <https://github.com/fedora-infra/anitya/issues/1468>`_)

* Migrate to Bootstrap 5
  (`#1504 <https://github.com/fedora-infra/anitya/issues/1504>`_)


Bug Fixes
---------

* Fix Python versioning parse doesn't return string
  (`#1402 <https://github.com/fedora-infra/anitya/issues/1402>`_)


Development Changes
-------------------

* Use npm for javascript package management
  (`#1504 <https://github.com/fedora-infra/anitya/issues/1504>`_)

* Improve Vagrant Development Environment
  (`#1520 <https://github.com/fedora-infra/anitya/issues/1520>`_)


Other Changes
-------------

* Use `anitya.project.version.remove.v2` instead of `anitya.project.version.remove`
  (`PR#1495 <https://github.com/fedora-infra/anitya/pull/1495>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Nikita Bugrovsky
* Michal Konečný


1.6.0 (2022-10-05)
==================

API Changes
-----------

* Add missing optional parameters to the `POST /api/v2/projects/` API endpoint.
  (`#1463 <https://github.com/fedora-infra/anitya/issues/1463>`_)

* Fix handling of JSON requests in API v2
  (`#1464 <https://github.com/fedora-infra/anitya/issues/1464>`_)


Features
--------

* Created SourceHut backend.
  (`#999 <https://github.com/fedora-infra/anitya/issues/999>`_)

* Add configuration for distro links
  (`#1066 <https://github.com/fedora-infra/anitya/issues/1066>`_)


Development Changes
-------------------

* Migrate Anitya project to poetry
  (`PR#1475 <https://github.com/fedora-infra/anitya/pull/1475>`_)

* Removed duplicated implementation of get_version on backends
  (`#1453 <https://github.com/fedora-infra/anitya/issues/1453>`_)


Other Changes
-------------

* Migrate from dependabot to renovate
  (`PR#1459 <https://github.com/fedora-infra/anitya/pull/1459>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Fabio Valentini
* Erol Keskin
* Michal Konečný


1.5.1 (2022-09-02)
==================

Bug Fixes
---------

* Fix wrong url replacement in GitHub backend.
  (`PR#1449 <https://github.com/fedora-infra/anitya/pull/1449>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Erol Keskin


1.5.0 (2022-08-30)
==================

API Changes
-----------

* /api/v2/packages/ endpoint now returns latest version info too.
  (`#1442 <https://github.com/fedora-infra/anitya/issues/1442>`_)


Features
--------

* Add Ubuntu links to project page.
  (`PR#1403 <https://github.com/fedora-infra/anitya/pull/1403>`_)

* Add cgit backend
  (`#1037 <https://github.com/fedora-infra/anitya/issues/1037>`_)

* Add Gogs backend
  (`#1222 <https://github.com/fedora-infra/anitya/issues/1222>`_)


Bug Fixes
---------

* Fixed version check url for GitHub projects those marked with "Check releases instead of tags"
  (`#1013 <https://github.com/fedora-infra/anitya/issues/1013>`_)

* Folder backend returns wrong version
  (`#1286 <https://github.com/fedora-infra/anitya/issues/1286>`_)

* Saved "Version scheme" value is not loaded
  (`#1389 <https://github.com/fedora-infra/anitya/issues/1389>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Erol Keskin
* Michal Konečný
* Steve Beattie


1.4.1 (2022-07-04)
==================

Bug Fixes
---------

* Empty versions obtained for some projects
  (`PR#1401 <https://github.com/fedora-infra/anitya/pull/1401>`_)

* Internal server errors occurring at release-monitoring
  (`#1390 <https://github.com/fedora-infra/anitya/issues/1390>`_)


1.4.0 (2022-06-21)
==================

API Changes
-----------

* Replace API v2 backend
  (`PR#1105 <https://github.com/fedora-infra/anitya/pull/1105>`_)


Features
--------

* Add link to AlmaLinux package to distribution mapping
  (`PR#1386 <https://github.com/fedora-infra/anitya/pull/1386>`_)

* Add sourceforge (git) backend to retrieve git tags
  (`#223 <https://github.com/fedora-infra/anitya/issues/223>`_)

* Add Python (PEP 440) versioning scheme
  (`#1015 <https://github.com/fedora-infra/anitya/issues/1015>`_)


Bug Fixes
---------

* KeyError: 'releases' on pypi backend
  (`#1387 <https://github.com/fedora-infra/anitya/issues/1387>`_)

* Fix documentation and javascript issues
  (`PR#1144 <https://github.com/fedora-infra/anitya/pull/1144>`_)

* Better error message when GitHub token is missing
  (`PR#1182 <https://github.com/fedora-infra/anitya/pull/1182>`_)

* Only include unyanked crate versions
  (`PR#1272 <https://github.com/fedora-infra/anitya/pull/1272>`_)

* Only include unyanked PyPI versions
  (`PR#1334 <https://github.com/fedora-infra/anitya/pull/1334>`_)

* Version Filter not applied on Test Check
  (`#1143 <https://github.com/fedora-infra/anitya/issues/1143>`_)

* Downgrade Sphinx to compatible version 4.0.3
  (`#1148 <https://github.com/fedora-infra/anitya/issues/1148>`_)

* Intermediate versions are skipped while update checking
  (`#1273 <https://github.com/fedora-infra/anitya/issues/1273>`_)

* Thread timeout in check_service
  (`#1284 <https://github.com/fedora-infra/anitya/issues/1284>`_)


Development Changes
-------------------

* Introduced static-type checking through inclusion of mypy in tox.
  Removed 3.6 and 3.7 from the list of supported python versions.
  (`PR#1114 <https://github.com/fedora-infra/anitya/pull/1114>`_)

* Migrate to cloud-fedora-35 container on CI
  (`PR#1296 <https://github.com/fedora-infra/anitya/pull/1296>`_)

* Update development environments to Fedora 36
  (`PR#1380 <https://github.com/fedora-infra/anitya/pull/1380>`_)

* Separate Anitya fedora messaging schema to https://github.com/fedora-infra/anitya-messages
  (`#RP1347 <https://github.com/fedora-infra/anitya/issues/RP1347>`_)

* Create podman/docker infrastructure for containerized workflow
  (`#936 <https://github.com/fedora-infra/anitya/issues/936>`_)

* Support for Python 3.9
  (`#1151 <https://github.com/fedora-infra/anitya/issues/1151>`_)

* Update CI pods to newer Fedora
  (`#1288 <https://github.com/fedora-infra/anitya/issues/1288>`_)

* Add support for Python 3.10
  (`#1300 <https://github.com/fedora-infra/anitya/issues/1300>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anatoli Babenia
* Adam Saleh
* Carl George
* Jerry James
* Lenka Segura
* Michael Scherer
* Michal Konečný
* Nikita Bugrovsky
* Onur
* mehmet
* Otto Urpelainen
* Petr Viktorin


1.3.0 (2021-03-19)
==================

Features
--------

* Add PLD Linux package link to project page.
  (`PR#1065 <https://github.com/fedora-infra/anitya/pull/1065>`_)

* Make the default regex pull in rc/alpha
  (`#1063 <https://github.com/fedora-infra/anitya/issues/1063>`_)


Bug Fixes
---------

* Remove Google code backend
  (`#1068 <https://github.com/fedora-infra/anitya/issues/1068>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Elan Ruusamäe


1.2.0 (2021-03-15)
==================

Features
--------

* Link Fedora packages to their source
  (`#557 <https://github.com/fedora-infra/anitya/issues/557>`_)


Bug Fixes
---------

* Unstable releases don't show up in folder backend
  (`#1056 <https://github.com/fedora-infra/anitya/issues/1056>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anatoli Babenia


1.1.3 (2021-03-08)
==================

Bug Fixes
---------

* Fix version_filter on GitHub backend
  (`#1042 <https://github.com/fedora-infra/anitya/issues/1042>`_)


1.1.2 (2021-03-05)
==================

Bug Fixes
---------

* Fix the stackage backend regex
  (`#1010 <https://github.com/fedora-infra/anitya/issues/1010>`_)

* Crash when release doesn't have tag associated in GitHub backend
  (`#1029 <https://github.com/fedora-infra/anitya/issues/1029>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* supzi-del


1.1.1 (2021-02-21)
==================

Bug Fixes
---------

* Stable versions in the APIs are sent with prefix
  (`#1026 <https://github.com/fedora-infra/anitya/issues/1026>`_)


1.1.0 (2021-02-19)
==================

API Changes
-----------

* Add stable_versions field to APIv1 and APIv2
  (`#1014 <https://github.com/fedora-infra/anitya/issues/1014>`_)


Features
--------

* Don't add project to check queue if they belong to blacklisted backend
  (`#888 <https://github.com/fedora-infra/anitya/issues/888>`_)


1.0.1 (2021-02-12)
==================

Bug Fixes
---------

* GitHub backend not retrieving new versions because of unknown cursor
  (`#1016 <https://github.com/fedora-infra/anitya/issues/1016>`_)


1.0.0 (2021-01-20)
==================

API Changes
-----------

* Add versions resource to API v2
  (`#491 <https://github.com/fedora-infra/anitya/issues/491>`_)

* API v1 api/version/get is now returning only versions field instead of whole project when no version is retrieved
  (`#898 <https://github.com/fedora-infra/anitya/issues/898>`_)


Features
--------

* Add missing methods to fedora messaging schema (version 1.1.0)
  (`PR#906 <https://github.com/fedora-infra/anitya/pull/906>`_)

* Add preview mode
  (`#491 <https://github.com/fedora-infra/anitya/issues/491>`_)

* Allow removing all versions at once (admin only)
  (`#623 <https://github.com/fedora-infra/anitya/issues/623>`_)

* Implement fedmsg meta methods in fedora messaging schema
  (`#752 <https://github.com/fedora-infra/anitya/issues/752>`_)

* Flag pre-release versions
  (`#753 <https://github.com/fedora-infra/anitya/issues/753>`_)

* Anitya should report every found version, not only latest
  (`#774 <https://github.com/fedora-infra/anitya/issues/774>`_)

* Add option to archive and unarchive project (admin only)
  (`#865 <https://github.com/fedora-infra/anitya/issues/865>`_)

* Add version filter to project
  (`#898 <https://github.com/fedora-infra/anitya/issues/898>`_)


Bug Fixes
---------

* Yahoo OpenId no longer exists in social_auth library
  (`PR#1005 <https://github.com/fedora-infra/anitya/pull/1005>`_)

* GitHub backend: Failure with error "No upstream version found" when the project has no new version
  (`#892 <https://github.com/fedora-infra/anitya/issues/892>`_)

* sar.py fails with AttributeError: 'User' object has no attribute 'social_auth'
  (`#954 <https://github.com/fedora-infra/anitya/issues/954>`_)


Development Changes
-------------------

* Enhance check_service log output
  (`PR#886 <https://github.com/fedora-infra/anitya/pull/886>`_)

* Move Anitya from release-monitoring organization to fedora-infra
  (`PR#887 <https://github.com/fedora-infra/anitya/pull/887>`_)

* Fix documentation build
  (`PR#902 <https://github.com/fedora-infra/anitya/pull/902>`_)

* Freeze version of dependencies
  (`PR#903 <https://github.com/fedora-infra/anitya/pull/903>`_)

* Fix service name in vagrant provisioning script
  (`PR#940 <https://github.com/fedora-infra/anitya/pull/940>`_)

* Add Flask to ReadTheDocs build requirements
  (`PR#946 <https://github.com/fedora-infra/anitya/pull/946>`_)

* Add pyasn1 to RTD build requirements
  (`PR#947 <https://github.com/fedora-infra/anitya/pull/947>`_)

* Add support for Python 3.8
  (`PR#979 <https://github.com/fedora-infra/anitya/pull/979>`_)

* Make vagrant environment more like production
  (`#924 <https://github.com/fedora-infra/anitya/issues/924>`_)


Other Changes
-------------

* Add guidelines for admins on release-monitoring.org
  (`PR#964 <https://github.com/fedora-infra/anitya/pull/964>`_)

* Add social auth info to SAR script
  (`PR#970 <https://github.com/fedora-infra/anitya/pull/970>`_)

* Completely remove fedmsg.
  (`#737 <https://github.com/fedora-infra/anitya/issues/737>`_)

* Add stable_versions field to project.version.update message
  (`#753 <https://github.com/fedora-infra/anitya/issues/753>`_)

* Fedora messaging schema 2.0.0 - new topic anitya.project.version.update.v2
  (`#774 <https://github.com/fedora-infra/anitya/issues/774>`_)

* Rewrite projects pages
  (`#885 <https://github.com/fedora-infra/anitya/issues/885>`_)

* Update documentation to reflect current state
  (`#972 <https://github.com/fedora-infra/anitya/issues/972>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anatoli Babenia
* luto
* Michal Konečný
* Olivier Lemasle
* Philippe Ombredanne


0.18 (2020-01-13)
=================

API Changes
-----------

* Filters in APIv2 are now case insensitive
  (`#807 <https://github.com/fedora-infra/anitya/issues/807>`_)


Features
--------

* Automatically delete projects without versions that reached configured error threshold
  (`PR#865 <https://github.com/fedora-infra/anitya/pull/865>`_)

* GitHub: Store and use latest known version cursors
  (`PR#873 <https://github.com/fedora-infra/anitya/pull/873>`_)

* Link to commit of latest version if known
  (`PR#874 <https://github.com/fedora-infra/anitya/pull/874>`_)

* Use dropdown field for distro when on Add project form
  (`#777 <https://github.com/fedora-infra/anitya/issues/777>`_)

* Add error counter to project
  (`#829 <https://github.com/fedora-infra/anitya/issues/829>`_)

* Add timeout option for check service
  (`#843 <https://github.com/fedora-infra/anitya/issues/843>`_)

* Strip whitespaces from version when removing prefix
  (`#866 <https://github.com/fedora-infra/anitya/issues/866>`_)


Bug Fixes
---------

* Fix crash on GNU, Crates and Folder backends
  (`PR#837 <https://github.com/fedora-infra/anitya/pull/837>`_)

* Fix OOM issue with check_service
  (`PR#842 <https://github.com/fedora-infra/anitya/pull/842>`_)

* Removed duplicate search form from project search result page
  (`PR#877 <https://github.com/fedora-infra/anitya/pull/877>`_)

* Fix accessing projects in GitLab subgroups
  (`PR#884 <https://github.com/fedora-infra/anitya/pull/884>`_)

* Database schema image is missing in documentation
  (`#692 <https://github.com/fedora-infra/anitya/issues/692>`_)

* Current page is forgotten on login
  (`#713 <https://github.com/fedora-infra/anitya/issues/713>`_)

* If URL is changed, update ecosystem value as well
  (`#764 <https://github.com/fedora-infra/anitya/issues/764>`_)

* Tooltips are not working on Firefox 68
  (`#813 <https://github.com/fedora-infra/anitya/issues/813>`_)

* Use tag name instead of release name for projects, which are checking only releases
  (`#845 <https://github.com/fedora-infra/anitya/issues/845>`_)

* Can't disable "Check releases instead of tags" checkbox when editing project
  (`#855 <https://github.com/fedora-infra/anitya/issues/855>`_)

* Allow no delimiter in calendar versioning pattern
  (`#867 <https://github.com/fedora-infra/anitya/issues/867>`_)

* Distro search is broken
  (`#876 <https://github.com/fedora-infra/anitya/issues/876>`_)


Development Changes
-------------------

* Use DEBUG level log for development
  (`PR#826 <https://github.com/fedora-infra/anitya/pull/826>`_)

* Add Dependabot configuration file
  (`PR#844 <https://github.com/fedora-infra/anitya/pull/844>`_)

* Bump Vagrant box to Fedora 31
  (`PR#858 <https://github.com/fedora-infra/anitya/pull/858>`_)

* Mock the Fedora Messaging calls in the unit tests
  (`PR#860 <https://github.com/fedora-infra/anitya/pull/860>`_)

* Make `black` show diff of needed changes
  (`PR#878 <https://github.com/fedora-infra/anitya/pull/878>`_)

* Make log output from check_project_release more readable
  (`#828 <https://github.com/fedora-infra/anitya/issues/828>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anatoli Babenia
* Aurélien Bompard
* Nicholas La Roux
* Michal Konečný
* Nils Philippsen


0.17.2 (2019-09-26)
===================

Bug Fixes
---------

* Fix crash on GNU, Crates and Folder backends
  (`PR#837 <https://github.com/fedora-infra/anitya/pull/837>`_)

* Fix OOM issue with check_service
  (`PR#842 <https://github.com/fedora-infra/anitya/pull/842>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Michal Konečný


0.17.1 (2019-09-09)
===================

Bug Fixes
---------

* Final info message in check service using error counter instead ratelimit counter
  (`PR#823 <https://github.com/fedora-infra/anitya/pull/823>`_)

* No error was shown when check_service thread crashed
  (`PR#824 <https://github.com/fedora-infra/anitya/pull/824>`_)

* Crash when sorting versions with and without date when looking for last retrieved version
  (`PR#825 <https://github.com/fedora-infra/anitya/pull/825>`_)

* Crash when calling FTP url
  (`PR#833 <https://github.com/fedora-infra/anitya/pull/833>`_)

* Latest version is not updated when version is removed from web interface
  (`#830 <https://github.com/fedora-infra/anitya/issues/830>`_)

* GitHub response 403 doesn't have ratelimit reset time
  (`#832 <https://github.com/fedora-infra/anitya/issues/832>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Michal Konečný


0.17.0 (2019-09-03)
===================

Features
--------

* Adhere to black's Python 3.6 formatting rules
  (`PR#818 <https://github.com/fedora-infra/anitya/pull/818>`_)

* Support multiple version prefixes
  (`#655 <https://github.com/fedora-infra/anitya/issues/655>`_)

* Make libraries.io SSE consumer part of Anitya
  (`#723 <https://github.com/fedora-infra/anitya/issues/723>`_)

* Check for new versions only when there is any change on the URL till last version was retrieved
  (`#730 <https://github.com/fedora-infra/anitya/issues/730>`_)

* Allow fetching releases on Github backend
  (`#733 <https://github.com/fedora-infra/anitya/issues/733>`_)

* Add calendar versioning
  (`#740 <https://github.com/fedora-infra/anitya/issues/740>`_)

* Add semantic versioning
  (`#741 <https://github.com/fedora-infra/anitya/issues/741>`_)


Bug Fixes
---------

* Restore missing closing """ in sample configuration
  (`PR#797 <https://github.com/fedora-infra/anitya/pull/797>`_)

* Constrain failure during alembic downgrade
  (`PR#812 <https://github.com/fedora-infra/anitya/pull/812>`_)

* Fix createdb.py to now create all tables properly
  (`PR#817 <https://github.com/fedora-infra/anitya/pull/817>`_)

* Hide ecosystem field for non admin users
  (`#687 <https://github.com/fedora-infra/anitya/issues/687>`_)

* Failures during project addition causes distro mapping to be skipped
  (`#735 <https://github.com/fedora-infra/anitya/issues/735>`_)

* Handle status code 403 as rate limit exception on Github backend
  (`#790 <https://github.com/fedora-infra/anitya/issues/790>`_)

* Cannot add distro
  (`#791 <https://github.com/fedora-infra/anitya/issues/791>`_)

* One revision is skipped when doing `alembic upgrade head`
  (`#819 <https://github.com/fedora-infra/anitya/issues/819>`_)


Development Changes
-------------------

* Add docker build to Travis CI tests
  (`PR#799 <https://github.com/fedora-infra/anitya/pull/799>`_)

* Change required version for pyasn1
  (`PR#812 <https://github.com/fedora-infra/anitya/pull/812>`_)

* Minor packaging cleanup and gitignore additions
  (`PR#816 <https://github.com/fedora-infra/anitya/pull/816>`_)

* Fix rabbitmq-server in dev environment
  (`#804 <https://github.com/fedora-infra/anitya/issues/804>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anatoli Babenia
* Michal Konečný
* Samuel Verschelde
* Vincent Fazio


0.16.1 (2019-07-16)
===================

Bug Fixes
---------

* Check service: Counters saved to database are always 0
  (`#795 <https://github.com/fedora-infra/anitya/issues/795>`_)


Development Changes
-------------------

* Fix issue with documentation build
  (`#789 <https://github.com/fedora-infra/anitya/issues/789>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Michal Konečný


0.16.0 (2019-06-24)
===================

Features
--------

* Turn Anitya cron job to service
  (`#668 <https://github.com/fedora-infra/anitya/issues/668>`_)


Bug Fixes
---------

* Error 500 when opening distro page
  (`#709 <https://github.com/fedora-infra/anitya/issues/709>`_)

* "Edit" form for Distro Mapping forgets the distributions
  (`#744 <https://github.com/fedora-infra/anitya/issues/744>`_)

* anitya.project.map.new not send when adding new mapping through APIv2
  (`#760 <https://github.com/fedora-infra/anitya/issues/760>`_)


Development Changes
-------------------

* Add new dependency ordered_set
  (`#668 <https://github.com/fedora-infra/anitya/issues/668>`_)

* Add diff-cover to tox testing suite
  (`#782 <https://github.com/fedora-infra/anitya/issues/782>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Michal Konečný


0.15.1 (2019-03-06)
===================

Bug Fixes
---------

* Fix topic for fedora_messaging
  (`PR#750 <https://github.com/fedora-infra/anitya/pull/750>`_)


Development Changes
-------------------

* Check formatting using black
  (`PR#725 <https://github.com/fedora-infra/anitya/pull/725>`_)

* Remove gunicorn dependency
  (`PR#742 <https://github.com/fedora-infra/anitya/pull/742>`_)


Other Changes
-------------

* Add sample configuration for Fedora Messaging
  (`#738 <https://github.com/fedora-infra/anitya/issues/738>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Michal Konečný


0.15.0 (2019-02-20)
===================

Features
--------

* Convert to Fedora Messaging
  (`PR#570 <https://github.com/fedora-infra/anitya/pull/570>`_)


Bug Fixes
---------

* Release notes point to fedora-messaging
  (`#699 <https://github.com/fedora-infra/anitya/issues/699>`_)

* Javascript error on add project page
  (`#714 <https://github.com/fedora-infra/anitya/issues/714>`_)

* Changed copyright datum on frontpage to 2013-2019
  (`#721 <https://github.com/fedora-infra/anitya/issues/721>`_)

* Invalid User-Agent
  (`#729 <https://github.com/fedora-infra/anitya/issues/729>`_)

Development Changes
-------------------

* Rename Vagrantfile.example to Vagrantfile
  (`PR#715 <https://github.com/fedora-infra/anitya/pull/715>`_)

* Introduce bandit to tox tests
  (`PR#724 <https://github.com/fedora-infra/anitya/pull/724>`_)


Other Changes
-------------

* Added example of usage in contribution guide.
  (`PR#719 <https://github.com/fedora-infra/anitya/pull/719>`_)

* Fix URL to fedmsg website on index.html to use the correct website URL
  (`PR#722 <https://github.com/fedora-infra/anitya/pull/722>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Jeremy Cline
* AsciiWolf
* Zlopez
* Michal Konečný
* Neal Gompa
* Yaron Shahrabani


0.14.1 (2019-01-17)
===================

Features
--------

* Show raw version on project page for admins
  (`PR#696 <https://github.com/fedora-infra/anitya/pull/696>`_)


Bug Fixes
---------

* Libraries.io consumer is replacing topic_prefix for Anitya
  (`PR#704 <https://github.com/fedora-infra/anitya/pull/704>`_)

* Release unlocked lock in cronjob
  (`PR#708 <https://github.com/fedora-infra/anitya/pull/708>`_)

* Comparing by dates created version duplicates
  (`#702 <https://github.com/fedora-infra/anitya/issues/702>`_)


Development Changes
-------------------

* Remove Date version scheme
  (`PR#707 <https://github.com/fedora-infra/anitya/pull/707>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anatoli Babenia
* Michal Konečný


0.14.0 (2019-01-08)
===================

Features
--------

* Add delete cascade on DB models
  (`PR#608 <https://github.com/fedora-infra/anitya/pull/608>`_)

* Logs table is replaced by simple status on project
  (`PR#635 <https://github.com/fedora-infra/anitya/pull/635>`_)

* Update form for adding new distributions
  (`PR#639 <https://github.com/fedora-infra/anitya/pull/639>`_)

* Refresh page after full check
  (`PR#670 <https://github.com/fedora-infra/anitya/pull/670>`_)

* Show URL for version check on project UI
  (`#549 <https://github.com/fedora-infra/anitya/issues/549>`_)

* Link to backend info from project view and edit pages
  (`#556 <https://github.com/fedora-infra/anitya/issues/556>`_)

* Retrieve all versions, not only the newest one
  (`#595 <https://github.com/fedora-infra/anitya/issues/595>`_)

* Add rate limit handling
  (`#600 <https://github.com/fedora-infra/anitya/issues/600>`_)

* Basic user management UI for admins
  (`#621 <https://github.com/fedora-infra/anitya/issues/621>`_)

* Rate limit enhancements
  (`#665 <https://github.com/fedora-infra/anitya/issues/665>`_)

* Add ecosystem information to project.version.update fedmsg topic.
  (`#666 <https://github.com/fedora-infra/anitya/issues/666>`_)


Bug Fixes
---------

* Fix unhandled exception in GitLab backend
  (`PR#663 <https://github.com/fedora-infra/anitya/pull/663>`_)

* Can't rename mapping for gstreamer
  (`#598 <https://github.com/fedora-infra/anitya/issues/598>`_)

* Source map error: request failed with status 404 for various javascript packages
  (`#606 <https://github.com/fedora-infra/anitya/issues/606>`_)

* about#test-your-regex link is broken
  (`#628 <https://github.com/fedora-infra/anitya/issues/628>`_)

* Github backend returns reversed list
  (`#642 <https://github.com/fedora-infra/anitya/issues/642>`_)

* Version prefix not working in GitLab backend
  (`#644 <https://github.com/fedora-infra/anitya/issues/644>`_)

* Latest version on Project UI is shown with prefix
  (`#662 <https://github.com/fedora-infra/anitya/issues/662>`_)

* Crash when version is too long
  (`#674 <https://github.com/fedora-infra/anitya/issues/674>`_)


Development Changes
-------------------

* Add python 3.7 to tox tests
  (`PR#650 <https://github.com/fedora-infra/anitya/pull/650>`_)

* Update Vagrantfile to use Fedora 29 image
  (`PR#653 <https://github.com/fedora-infra/anitya/pull/653>`_)

* Drop support for python 2.7 and python 3.5
  (`PR#672 <https://github.com/fedora-infra/anitya/pull/672>`_)


Other Changes
-------------

* Update contribution guide
  (`PR#636 <https://github.com/fedora-infra/anitya/pull/636>`_)

* Add GDPR SAR script
  (`PR#649 <https://github.com/fedora-infra/anitya/pull/649>`_)

* Add supported versions of python to setup script
  (`PR#651 <https://github.com/fedora-infra/anitya/pull/651>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Anatoli Babenia
* Graham Williamson
* Jeremy Cline
* Michal Konečný


0.13.2 (2018-10-12)
===================

Features
--------

* Show users their ID on Settings page
  (`PR#631 <https://github.com/fedora-infra/anitya/pull/631>`_)

* Add sorting by creation date for versions
  (`#593 <https://github.com/fedora-infra/anitya/issues/593>`_)


Bug Fixes
---------

* Can't parse owner/repo on Github backend
  (`PR#632 <https://github.com/fedora-infra/anitya/pull/632>`_)

* Login into staging using OpenID not possible
  (`#616 <https://github.com/fedora-infra/anitya/issues/616>`_)


Development Changes
-------------------

* Add towncrier for generating release notes
  (`PR#618 <https://github.com/fedora-infra/anitya/pull/618>`_)

* Remove deprecations warning
  (`PR#627 <https://github.com/fedora-infra/anitya/pull/627>`_)

* Add documentation dependency to vagrant container
  (`PR#630 <https://github.com/fedora-infra/anitya/pull/630>`_)


Contributors
------------
Many thanks to the contributors of bug reports, pull requests, and pull request
reviews for this release:

* Eli Young
* Jeremy Cline
* Michal Konečný


v0.13.1
=======

Features
--------

* Add database schema generation (`#603
  <https://github.com/fedora-infra/anitya/pull/603>`_).

Bug Fixes
---------

* Fix cron issues (`#613
  <https://github.com/fedora-infra/anitya/pull/613>`_).

v0.13.0
=======

Dependencies
------------

* Explicitly depend on ``defusedxml``

Features
--------

* Update GitHub backend to `GitHub API v4
  <https://developer.github.com/v4/>`_ (`#582
  <https://github.com/fedora-infra/anitya/pull/582>`_).

* Add GitLab backend. This is implemented using `GitLab API v4
  <https://docs.gitlab.com/ee/api/README.html>`_ (`#591
  <https://github.com/fedora-infra/anitya/pull/591>`_).

* Update CPAN backend to use metacpan.org (`#569
  <https://github.com/fedora-infra/anitya/pull/569>`_).

* Parse XML from CPAN with defusedxml (`#569
  <https://github.com/fedora-infra/anitya/pull/569>`_).

Bug Fixes
---------

* Change edit message for project, when no edit actually happened (`#579
  <https://github.com/fedora-infra/anitya/pull/579>`_).

* Fix wrong title on Edit page (`#578
  <https://github.com/fedora-infra/anitya/pull/578>`_).

* Default custom regex is now configurable (`#571
  <https://github.com/fedora-infra/anitya/pull/571>`_).

v0.12.1
=======

Dependencies
------------

* Unpin ``straight.plugin`` dependency. It was pinned to avoid a bug which has
  since been fixed in the latest releases (`#564
  <https://github.com/fedora-infra/anitya/pull/564>`_).

Bug Fixes
---------

* Rather than returning an HTTP 500 when authenticating with two separate
  identity providers using the same email, return a HTTP 400 to indicate the
  client should not retry the request and inform them they must log in with
  the original identity provider (`#563
  <https://github.com/fedora-infra/anitya/pull/563>`_).


v0.12.0
=======

Dependencies
------------

* Drop the dependency on the Python ``bunch`` package as it is not used.

* There is no longer a hard dependency on the ``rpm`` Python package.

* Introduce a dependency on the Python ``social-auth-app-flask-sqlalchemy`` and
  ``flask-login`` packages in order to support authenticating against OAuth2,
  OpenID Connect, and plain OpenID providers.

* Introduce a dependency on the Python ``blinker`` package to support signaling
  in Flask.

* Introduce a dependency on the Python ``pytoml`` package in order to support
  a TOML configuration format.


Backwards-incompatible Changes
------------------------------

* Dropped support for Python 2.6

* Added support for Python 3.4+

APIs
^^^^

A number of functions that make up Anitya's Python API have been moved
(`#503 <https://github.com/fedora-infra/anitya/pull/503>`_). The full
list of functions are below. Note that no function signatures have changed.

* ``anitya.check_release`` is now ``anitya.lib.utilities.check_project_release``.

* ``anitya.fedmsg_publish`` is now ``anitya.lib.utilities.fedmsg_publish``.

* ``anitya.log`` is now ``anitya.lib.utilities.log``.

* ``anitya.lib.init`` is now ``anitya.lib.utilities.init``.

* ``anitya.lib.create_project`` is now ``anitya.lib.utilities.create_project``.

* ``anitya.lib.edit_project`` is now ``anitya.lib.utilities.edit_project``.

* ``anitya.lib.map_project`` is now ``anitya.lib.utilities.map_project``.

* ``anitya.lib.flag_project`` is now ``anitya.lib.utilities.flag_project``.

* ``anitya.lib.set_flag_state`` is now ``anitya.lib.utilities.set_flag_state``.

* ``anitya.lib.get_last_cron`` is now ``anitya.lib.utilities.get_last_cron``.


Deprecations
------------

* Deprecated the v1 HTTP API.


Features
--------

* Introduced a new set of APIs under ``api/v2/`` that support write operations
  for users authenticated with an API token.

* Configuration is now TOML format.

* Added a user guide to the documentation.

* Added an admin guide to the documentation.

* Automatically generate API documentation with Sphinx.

* Introduce httpdomain support to document the HTTP APIs.

* Add initial support for projects to set a "version scheme" in order to help
  with version ordering. At the present the only version scheme implemented is
  the RPM scheme.

* Add support for authenticating using a large number of OAuth2, OpenID Connect,
  and OpenID providers.

* Add a fedmsg consumer that integrates with libraries.io to provide more timely
  project update notifications.

* Add support for running on OpenShift with s2i.

* Switch over to pypi.org rather than pypi.python.org

* Use HTTPS in backend examples, default URLs, and documentation.


Bug Fixes
---------

* Fixed deprecation warnings from using ``flask.ext`` (#431).

* Fix the NPM backend's update feed.


Developer Improvements
----------------------

* Fixed all warnings generated from building the Sphinx documentation and
  introduce tests to ensure there are no regressions (#427).

* Greatly improved the unit tests by breaking monolithic tests up.

* Moved the unit tests into the ``anitya.tests`` package so tests didn't need
  to mess with the Python path.

* Fixed logging during test runs

* Switched to pytest as the test runner since nose is dead.

* Introduced nested transactions for database tests rather than removing the
  database after each test. This greatly reduced run time.

* Added support for testing against multiple Python versions via tox.

* Added Travis CI integration.

* Added code coverage with pytest-cov and Codecov integration.

* Fixed all flake8 errors.

* Refactored the database code to avoid circular dependencies.

* Allow the Vagrant environment to be provisioned with an empty database.


Contributors
------------

Many thanks to all the contributors for this release, including those who filed
issues. Commits for this release were contributed by:

* Elliott Sales de Andrade
* Jeremy Cline
* luto
* Michael Simacek
* Nick Coghlan
* Nicolas Quiniou-Briand
* Ricardo Martincoski
* robled

Thank you all for your hard work.


v0.11.0
=======

Released February 08, 2017.

* Return 4XX codes in error cases for /projects/new rather than 200 (Issue #246)

* Allow projects using the "folder" backend to make insecure HTTPS requests
  (Issue #386)

* Fix an issue where turning the insecure flag on and then off for a project
  resulted in insecure requests until the server was restarted (Issue #394)

* Add a data migration to set the ecosystem of existing projects if the backend
  they use is the default backend for an ecosystem. Note that this migration
  can fail if existing data has duplicate projects since there is a new
  constraint that a project name is unique within an ecosystem (Issue #402).

* Fix the regular expression used with the Debian backend to strip the "orig"
  being incorrectly included in the version (Issue #398)

* Added a new backend and ecosystem for https://crates.io (Issue #414)

* [insert summary of change here]


v0.10.1
=======

Released November 29, 2016.

* Fix an issue where the version prefix was not being stripped (Issue #372)

* Fix an issue where logs were not viewable to some users (Issue #367)

* Update anitya's mail_logging to be compatible with old and new psutil
  (Issue #368)

* Improve Anitya's error reporting via email (Issue #368)

* Report the reason fetching a URL failed for the folder backend (Issue #338)

* Add a timeout to HTTP requests Anitya makes to ensure it does not wait
  indefinitely (Issue #377)

* Fix an issue where prefixes could be stripped further than intended (Issue #381)

* Add page titles to the HTML templates (Issue #371)

* Switch from processes to threads in the Anitya cron job to avoid sharing
  network sockets for HTTP requests across processes (Issue #335)
