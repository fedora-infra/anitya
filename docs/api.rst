=================
API Documentation
=================

Anitya provides several APIs for users.

.. _http-api-v2:

HTTP API v2
===========

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

Anitya can be used without its web front-end, if you so choose. Please be aware
that Anitya is still in the early stages of development and its Python APIs are
not stable.

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

Backend API
-----------

.. automodule:: anitya.lib.backends
    :members:
    :undoc-members:
    :show-inheritance:


Plugin API
----------

.. automodule:: anitya.lib.plugins
    :members:
    :undoc-members:
    :show-inheritance:
