import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from ..client import HLS_AES_KEY, SegmentRetrievalException, SiriusXMClient

logger = logging.getLogger(__file__)


def make_sync_http_handler(sxm: SiriusXMClient) -> BaseHTTPRequestHandler:
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
        def do_GET(self):
            if self.path.endswith('.m3u8'):
                data = sxm.get_playlist(self.path.rsplit('/', 1)[1][:-5])
                if data:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/x-mpegURL')
                    self.end_headers()
                    self.wfile.write(bytes(data, 'utf-8'))
                else:
                    self.send_response(503)
                    self.end_headers()
            elif self.path.endswith('.aac'):
                segment_path = self.path[1:]
                try:
                    data = sxm.get_segment(segment_path)
                except SegmentRetrievalException:
                    sxm.reset_session()
                    sxm.authenticate()
                    data = sxm.get_segment(segment_path)

                if data:
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/x-aac')
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.send_response(503)
                    self.end_headers()
            elif self.path.endswith('/key/1'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(HLS_AES_KEY)
            else:
                self.send_response(404)
                self.end_headers()
    return SiriusHandler


def run_sync_http_server(sxm: SiriusXMClient, port: int, ip='0.0.0.0') -> None:
    """
    Creates and runs an instance of :class:`http.server.HTTPServer` to proxy SiriusXM
    requests without authentication.

    You still need a valid SiriusXM account with streaming rights,
    via the :class:`SiriusXMClient`.

    Parameters
    ----------
    port : :class:`int`
        Port number to bind SiriusXM Proxy server on
    ip : :class:`str`
        IP address to bind SiriusXM Proxy server on
    """

    httpd = HTTPServer((ip, port), make_sync_http_handler(sxm))
    try:
        logger.info(f'running SiriusXM proxy server on http://{ip}:{port}')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
