=================
API Documentation
=================

Anitya provides several APIs for users.

.. _http-api-v2:

HTTP API v2
===========

The token for API could be obtained from `settings`_ page in
Anitya web interface. This token needs to be provided in
``Authorization`` header of the request. See request examples
bellow.

.. autoflask:: anitya.app:create()
   :undoc-static:
   :modules: anitya.api_v2
   :order: path


HTTP API v1
===========

.. autoflask:: anitya.app:create()
   :undoc-static:
   :modules: anitya.api
   :order: path


Python APIs
===========

Exceptions
----------

.. automodule:: anitya.lib.exceptions
    :members:
    :undoc-members:
    :show-inheritance:

Database API
------------

.. automodule:: anitya.db
    :members:
    :undoc-members:
    :show-inheritance:

anitya.db.meta
^^^^^^^^^^^^^^

.. automodule:: anitya.db.meta
    :members:
    :undoc-members:
    :show-inheritance:

anitya.db.events
^^^^^^^^^^^^^^^^

.. automodule:: anitya.db.events
    :members:
    :undoc-members:
    :show-inheritance:

anitya.db.models
^^^^^^^^^^^^^^^^

.. automodule:: anitya.db.models
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

Backend API
-----------

.. automodule:: anitya.lib.backends
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:


Plugin API
----------

.. automodule:: anitya.lib.plugins
    :members:
    :undoc-members:
    :show-inheritance:

Ecosystem API
-------------

.. automodule:: anitya.lib.ecosystems
    :noindex:
    :members:
    :undoc-members:
    :show-inheritance:

Versions API
------------

.. automodule:: anitya.lib.versions.base
    :members:
    :undoc-members:
    :show-inheritance:

.. _settings: https://release-monitoring.org/settings
