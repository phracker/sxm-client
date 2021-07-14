# -*- coding: utf-8 -*-

"""Top-level package for sxm."""

from sxm.http import make_http_handler, run_http_server
from sxm.client import (
    HLS_AES_KEY,
    SXMClient,
    AuthenticationError,
    SegmentRetrievalException,
)

__author__ = """AngellusMortis"""
__email__ = "cbailey@mort.is"
__version__ = "0.2.0"
__all__ = [
    "AuthenticationError",
    "HLS_AES_KEY",
    "make_http_handler",
    "run_http_server",
    "SegmentRetrievalException",
    "SXMClient",
]
