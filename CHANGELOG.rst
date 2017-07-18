Changes
=======

dev (master)
------------

Backwards-incompatible API changes
----------------------------------

A number of functions that make up Anitya's Python API have been moved
(`#503 <https://github.com/release-monitoring/anitya/pull/503>`_). The full
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


Features
--------


Bug fixes
---------


0.11.0 (Feb. 08, 2017)
----------------------

* Return 4XX codes in error cases for /projects/new rather than 200 (Issue #246)

* Allow projecst using the "folder" backend to make insecure HTTPS requests
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


0.10.1 (Nov. 29, 2016)
----------------------

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
