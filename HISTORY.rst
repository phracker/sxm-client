=======
History
=======

0.2.5 (2021-08-16)
------------------

* Pulls `tune_time` from `wallClockRenderTime`
* Adds `primary_hls` and `seconary_hls`
* Adds quality selection
* Overhauls time/datetime management
* Adds automatic failover to secondary HLS

0.2.4 (2021-08-15)
------------------

* Fixes pydantic issue in `XMLiveChannel`
* Adjusts selected HLS stream to (hopefully) fix `radio_time`
* Switches HTTP server to using `aiohttp`
* Adds `SXMClientAsync`

0.2.3 (2021-08-15)
------------------

* Splits typer params out into seperate variables

0.2.2 (2021-08-15)
------------------

* Adds type stubs

0.2.0 (2021-08-15)
------------------

* Fixes authentication (thanks @Lustyn)
* Replaces setuptools with filt
* Replaces click with typer
* Replaces requests with httpx
* Updates linting
* Replaces TravisCI with Github Actions
* Adds Pydantic for SXM models

0.1.0 (2018-12-25)
------------------

* First release on PyPI.
