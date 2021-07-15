import logging
from .client import SXMClient as SXMClient
from http.server import BaseHTTPRequestHandler
from typing import Type

def make_http_handler(sxm: SXMClient, logger: logging.Logger, request_level: int = ...) -> Type[BaseHTTPRequestHandler]: ...
def run_http_server(sxm: SXMClient, port: int, ip: str = ..., logger: logging.Logger = ...) -> None: ...
