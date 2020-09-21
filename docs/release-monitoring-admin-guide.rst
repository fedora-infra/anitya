=================================
release-monitoring.org guidelines
=================================

This guide is intended for people, who have been granted administrator rights on release-monitoring.org.

Basics
======

* try to not remove anything that could be of value
* when removing something, try to create as little impact for others as possible
* check https://release-monitoring.org/flags once in a while
* if in doubt, ask in #fedora-apps on freenode IRC

Cases
=====

Below are a number of common flags submitted by users. Please don't view these as rigid laws, but as guidelines to make our handling of cases consistent. Feel free to adapt them, if it seems reasonable.

Project X is a duplicate!
-------------------------

1. check, if this actually is a duplicate; if not, close the flag
2. check which name matches the name used by the project itself
3. check which one seems more correct/complete (i.e. version source, distro mappings, ...)
4. transfer valuable information/settings from to-be-deleted project to will-stay project, if any
5. delete the project duplicated, close the flag

pypi/gem/... duplicates
~~~~~~~~~~~~~~~~~~~~~~~

Two projects: "nispor" on GitHub, "nispor" on pypi/gem/whatever.

1. check if there is any value added by the pypi/gem/... package (e.g. the versions are different, pypi lags behind, tagging on github are unreliable ...). If there is, do nothing.
2. transfer valuable information/settings from github project to pypi project, if any
3. if there is no added value, delete the pypi one

"Please delete this thing, was just testing"
--------------------------------------------

1. check if this seems reasonable
2. delete the thing (project, mapping, version, ...).

Package does not exist in distribution, please delete mapping
-------------------------------------------------------------

check, if it really doesn't exist, then:

a) does exist: do nothing
b) doesn't exist: delete the mapping
c) existed in old, non-EOL version: do nothing
d) existed in old, EOL version: delete

User's flag is wrong, user misunderstood, ...
---------------------------------------------

Just close. If you feel very motivated or it seems important, mail them and try to clear it up.
