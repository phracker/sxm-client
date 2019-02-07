import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Type

from .client import HLS_AES_KEY, SegmentRetrievalException, SiriusXMClient

__all__ = ["make_http_handler", "run_http_server"]


def make_http_handler(
    sxm: SiriusXMClient,
    logger: logging.Logger,
    request_level: int = logging.INFO,
) -> Type[BaseHTTPRequestHandler]:
    """
    Creates and returns a configured
    :class:`http.server.BaseHTTPRequestHandler` ready to be used
    by a :class:`http.server.HTTPServer` instance with your
    :class:`SiriusXMClient`.

    Really useful if you want to create your own HTTP server as part
    of another application.

    Parameters
    ----------
    sxm : :class:`SiriusXMClient`
        SiriusXM client to use
    """

    class SiriusHandler(BaseHTTPRequestHandler):
        def log_error(self, format, *args):
            logger.warn(format % args)

        def log_message(self, format, *args):
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
            else:
                self.send_response(404)
                self.end_headers()

    return SiriusHandler


def run_http_server(
    sxm: SiriusXMClient, port: int, ip="0.0.0.0", logger: logging.Logger = None
) -> None:
    """
    Creates and runs an instance of :class:`http.server.HTTPServer` to proxy
    SiriusXM requests without authentication.

    You still need a valid SiriusXM account with streaming rights,
    via the :class:`SiriusXMClient`.

    Parameters
    ----------
    port : :class:`int`
        Port number to bind SiriusXM Proxy server on
    ip : :class:`str`
        IP address to bind SiriusXM Proxy server on
    """

    if logger is None:
        logger = logging.getLogger(__file__)

    httpd = HTTPServer((ip, port), make_http_handler(sxm, logger))
    try:
        logger.info(f"running SiriusXM proxy server on http://{ip}:{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
