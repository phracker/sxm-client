# -*- coding: utf-8 -*-

"""Top-level package for sxm."""

from sxm.client import (
    HLS_AES_KEY,
    AuthenticationError,
    SegmentRetrievalException,
    SXMClient,
)
from sxm.http import make_http_handler, run_http_server

__author__ = """AngellusMortis"""
__email__ = "cbailey@mort.is"
__version__ = "0.2.3"
__all__ = [
    "AuthenticationError",
    "HLS_AES_KEY",
    "make_http_handler",
    "run_http_server",
    "SegmentRetrievalException",
    "SXMClient",
]
