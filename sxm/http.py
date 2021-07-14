import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Type

from .client import HLS_AES_KEY, SegmentRetrievalException, SXMClient

__all__ = ["make_http_handler", "run_http_server"]


def make_http_handler(
    sxm: SXMClient, logger: logging.Logger, request_level: int = logging.INFO
) -> Type[BaseHTTPRequestHandler]:
    """
    Creates and returns a configured
    :class:`http.server.BaseHTTPRequestHandler` ready to be used
    by a :class:`http.server.HTTPServer` instance with your
    :class:`SXMClient`.

    Really useful if you want to create your own HTTP server as part
    of another application.

    Parameters
    ----------
    sxm : :class:`SXMClient`
        SXM client to use
    """

    class SiriusHandler(BaseHTTPRequestHandler):
        def log_error(self, format, *args):  # noqa: A002
            logger.warn(format % args)

        def log_message(self, format, *args):  # noqa: A002
            logger.log(request_level, format % args)

        def do_GET(self):
            if self.path.endswith(".m3u8"):
                data = sxm.get_playlist(self.path.rsplit("/", 1)[1][:-5])
                if data:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-mpegURL")
                    self.end_headers()
                    self.wfile.write(bytes(data, "utf-8"))
                else:
                    self.send_response(503)
                    self.end_headers()
            elif self.path.endswith(".aac"):
                segment_path = self.path[1:]
                try:
                    data = sxm.get_segment(segment_path)
                except SegmentRetrievalException:
                    sxm.reset_session()
                    sxm.authenticate()
                    data = sxm.get_segment(segment_path)

                if data:
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/x-aac")
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.send_response(503)
                    self.end_headers()
            elif self.path.endswith("/key/1"):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(HLS_AES_KEY)
            elif self.path.endswith("/channels/"):
                try:
                    raw_channels = sxm.get_channels()
                except Exception:
                    raw_channels = []

                if len(raw_channels) > 0:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps(raw_channels).encode("utf-8"))
                else:
                    self.send_response(403)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

    return SiriusHandler


def run_http_server(
    sxm: SXMClient,
    port: int,
    ip="0.0.0.0",  # nosec
    logger: logging.Logger = None,
) -> None:
    """
    Creates and runs an instance of :class:`http.server.HTTPServer` to proxy
    SXM requests without authentication.

    You still need a valid SXM account with streaming rights,
    via the :class:`SXMClient`.

    Parameters
    ----------
    port : :class:`int`
        Port number to bind SXM Proxy server on
    ip : :class:`str`
        IP address to bind SXM Proxy server on
    """

    if logger is None:
        logger = logging.getLogger(__file__)

    httpd = HTTPServer((ip, port), make_http_handler(sxm, logger))
    try:
        logger.info(f"running SXM proxy server on http://{ip}:{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
