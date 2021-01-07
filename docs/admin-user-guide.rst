================
Admin User Guide
================

This guide is intended for people, who have been granted administrator rights in Anitya.
It will describe the use cases that can be done by the administrator user.

Delete Project
==============

As admin in Anitya you have rights to delete the project, but this should be done
only if you are sure that this project has no value. To delete a project, go on the
project page and click **Delete** button in bottom of the project table.

.. _test-check:

Test Check on Project
=====================

As admin you can do a test check for releases on the project. This is done by clicking
**Test check** button in top of the project table beside latest version. This will do a
check for new releases and shows you the output of the operation in pop-up window. This
operation will not change anything in the database, just shows you what will happen when
next check for this project will be done.

.. _full-check:

Full Check on Project
=====================

As admin you can do a manual check for releases on the project. This is done by clicking
**Full check** button in top of the project table beside latest version. This will do a
check for new releases and saves the result. It's recommended to always do a :ref:`test-check`
before.


Archive Project
===============

As admin you can archive project. The archived project could no longer be edited and is not
checked for a new releases, but will remain read-only in Anitya database. The archivation
could be done by clicking the **Archive** button in bottom of project table on project page.
This option is particularly useful for projects that are no longer alive upstream.


Unarchive Project
=================

As admin you can unarchive archived projects. This could be done by clicking the
**Unarchive** button in bottom of archived project table on project page.


Delete a Version on Project
===========================

As admin you have a power to delete any version on project. This could be useful
if the project was incorrectly setup and retrieved something that is not considered
a release. To delete a version click on the **[x]** beside the desired version in
versions table on project page.


Delete All Versions on Project
==============================

It's sometimes easier to just delete all the versions and do a :ref:`full-check` again.
In this case the admin could delete all versions at once by clicking **Delete versions**
button in bottom of the versions table on project page. Be aware that this could
send plenty of messages, because the message is sent every time a version is deleted.


Delete Mapping on Project
=========================

As admin you can delete a mapping on the project. This could be needed if the project is
renamed in the distribution or no longer provided by the distribution. To delete the
mapping click on the **Delete** button beside the mapping you want to delete in the mappings
table on the project info page.


Delete Distribution
===================

As admin you can delete a distribution in Anitya. This could be useful if there is distribution
containing typo and the correct distribution is already in Anitya. It is always good to check
if the distribution doesn't have any project mapped to it, to check click on the `distros`_
link in header and then click on the distribution you plan to delete. If there is no project
mapped to this distribution it could be safely deleted. Otherwise the project mappings will
be deleted with the distribution.

To delete the distribution click on the `distros`_ link in page header and then click on **Delete**
button on the row which contains distribution you want to delete.


Edit an Existing Distribution
=============================

As admin you can edit a name of existing distribution in Anitya. To edit the distribution name
clink on the `distros`_ link in header and then click on **Edit** button bellow the name of
distribution you want to edit.

.. note::
   The name must be unique, so if you change the name to distribution
   that already exists in Anitya, it will not be allowed.


User management
===============

As admin user you are allowed to do a basic user management. This includes banning a user,
giving admin rights or revoke them. To get to user management page click `users`_ link in
page header. You can find some basic info about the users like *User Id*, *Username*, *E-mail*,
if the user is currently admin and if the user is active or not.

Ban user
--------

Sometimes there is a situation that needs the user to be banned from Anitya. If this is ever
needed you can do it by clicking the **Ban** button in the row with desired user. This user
is then marked as inactive and could no longer login to Anitya. The user needs to have
*Active* set to `True` otherwise this action is not available.

.. note::
    This option should be used as last resort.

Remove ban
----------

To remove ban from a user click on the **Remove ban** button in the row with desired user.
The user will be marked as active and will be able to login to Anitya again.
The user needs to have *Active* set to `False` otherwise this action is not available.


Give admin rights
-----------------

To give admin rights to another user click **Give admin permissions** button in the
row with desired user. The user needs to have *Admin* set to `False` otherwise this action
is not available.

Revoke admin rights
-------------------

To revoke admin rights from another user click **Revoke admin permissions** button in the
row with desired user. The user needs to have *Admin* set to `True` otherwise this action
is not available.

.. note::
    Admin user which is specified in Anitya configuration file can't be striped of admin
    rights this way.

Solving Flags
=============

The flags could be solved on Flags page, which is accessed through `flags`_ link in the page
header.

Basics
------

* try to not remove anything that could be of value
* when removing something, try to create as little impact for others as possible
* check `flags`_ once in a while
* if in doubt, ask in #fedora-apps on freenode IRC

Cases
-----

Below are a number of common flags submitted by users. Please don't view these as rigid laws, but as guidelines to make our handling of cases consistent. Feel free to adapt them, if it seems reasonable.

Project X is a duplicate!
^^^^^^^^^^^^^^^^^^^^^^^^^

1. check if this actually is a duplicate; if not, close the flag
2. check which name matches the name used by the project itself
3. check which one seems more correct/complete (i.e. version source, distro mappings, ...)
4. transfer valuable information/settings from to-be-deleted project to will-stay project, if any
5. delete the project duplicate, close the flag

.. note::
   The flag will be deleted automatically if the flagged project is the one that will
   be deleted.

pypi/gem/... duplicates
^^^^^^^^^^^^^^^^^^^^^^^

Two projects: "nispor" on GitHub, "nispor" on pypi/gem/whatever.

1. check if there is any value added by the pypi/gem/... package (e.g. the versions are different, pypi lags behind, tagging on github are unreliable ...). If there is, do nothing.
2. transfer valuable information/settings from github project to pypi project, if any
3. if there is no added value, delete the pypi one

"Please delete this thing, was just testing"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. check if this seems reasonable
2. delete the thing (project, mapping, version, ...).

Package does not exist in distribution, please delete mapping
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check if it really doesn't exist, then:

a) does exist: do nothing
b) doesn't exist: delete the mapping
c) existed in old, non-EOL version: do nothing
d) existed in old, EOL version: delete

User's flag is wrong, user misunderstood, ...
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just close. If you feel very motivated or it seems important, mail them and try to clear it up.

Upstream dead
^^^^^^^^^^^^^

1. Check if the project is really dead upstream

   Last commit date is usually a good thing to check.

2. Archive the project

   This will lower the amount of projects which are checked for new versions,
   but the project will be still in Anitya, if anybody would want to look at it.

.. _distros: https://release-monitoring.org/distros
.. _users: https://release-monitoring.org/users
.. _flags: https://release-monitoring.org/flags
