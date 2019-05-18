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

SXMClient
=========

.. autoclass:: SXMClient
    :members:

HTTP Server
===========

.. autofunction:: make_http_handler

.. autofunction:: run_http_server
