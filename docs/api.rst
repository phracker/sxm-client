.. currentmodule:: sxm

=============
API Reference
=============

.. toctree::
   :maxdepth: 2
   :caption: API:

   models/api

Exceptions
==========

.. autoexception:: AuthenticationError

.. autoexception:: SegmentRetrievalException

SiriusXMClient
==============

.. autoclass:: SiriusXMClient
    :members:

HTTP Server
===========

.. autofunction:: make_sync_http_handler

.. autofunction:: run_sync_http_server

Async HTTP Server
=================

.. autofunction:: make_async_http_app

.. autofunction:: run_async_http_server
