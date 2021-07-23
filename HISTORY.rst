=======
History
=======

0.2.7 (2021-07-23)
------------------

* Adds caching of HLS chunks to HLS proxy to make it more resilient to network issues
* HLS chunk caching can be disabled with `-n` or `--no-precache`
* Speeds up `XMLiveChannel.get_latest_cut`

0.2.6 (2021-07-17)
------------------

* Fixes secondary HLS URL generation

0.2.5 (2021-07-16)
------------------

* Pulls `tune_time` from `wallClockRenderTime`
* Adds `primary_hls` and `seconary_hls`
* Adds quality selection
* Overhauls time/datetime management
* Adds automatic failover to secondary HLS

0.2.4 (2021-07-15)
------------------

* Fixes pydantic issue in `XMLiveChannel`
* Adjusts selected HLS stream to (hopefully) fix `radio_time`
* Switches HTTP server to using `aiohttp`
* Adds `SXMClientAsync`

0.2.3 (2021-07-15)
------------------

* Splits typer params out into seperate variables

0.2.2 (2021-07-15)
------------------

* Adds type stubs

0.2.0 (2021-07-15)
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
